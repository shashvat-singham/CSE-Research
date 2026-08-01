"""Verify the vectorised layers against literal transcriptions of the Java loops.

The reference implementations below are deliberately written the way
``MNIST0_DNNt_Original.java`` writes them — nested scalar loops — so that a
disagreement points at the NumPy rewrite rather than at a shared
misunderstanding of the architecture.
"""

from __future__ import annotations

import numpy as np
import pytest

from nnrepair.models.layers import conv2d_valid, dense, dense_batched, flatten, maxpool2d, relu


def java_conv2d(inputs, weights, biases):
    """Literal transcription of the Java convolution loop."""
    kh, kw, cin, cout = weights.shape
    out_h = inputs.shape[0] - kh + 1
    out_w = inputs.shape[1] - kw + 1
    out = np.zeros((out_h, out_w, cout))
    for i in range(out_h):
        for j in range(out_w):
            for k in range(cout):
                out[i][j][k] = biases[k]
                for I in range(kh):
                    for J in range(kw):
                        for K in range(cin):
                            out[i][j][k] += weights[I][J][K][k] * inputs[i + I][j + J][K]
    return out


def java_maxpool(inputs, size=2):
    """Literal transcription of the Java pooling loop, zero-seeded as it is."""
    h, w, c = inputs.shape
    out = np.zeros((h // size, w // size, c))
    for i in range(h // size):
        for j in range(w // size):
            for k in range(c):
                out[i][j][k] = 0
                for I in range(i * size, (i + 1) * size):
                    for J in range(j * size, (j + 1) * size):
                        if inputs[I][J][k] > out[i][j][k]:
                            out[i][j][k] = inputs[I][J][k]
    return out


def java_flatten_mnist(layer4):
    """The Java index arithmetic for MNIST's 12x12x4 -> 576 flatten."""
    out = np.zeros(576)
    for i in range(576):
        d0 = i // 48
        d1 = (i % 48) // 4
        d2 = i - d0 * 48 - d1 * 4
        out[i] = layer4[d0][d1][d2]
    return out


def java_flatten_cifar(layer9):
    """The Java index arithmetic for CIFAR's 5x5x64 -> 1600 flatten."""
    out = np.zeros(1600)
    for i in range(1600):
        d0 = i // 320
        d1 = (i % 320) // 64
        d2 = i - d0 * 320 - d1 * 64
        out[i] = layer9[d0][d1][d2]
    return out


@pytest.fixture
def rng():
    return np.random.default_rng(20240801)


def test_conv2d_matches_java_mnist_layer0(rng):
    inputs = rng.normal(size=(28, 28, 1))
    weights = rng.normal(size=(3, 3, 1, 2))
    biases = rng.normal(size=2)
    np.testing.assert_allclose(
        conv2d_valid(inputs, weights, biases), java_conv2d(inputs, weights, biases), rtol=0, atol=1e-12
    )


def test_conv2d_matches_java_multichannel(rng):
    """Layer 2 has 2 input channels, the case a channel-axis slip would break."""
    inputs = rng.normal(size=(26, 26, 2))
    weights = rng.normal(size=(3, 3, 2, 4))
    biases = rng.normal(size=4)
    np.testing.assert_allclose(
        conv2d_valid(inputs, weights, biases), java_conv2d(inputs, weights, biases), rtol=0, atol=1e-11
    )


def test_conv2d_is_correlation_not_convolution():
    """A flipped kernel would still pass a symmetric test; this one is asymmetric."""
    inputs = np.arange(9, dtype=np.float64).reshape(3, 3, 1)
    weights = np.zeros((2, 2, 1, 1))
    weights[0, 0, 0, 0] = 1.0  # top-left tap only
    out = conv2d_valid(inputs, weights, np.zeros(1))
    # Correlation picks input[i][j]; convolution would pick input[i+1][j+1].
    np.testing.assert_allclose(out[:, :, 0], [[0.0, 1.0], [3.0, 4.0]])


def test_maxpool_matches_java(rng):
    inputs = relu(rng.normal(size=(24, 24, 4)))
    np.testing.assert_allclose(maxpool2d(inputs, 2), java_maxpool(inputs, 2))


def test_maxpool_rejects_indivisible_shape():
    with pytest.raises(ValueError, match="not divisible"):
        maxpool2d(np.zeros((5, 4, 1)), 2)


def test_flatten_matches_java_mnist_indexing(rng):
    layer4 = rng.normal(size=(12, 12, 4))
    np.testing.assert_array_equal(flatten(layer4), java_flatten_mnist(layer4))


def test_flatten_matches_java_cifar_indexing(rng):
    layer9 = rng.normal(size=(5, 5, 64))
    np.testing.assert_array_equal(flatten(layer9), java_flatten_cifar(layer9))


def test_dense_matches_java_loop(rng):
    inputs = rng.normal(size=576)
    weights = rng.normal(size=(576, 128))
    biases = rng.normal(size=128)
    expected = np.array(
        [biases[i] + sum(weights[I][i] * inputs[I] for I in range(576)) for i in range(128)]
    )
    np.testing.assert_allclose(dense(inputs, weights, biases), expected, rtol=1e-12)


def test_dense_batched_matches_per_variant_dense(rng):
    """The batched path must equal looping one expert at a time."""
    inputs = rng.normal(size=128)
    weights = rng.normal(size=(12, 128, 10))
    biases = rng.normal(size=10)
    batched = dense_batched(inputs, weights, biases)
    for slot in range(12):
        np.testing.assert_allclose(batched[slot], dense(inputs, weights[slot], biases), rtol=1e-12)


def test_dense_batched_accepts_diverged_inputs(rng):
    """Intermediate-layer repair diverges before the final dense layer."""
    inputs = rng.normal(size=(12, 576))
    weights = np.broadcast_to(rng.normal(size=(576, 128)), (12, 576, 128))
    biases = rng.normal(size=128)
    batched = dense_batched(inputs, weights, biases)
    for slot in range(12):
        np.testing.assert_allclose(batched[slot], dense(inputs[slot], weights[slot], biases), rtol=1e-12)


def test_relu():
    np.testing.assert_array_equal(relu(np.array([-1.0, 0.0, 2.5])), [0.0, 0.0, 2.5])
