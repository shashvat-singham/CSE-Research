"""The MNIST0 network, original and repaired.

Python port of ``MNIST0_DNNt_Original.java`` and ``MNIST0_DNNt_Combined.java``.

Architecture (28x28x1 input)::

    0  conv2d_1     3x3, 1 -> 2     26x26x2
    1  activation_1 relu
    2  conv2d_2     3x3, 2 -> 4     24x24x4
    3  activation_2 relu
    4  max_pooling  2x2             12x12x4
    5  flatten                      576
    6  dense_1      576 -> 128      128
    7  activation_3 relu
    8  dense_2      128 -> 10       10
    9  activation_4 identity, argmax

Repairs target layer 6 (intermediate) or layer 8 (last). Because every layer
before the repaired one is unaffected by the weight deltas, the trunk is
evaluated once and shared; only the tail is evaluated per expert. The Java
version recomputed the whole network for each of the twelve slots, which is
where its runtime went.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from ..combination import AVERAGE_REPAIR_SLOT, FULL_REPAIR_SLOT, ORIGINAL_SLOT
from .internal_data import MNIST0InternalData
from .layers import conv2d_valid, dense, dense_batched, flatten, maxpool2d, relu

__all__ = ["MNIST0Network", "NUMBER_OF_EXPERTS", "REPAIRABLE_LAYERS"]

NUMBER_OF_EXPERTS = 10
REPAIRABLE_LAYERS = (6, 8)


class MNIST0Network:
    """Runs the MNIST0 classifier, optionally with per-expert weight deltas.

    Args:
        internal: Loaded weights and biases.
        weight_deltas: Repair deltas of shape ``(slots, fan_in, fan_out)`` as
            produced by :func:`~nnrepair.z3_solutions.load_repaired_weights_mnist0`.
            ``None`` runs the original network only.
    """

    def __init__(
        self,
        internal: MNIST0InternalData,
        weight_deltas: np.ndarray | None = None,
    ) -> None:
        self.internal = internal
        self.weight_deltas = weight_deltas

    # -- trunk ---------------------------------------------------------------

    def _trunk_to_flatten(self, input_image: np.ndarray) -> np.ndarray:
        """Layers 0-5: everything up to the first dense layer.

        Args:
            input_image: ``(28, 28, 1)``.

        Returns:
            ``(576,)`` flattened activations.
        """
        internal = self.internal
        layer0 = conv2d_valid(input_image, internal.weights0, internal.biases0)
        layer1 = relu(layer0)
        layer2 = conv2d_valid(layer1, internal.weights2, internal.biases2)
        layer3 = relu(layer2)
        layer4 = maxpool2d(layer3, size=2)
        return flatten(layer4)

    # -- original ------------------------------------------------------------

    def logits_original(self, input_image: np.ndarray) -> np.ndarray:
        """Return the unrepaired network's 10 output scores."""
        internal = self.internal
        layer5 = self._trunk_to_flatten(input_image)
        layer6 = dense(layer5, internal.weights6, internal.biases6)
        layer7 = relu(layer6)
        return dense(layer7, internal.weights8, internal.biases8)

    def run_original(self, input_image: np.ndarray) -> int:
        """Return the unrepaired network's predicted label."""
        return int(np.argmax(self.logits_original(input_image)))

    # -- repaired ------------------------------------------------------------

    def run(
        self,
        input_image: np.ndarray,
        repaired_layer_id: int,
        expert_ids: Sequence[int],
        optimized: bool = False,
    ) -> dict[int, np.ndarray]:
        """Evaluate the original network and every repaired variant.

        Args:
            input_image: ``(28, 28, 1)``.
            repaired_layer_id: ``6`` or ``8``.
            expert_ids: Experts to evaluate.
            optimized: Skip the FULL and AVERAGE slots.

        Returns:
            Slot to 10 output scores. Always contains ``ORIGINAL_SLOT`` (-1)
            and one entry per expert; contains ``FULL_REPAIR_SLOT`` and
            ``AVERAGE_REPAIR_SLOT`` unless ``optimized``.

        Raises:
            ValueError: If ``repaired_layer_id`` is not repairable, or no
                deltas were supplied.
        """
        if repaired_layer_id not in REPAIRABLE_LAYERS:
            raise ValueError(
                f"Layer {repaired_layer_id} is not repairable for MNIST0; "
                f"expected one of {REPAIRABLE_LAYERS}"
            )
        if self.weight_deltas is None:
            raise ValueError("No weight deltas supplied; use run_original() instead.")

        internal = self.internal
        slots = list(expert_ids)
        if not optimized:
            slots += [FULL_REPAIR_SLOT, AVERAGE_REPAIR_SLOT]

        layer5 = self._trunk_to_flatten(input_image)

        # Original path, kept alongside so callers can compare against it.
        layer6_orig = dense(layer5, internal.weights6, internal.biases6)
        layer7_orig = relu(layer6_orig)
        layer8_orig = dense(layer7_orig, internal.weights8, internal.biases8)

        results: dict[int, np.ndarray] = {ORIGINAL_SLOT: layer8_orig}
        if not slots:
            return results

        deltas = self.weight_deltas[slots]  # (S, fan_in, fan_out)

        if repaired_layer_id == 6:
            repaired_w6 = internal.weights6[None, :, :] + deltas
            layer6 = dense_batched(layer5, repaired_w6, internal.biases6)
            layer7 = relu(layer6)
            # Layer 8 is unrepaired, so all variants share its weights.
            layer8 = layer7 @ internal.weights8 + internal.biases8
        else:  # repaired_layer_id == 8
            repaired_w8 = internal.weights8[None, :, :] + deltas
            layer8 = dense_batched(layer7_orig, repaired_w8, internal.biases8)

        results.update({slot: layer8[i] for i, slot in enumerate(slots)})
        return results
