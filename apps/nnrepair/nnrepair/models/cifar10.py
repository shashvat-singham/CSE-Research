"""The CIFAR10 network, original and repaired.

Python port of ``CIFAR10_DNNt_Original.java`` and ``CIFAR10_DNNt_Combined.java``.

Architecture (32x32x3 input)::

     0  conv2d_1     3x3, 3 -> 32    30x30x32
     1  activation_1 relu
     2  conv2d_2     3x3, 32 -> 32   28x28x32
     3  activation_2 relu
     4  max_pooling  2x2             14x14x32
     5  conv2d_3     3x3, 32 -> 64   12x12x64
     6  activation_3 relu
     7  conv2d_4     3x3, 64 -> 64   10x10x64
     8  activation_4 relu
     9  max_pooling  2x2             5x5x64
    10  flatten                      1600
    11  dense_1      1600 -> 512     512
    12  activation_5 relu
    13  dense_2      512 -> 10       10
    14  activation_6 identity, argmax

Only layer 13 carries a repair in the shipped artifacts.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from ..combination import AVERAGE_REPAIR_SLOT, FULL_REPAIR_SLOT, ORIGINAL_SLOT
from .internal_data import CIFAR10InternalData
from .layers import conv2d_valid, dense, dense_batched, flatten, maxpool2d, relu

__all__ = ["CIFAR10Network", "NUMBER_OF_EXPERTS", "REPAIRABLE_LAYERS"]

NUMBER_OF_EXPERTS = 10
REPAIRABLE_LAYERS = (13,)


class CIFAR10Network:
    """Runs the CIFAR10 classifier, optionally with per-expert weight deltas.

    Args:
        internal: Loaded weights and biases.
        weight_deltas: Repair deltas of shape ``(slots, 512, 10)`` as produced
            by :func:`~nnrepair.z3_solutions.load_repaired_weights_cifar10`.
    """

    def __init__(
        self,
        internal: CIFAR10InternalData,
        weight_deltas: np.ndarray | None = None,
    ) -> None:
        self.internal = internal
        self.weight_deltas = weight_deltas

    # -- trunk ---------------------------------------------------------------

    def _trunk_to_relu12(self, input_image: np.ndarray) -> np.ndarray:
        """Layers 0-12: everything up to the repaired final dense layer.

        Args:
            input_image: ``(32, 32, 3)``.

        Returns:
            ``(512,)`` post-ReLU activations.
        """
        internal = self.internal
        x = conv2d_valid(input_image, internal.weights0, internal.biases0)
        x = relu(x)
        x = conv2d_valid(x, internal.weights2, internal.biases2)
        x = relu(x)
        x = maxpool2d(x, size=2)
        x = conv2d_valid(x, internal.weights5, internal.biases5)
        x = relu(x)
        x = conv2d_valid(x, internal.weights7, internal.biases7)
        x = relu(x)
        x = maxpool2d(x, size=2)
        layer10 = flatten(x)
        layer11 = dense(layer10, internal.weights11, internal.biases11)
        return relu(layer11)

    # -- original ------------------------------------------------------------

    def logits_original(self, input_image: np.ndarray) -> np.ndarray:
        """Return the unrepaired network's 10 output scores."""
        layer12 = self._trunk_to_relu12(input_image)
        return dense(layer12, self.internal.weights13, self.internal.biases13)

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
            input_image: ``(32, 32, 3)``.
            repaired_layer_id: ``13``.
            expert_ids: Experts to evaluate.
            optimized: Skip the FULL and AVERAGE slots.

        Returns:
            Slot to 10 output scores, including ``ORIGINAL_SLOT`` (-1).

        Raises:
            ValueError: If ``repaired_layer_id`` is not repairable, or no
                deltas were supplied.
        """
        if repaired_layer_id not in REPAIRABLE_LAYERS:
            raise ValueError(
                f"Layer {repaired_layer_id} is not repairable for CIFAR10; "
                f"expected one of {REPAIRABLE_LAYERS}"
            )
        if self.weight_deltas is None:
            raise ValueError("No weight deltas supplied; use run_original() instead.")

        internal = self.internal
        slots = list(expert_ids)
        if not optimized:
            slots += [FULL_REPAIR_SLOT, AVERAGE_REPAIR_SLOT]

        layer12 = self._trunk_to_relu12(input_image)
        layer13_orig = dense(layer12, internal.weights13, internal.biases13)

        results: dict[int, np.ndarray] = {ORIGINAL_SLOT: layer13_orig}
        if not slots:
            return results

        repaired_w13 = internal.weights13[None, :, :] + self.weight_deltas[slots]
        layer13 = dense_batched(layer12, repaired_w13, internal.biases13)

        results.update({slot: layer13[i] for i, slot in enumerate(slots)})
        return results
