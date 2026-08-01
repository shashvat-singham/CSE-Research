"""Loading of extracted network weights.

Python port of ``MNIST0_InternalData.java`` and ``CIFAR10_InternalData.java``.

Both Java classes hand-roll a reader per tensor: read a text file of
comma-separated rows, flatten it into a 1-D buffer, then walk nested loops to
place values into a rectangular array. Every one of those loops iterates in
row-major order, so the whole exercise is a ``reshape`` — which is what this
module does, in four lines per tensor instead of forty.

Weight files are the raw dumps under ``NN-Code/<subject>/params/``. They are
large (up to 17 MB) and excluded from the deployed apps; see
``NN-Code/README.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import numpy as np

__all__ = ["MNIST0InternalData", "CIFAR10InternalData", "load_tensor", "load_vector"]


def load_tensor(path: str | Path, shape: tuple[int, ...]) -> np.ndarray:
    """Read a comma-separated weight dump and reshape it.

    Args:
        path: File of comma-separated rows, blank lines allowed.
        shape: Target shape; its product must equal the value count.

    Returns:
        A ``float64`` array of the requested shape.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If the file holds the wrong number of values.
    """
    path = Path(path)
    values = np.loadtxt(path, delimiter=",", dtype=np.float64, ndmin=1).reshape(-1)
    expected = int(np.prod(shape))
    if values.size != expected:
        raise ValueError(
            f"{path.name}: expected {expected} values for shape {shape}, got {values.size}"
        )
    return values.reshape(shape)


def load_vector(path: str | Path, size: int) -> np.ndarray:
    """Read a one-value-per-line bias dump.

    Raises:
        ValueError: If the file does not hold exactly ``size`` values.
    """
    return load_tensor(path, (size,))


@dataclass(frozen=True)
class MNIST0InternalData:
    """Weights and biases of the MNIST0 network.

    Layer shapes, following the Keras model the artifact was extracted from:

    ==========  =============  ===================
    Layer       Weights        Biases
    ==========  =============  ===================
    0 conv2d_1  ``3x3x1x2``    ``2``
    2 conv2d_2  ``3x3x2x4``    ``4``
    6 dense_1   ``576x128``    ``128``
    8 dense_2   ``128x10``     ``10``
    ==========  =============  ===================
    """

    weights0: np.ndarray
    weights2: np.ndarray
    weights6: np.ndarray
    weights8: np.ndarray
    biases0: np.ndarray
    biases2: np.ndarray
    biases6: np.ndarray
    biases8: np.ndarray

    @classmethod
    def from_directory(
        cls,
        path: str | Path,
        weights0file: str = "weights0.txt",
        weights2file: str = "weights2.txt",
        weights6file: str = "weights6.txt",
        weights8file: str = "weights8.txt",
        bias0file: str = "biases0.txt",
        bias2file: str = "biases2.txt",
        bias6file: str = "biases6.txt",
        bias8file: str = "biases8.txt",
    ) -> "MNIST0InternalData":
        """Load every tensor from a ``params`` directory."""
        base = Path(path)
        return cls(
            weights0=load_tensor(base / weights0file, (3, 3, 1, 2)),
            weights2=load_tensor(base / weights2file, (3, 3, 2, 4)),
            weights6=load_tensor(base / weights6file, (576, 128)),
            weights8=load_tensor(base / weights8file, (128, 10)),
            biases0=load_vector(base / bias0file, 2),
            biases2=load_vector(base / bias2file, 4),
            biases6=load_vector(base / bias6file, 128),
            biases8=load_vector(base / bias8file, 10),
        )

    @cached_property
    def input_shape(self) -> tuple[int, int, int]:
        return (28, 28, 1)


@dataclass(frozen=True)
class CIFAR10InternalData:
    """Weights and biases of the CIFAR10 network.

    ===========  ==============  ==========
    Layer        Weights         Biases
    ===========  ==============  ==========
    0 conv2d_1   ``3x3x3x32``    ``32``
    2 conv2d_2   ``3x3x32x32``   ``32``
    5 conv2d_3   ``3x3x32x64``   ``64``
    7 conv2d_4   ``3x3x64x64``   ``64``
    11 dense_1   ``1600x512``    ``512``
    13 dense_2   ``512x10``      ``10``
    ===========  ==============  ==========
    """

    weights0: np.ndarray
    weights2: np.ndarray
    weights5: np.ndarray
    weights7: np.ndarray
    weights11: np.ndarray
    weights13: np.ndarray
    biases0: np.ndarray
    biases2: np.ndarray
    biases5: np.ndarray
    biases7: np.ndarray
    biases11: np.ndarray
    biases13: np.ndarray

    @classmethod
    def from_directory(cls, path: str | Path) -> "CIFAR10InternalData":
        """Load every tensor from a ``params`` directory."""
        base = Path(path)
        return cls(
            weights0=load_tensor(base / "weights0.txt", (3, 3, 3, 32)),
            weights2=load_tensor(base / "weights2.txt", (3, 3, 32, 32)),
            weights5=load_tensor(base / "weights5.txt", (3, 3, 32, 64)),
            weights7=load_tensor(base / "weights7.txt", (3, 3, 64, 64)),
            weights11=load_tensor(base / "weights11.txt", (1600, 512)),
            weights13=load_tensor(base / "weights13.txt", (512, 10)),
            biases0=load_vector(base / "biases0.txt", 32),
            biases2=load_vector(base / "biases2.txt", 32),
            biases5=load_vector(base / "biases5.txt", 64),
            biases7=load_vector(base / "biases7.txt", 64),
            biases11=load_vector(base / "biases11.txt", 512),
            biases13=load_vector(base / "biases13.txt", 10),
        )

    @cached_property
    def input_shape(self) -> tuple[int, int, int]:
        return (32, 32, 3)
