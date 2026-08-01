"""Network architectures and their layer primitives."""

from __future__ import annotations

from .cifar10 import CIFAR10Network
from .internal_data import CIFAR10InternalData, MNIST0InternalData
from .layers import conv2d_valid, dense, dense_batched, flatten, maxpool2d, relu
from .mnist0 import MNIST0Network

__all__ = [
    "CIFAR10InternalData",
    "CIFAR10Network",
    "MNIST0InternalData",
    "MNIST0Network",
    "conv2d_valid",
    "dense",
    "dense_batched",
    "flatten",
    "maxpool2d",
    "relu",
]
