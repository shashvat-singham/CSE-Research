"""Vectorised equivalents of the hand-unrolled Java layer loops.

The Java ``*_DNNt_*`` classes spell every layer out as four to six nested
``for`` loops over scalar ``double``s. Those loops are exactly convolution,
ReLU, max-pooling, flatten and dense — expressed here as NumPy so a full test
set runs in seconds rather than hours.

Two conventions from the Java carry over and matter for bit-comparability:

* Convolution is **cross-correlation** with no kernel flip and ``valid``
  padding, matching Keras' ``Conv2D`` (which is what the weights came from).
* Tensors stay in ``(height, width, channel)`` order, so ``flatten`` is a
  plain C-order ``reshape``. The Java index arithmetic
  ``d0 = i/48, d1 = (i%48)/4, d2 = i - d0*48 - d1*4`` is precisely C-order
  over a ``(12, 12, 4)`` array.
"""

from __future__ import annotations

import numpy as np

__all__ = ["conv2d_valid", "relu", "maxpool2d", "flatten", "dense", "dense_batched"]


def conv2d_valid(inputs: np.ndarray, weights: np.ndarray, biases: np.ndarray) -> np.ndarray:
    """2-D cross-correlation with ``valid`` padding and unit stride.

    Args:
        inputs: ``(H, W, C_in)``.
        weights: ``(KH, KW, C_in, C_out)``.
        biases: ``(C_out,)``.

    Returns:
        ``(H - KH + 1, W - KW + 1, C_out)``.
    """
    kernel_h, kernel_w, _, out_channels = weights.shape
    out_h = inputs.shape[0] - kernel_h + 1
    out_w = inputs.shape[1] - kernel_w + 1

    # Sliding window view avoids materialising an im2col copy of the input.
    windows = np.lib.stride_tricks.sliding_window_view(
        inputs, (kernel_h, kernel_w), axis=(0, 1)
    )  # (out_h, out_w, C_in, KH, KW)

    # 'ijckl,klco->ijo': sum over kernel positions (k, l) and input channels (c).
    out = np.einsum("ijckl,klco->ijo", windows, weights, optimize=True)
    return out + biases.reshape(1, 1, out_channels)


def relu(inputs: np.ndarray) -> np.ndarray:
    """Element-wise ``max(0, x)``."""
    return np.maximum(inputs, 0.0)


def maxpool2d(inputs: np.ndarray, size: int = 2) -> np.ndarray:
    """Non-overlapping max pooling over the spatial dimensions.

    The Java seeds each pooling window at ``0`` rather than ``-inf``, so an
    all-negative window yields ``0``. Every pooling layer in both networks is
    fed by a ReLU, so inputs are non-negative and the two agree; this
    implementation keeps the true maximum.

    Args:
        inputs: ``(H, W, C)`` with ``H`` and ``W`` divisible by ``size``.
        size: Window edge length.

    Returns:
        ``(H // size, W // size, C)``.
    """
    height, width, channels = inputs.shape
    if height % size or width % size:
        raise ValueError(f"maxpool2d: {height}x{width} is not divisible by {size}")
    reshaped = inputs.reshape(height // size, size, width // size, size, channels)
    return reshaped.max(axis=(1, 3))


def flatten(inputs: np.ndarray) -> np.ndarray:
    """Flatten to 1-D in C order."""
    return inputs.reshape(-1)


def dense(inputs: np.ndarray, weights: np.ndarray, biases: np.ndarray) -> np.ndarray:
    """Fully connected layer.

    Args:
        inputs: ``(fan_in,)``.
        weights: ``(fan_in, fan_out)``.
        biases: ``(fan_out,)``.

    Returns:
        ``(fan_out,)``.
    """
    return inputs @ weights + biases


def dense_batched(
    inputs: np.ndarray, weights: np.ndarray, biases: np.ndarray
) -> np.ndarray:
    """Dense layer evaluated for a stack of weight variants at once.

    This is what makes the repaired networks tractable: each expert differs
    from the original only by a delta on one dense layer, so all variants share
    a trunk and diverge in a single batched matmul.

    Args:
        inputs: ``(fan_in,)`` shared across variants, or ``(S, fan_in)`` when
            variants have already diverged upstream.
        weights: ``(S, fan_in, fan_out)``.
        biases: ``(fan_out,)``, broadcast across variants.

    Returns:
        ``(S, fan_out)``.
    """
    if inputs.ndim == 1:
        return np.einsum("i,sio->so", inputs, weights, optimize=True) + biases
    return np.einsum("si,sio->so", inputs, weights, optimize=True) + biases
