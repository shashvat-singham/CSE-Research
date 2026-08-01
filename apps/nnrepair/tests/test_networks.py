"""Verify whole-network inference against literal transcriptions of the Java.

:mod:`test_layers` checks each layer in isolation. This module checks the
assembled networks, including the batched per-expert path that has no
counterpart in the Java (which recomputed every slot from scratch).

Where the extracted weights are available locally, the check runs on real
weights and real inputs; otherwise it falls back to random tensors of the
correct shape, which still exercises every index mapping.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from nnrepair.combination import AVERAGE_REPAIR_SLOT, FULL_REPAIR_SLOT, ORIGINAL_SLOT
from nnrepair.models.cifar10 import CIFAR10InternalData, CIFAR10Network
from nnrepair.models.internal_data import MNIST0InternalData
from nnrepair.models.mnist0 import MNIST0Network

ARTIFACT_ROOT = Path(__file__).resolve().parents[3] / "NNRepair"
MNIST_ADV = ARTIFACT_ROOT / "NN-Code" / "mnist0-adv"


def java_mnist0_run(inp, internal):
    """Literal transcription of ``MNIST0_DNNt_Original.run()``."""
    w0, w2, w6, w8 = internal.weights0, internal.weights2, internal.weights6, internal.weights8
    b0, b2, b6, b8 = internal.biases0, internal.biases2, internal.biases6, internal.biases8

    layer0 = np.zeros((26, 26, 2))
    for i in range(26):
        for j in range(26):
            for k in range(2):
                layer0[i][j][k] = b0[k]
                for I in range(3):
                    for J in range(3):
                        for K in range(1):
                            layer0[i][j][k] += w0[I][J][K][k] * inp[i + I][j + J][K]
    layer1 = np.where(layer0 > 0, layer0, 0.0)

    layer2 = np.zeros((24, 24, 4))
    for i in range(24):
        for j in range(24):
            for k in range(4):
                layer2[i][j][k] = b2[k]
                for I in range(3):
                    for J in range(3):
                        for K in range(2):
                            layer2[i][j][k] += w2[I][J][K][k] * layer1[i + I][j + J][K]
    layer3 = np.where(layer2 > 0, layer2, 0.0)

    layer4 = np.zeros((12, 12, 4))
    for i in range(12):
        for j in range(12):
            for k in range(4):
                for I in range(i * 2, (i + 1) * 2):
                    for J in range(j * 2, (j + 1) * 2):
                        if layer3[I][J][k] > layer4[i][j][k]:
                            layer4[i][j][k] = layer3[I][J][k]

    layer5 = np.zeros(576)
    for i in range(576):
        d0 = i // 48
        d1 = (i % 48) // 4
        d2 = i - d0 * 48 - d1 * 4
        layer5[i] = layer4[d0][d1][d2]

    layer6 = np.zeros(128)
    for i in range(128):
        layer6[i] = b6[i]
        for I in range(576):
            layer6[i] += w6[I][i] * layer5[I]
    layer7 = np.where(layer6 > 0, layer6, 0.0)

    layer8 = np.zeros(10)
    for i in range(10):
        layer8[i] = b8[i]
        for I in range(128):
            layer8[i] += w8[I][i] * layer7[I]
    return layer8


def random_mnist0_data(rng):
    return MNIST0InternalData(
        weights0=rng.normal(scale=0.3, size=(3, 3, 1, 2)),
        weights2=rng.normal(scale=0.3, size=(3, 3, 2, 4)),
        weights6=rng.normal(scale=0.1, size=(576, 128)),
        weights8=rng.normal(scale=0.1, size=(128, 10)),
        biases0=rng.normal(scale=0.1, size=2),
        biases2=rng.normal(scale=0.1, size=4),
        biases6=rng.normal(scale=0.1, size=128),
        biases8=rng.normal(scale=0.1, size=10),
    )


def random_cifar10_data(rng):
    return CIFAR10InternalData(
        weights0=rng.normal(scale=0.1, size=(3, 3, 3, 32)),
        weights2=rng.normal(scale=0.05, size=(3, 3, 32, 32)),
        weights5=rng.normal(scale=0.05, size=(3, 3, 32, 64)),
        weights7=rng.normal(scale=0.05, size=(3, 3, 64, 64)),
        weights11=rng.normal(scale=0.02, size=(1600, 512)),
        weights13=rng.normal(scale=0.05, size=(512, 10)),
        biases0=rng.normal(scale=0.05, size=32),
        biases2=rng.normal(scale=0.05, size=32),
        biases5=rng.normal(scale=0.05, size=64),
        biases7=rng.normal(scale=0.05, size=64),
        biases11=rng.normal(scale=0.05, size=512),
        biases13=rng.normal(scale=0.05, size=10),
    )


@pytest.fixture
def rng():
    return np.random.default_rng(4242)


class TestMNIST0:
    def test_matches_java_transcription_on_random_weights(self, rng):
        internal = random_mnist0_data(rng)
        image = rng.uniform(size=(28, 28, 1))
        np.testing.assert_allclose(
            MNIST0Network(internal).logits_original(image),
            java_mnist0_run(image, internal),
            rtol=0,
            atol=1e-10,
        )

    @pytest.mark.skipif(not (MNIST_ADV / "params").is_dir(), reason="weight dumps not present")
    def test_matches_java_transcription_on_real_weights(self):
        internal = MNIST0InternalData.from_directory(MNIST_ADV / "params")
        rng = np.random.default_rng(7)
        image = rng.uniform(size=(28, 28, 1))
        np.testing.assert_allclose(
            MNIST0Network(internal).logits_original(image),
            java_mnist0_run(image, internal),
            rtol=0,
            atol=1e-10,
        )

    def test_zero_deltas_reproduce_the_original(self, rng):
        """Every repaired slot must collapse onto ORIG when deltas vanish."""
        internal = random_mnist0_data(rng)
        image = rng.uniform(size=(28, 28, 1))
        deltas = np.zeros((12, 128, 10))
        result = MNIST0Network(internal, deltas).run(image, 8, range(10))
        for slot, logits in result.items():
            np.testing.assert_allclose(
                logits, result[ORIGINAL_SLOT], rtol=1e-12, err_msg=f"slot {slot}"
            )

    def test_last_layer_repair_shifts_only_the_repaired_layer(self, rng):
        internal = random_mnist0_data(rng)
        image = rng.uniform(size=(28, 28, 1))
        deltas = np.zeros((12, 128, 10))
        deltas[3] = 5.0  # expert 3 only
        result = MNIST0Network(internal, deltas).run(image, 8, range(10))
        assert not np.allclose(result[3], result[ORIGINAL_SLOT])
        np.testing.assert_allclose(result[5], result[ORIGINAL_SLOT], rtol=1e-12)

    def test_intermediate_repair_propagates_through_relu(self, rng):
        internal = random_mnist0_data(rng)
        image = rng.uniform(size=(28, 28, 1))
        deltas = np.zeros((12, 576, 128))
        deltas[2] = 0.01
        result = MNIST0Network(internal, deltas).run(image, 6, range(10))
        assert not np.allclose(result[2], result[ORIGINAL_SLOT])
        np.testing.assert_allclose(result[4], result[ORIGINAL_SLOT], rtol=1e-12)

    def test_batched_path_equals_one_expert_at_a_time(self, rng):
        """The batched matmul is the port's main departure from the Java."""
        internal = random_mnist0_data(rng)
        image = rng.uniform(size=(28, 28, 1))
        deltas = rng.normal(scale=0.1, size=(12, 128, 10))
        network = MNIST0Network(internal, deltas)
        batched = network.run(image, 8, range(10))
        for expert_id in range(10):
            single = network.run(image, 8, [expert_id], optimized=True)
            np.testing.assert_allclose(batched[expert_id], single[expert_id], rtol=1e-12)

    def test_optimized_omits_full_and_average_slots(self, rng):
        internal = random_mnist0_data(rng)
        network = MNIST0Network(internal, np.zeros((12, 128, 10)))
        result = network.run(rng.uniform(size=(28, 28, 1)), 8, range(10), optimized=True)
        assert FULL_REPAIR_SLOT not in result
        assert AVERAGE_REPAIR_SLOT not in result

    def test_unrepairable_layer_is_rejected(self, rng):
        network = MNIST0Network(random_mnist0_data(rng), np.zeros((12, 128, 10)))
        with pytest.raises(ValueError, match="not repairable"):
            network.run(rng.uniform(size=(28, 28, 1)), 7, range(10))

    def test_run_without_deltas_is_rejected(self, rng):
        network = MNIST0Network(random_mnist0_data(rng))
        with pytest.raises(ValueError, match="No weight deltas"):
            network.run(rng.uniform(size=(28, 28, 1)), 8, range(10))


class TestCIFAR10:
    def test_shapes_flow_through_to_ten_logits(self, rng):
        internal = random_cifar10_data(rng)
        image = rng.uniform(size=(32, 32, 3))
        assert CIFAR10Network(internal).logits_original(image).shape == (10,)

    def test_zero_deltas_reproduce_the_original(self, rng):
        internal = random_cifar10_data(rng)
        image = rng.uniform(size=(32, 32, 3))
        result = CIFAR10Network(internal, np.zeros((12, 512, 10))).run(image, 13, range(10))
        for slot, logits in result.items():
            np.testing.assert_allclose(
                logits, result[ORIGINAL_SLOT], rtol=1e-12, err_msg=f"slot {slot}"
            )

    def test_batched_path_equals_one_expert_at_a_time(self, rng):
        internal = random_cifar10_data(rng)
        image = rng.uniform(size=(32, 32, 3))
        deltas = rng.normal(scale=0.1, size=(12, 512, 10))
        network = CIFAR10Network(internal, deltas)
        batched = network.run(image, 13, range(10))
        for expert_id in range(10):
            single = network.run(image, 13, [expert_id], optimized=True)
            np.testing.assert_allclose(batched[expert_id], single[expert_id], rtol=1e-12)

    def test_only_layer_13_is_repairable(self, rng):
        network = CIFAR10Network(random_cifar10_data(rng), np.zeros((12, 512, 10)))
        with pytest.raises(ValueError, match="not repairable"):
            network.run(rng.uniform(size=(32, 32, 3)), 11, range(10))
