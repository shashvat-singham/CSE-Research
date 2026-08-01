"""Reading input datasets, in text or compressed form.

The artifact ships its MNIST inputs as CSV text: 10,000 rows of 784
fixed-point decimals, 90 MB per file, ten files. That is 900 MB to distribute
a quantity of information that is far smaller than it looks.

Each file is an 8-bit image perturbed by FGSM and clipped to ``[0, 1]``, so the
whole 7.8-million-value array draws on only a few hundred distinct values. This
module stores that as a **codebook**: a ``uint16`` index per pixel plus a
``float64`` table of the distinct values. Round-tripping is exact — the values
that come back are the same float64s ``numpy.loadtxt`` produces from the text —
and a 90 MB file becomes about 3 MB.

Both formats are read through :func:`load_inputs` and :func:`iter_inputs`, so
callers do not care which is on disk. Text remains authoritative; the
compressed form is a distribution convenience, written by
``tools/compress_datasets.py``.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import numpy as np

__all__ = [
    "CODEBOOK_SUFFIX",
    "compress_dataset",
    "iter_inputs",
    "load_inputs",
    "resolve_dataset",
]

#: Extension used for the compressed form.
CODEBOOK_SUFFIX = ".npz"

#: Ceiling on distinct values before the codebook stops paying for itself.
_MAX_CODEBOOK_VALUES = 60_000


def resolve_dataset(path: str | Path) -> Path:
    """Return the file to actually read for a dataset.

    Prefers a sibling ``.npz`` when one exists, so a deployment can ship the
    compressed form while code and configuration keep naming the ``.txt``.

    Args:
        path: The dataset path as configured, usually the ``.txt``.

    Returns:
        The compressed sibling if present, else ``path`` unchanged.
    """
    path = Path(path)
    if path.suffix == CODEBOOK_SUFFIX:
        return path
    compressed = path.with_suffix(CODEBOOK_SUFFIX)
    return compressed if compressed.exists() else path


def compress_dataset(source: str | Path, destination: str | Path | None = None) -> Path:
    """Rewrite a CSV dataset as a codebook ``.npz``.

    Args:
        source: The ``.txt`` file of comma-separated rows.
        destination: Output path; defaults to ``source`` with an ``.npz``
            extension.

    Returns:
        The path written.

    Raises:
        FileNotFoundError: If ``source`` does not exist.
        ValueError: If the data holds too many distinct values for a
            ``uint16`` codebook to represent.
    """
    source = Path(source)
    target = Path(destination) if destination else source.with_suffix(CODEBOOK_SUFFIX)

    data = np.loadtxt(source, delimiter=",", dtype=np.float64, ndmin=2)
    values, codes = np.unique(data, return_inverse=True)

    if values.size > _MAX_CODEBOOK_VALUES:
        raise ValueError(
            f"{source.name} holds {values.size} distinct values, too many for a "
            "uint16 codebook. Ship the text file instead."
        )

    codes = codes.astype(np.uint16).reshape(data.shape)
    if not np.array_equal(values[codes], data):
        raise ValueError(f"{source.name}: codebook round-trip is not exact; refusing to write.")

    np.savez_compressed(target, codes=codes, values=values)
    return target


def _decode(archive: np.lib.npyio.NpzFile) -> np.ndarray:
    """Rebuild the float64 array from a codebook archive."""
    return archive["values"][archive["codes"]]


def load_inputs(path: str | Path, limit: int | None = None) -> np.ndarray:
    """Load a whole dataset as ``(rows, features)`` float64.

    Args:
        path: Dataset path; a ``.npz`` sibling is preferred automatically.
        limit: Read at most this many rows.

    Returns:
        The inputs, unnormalised.

    Raises:
        FileNotFoundError: If neither form exists.
    """
    resolved = resolve_dataset(path)

    if resolved.suffix == CODEBOOK_SUFFIX:
        with np.load(resolved) as archive:
            codes = archive["codes"]
            if limit is not None:
                codes = codes[:limit]
            return archive["values"][codes]

    return np.loadtxt(resolved, delimiter=",", dtype=np.float64, ndmin=2, max_rows=limit)


def iter_inputs(
    path: str | Path,
    shape: tuple[int, ...],
    needs_normalization: bool,
    limit: int | None = None,
) -> Iterator[np.ndarray]:
    """Stream a dataset one reshaped image at a time.

    Text files are read line by line so a 90 MB file never lands in memory at
    once. A codebook archive is loaded whole — decoded, the largest here is
    about 60 MB, and slicing it is what makes the compressed form fast.

    Args:
        path: Dataset path; a ``.npz`` sibling is preferred automatically.
        shape: Target ``(H, W, C)`` per image.
        needs_normalization: Divide by 255. The FGSM files are already in
            ``[0, 1]`` and must not be divided again.
        limit: Stop after this many images.

    Yields:
        Arrays of the requested shape.

    Raises:
        ValueError: If a row's length does not match ``shape``.
    """
    resolved = resolve_dataset(path)
    expected = int(np.prod(shape))

    if resolved.suffix == CODEBOOK_SUFFIX:
        data = load_inputs(resolved, limit)
        if data.shape[1] != expected:
            raise ValueError(
                f"{resolved.name}: rows have {data.shape[1]} values, expected {expected}"
            )
        if needs_normalization:
            data = data / 255.0
        for row in data:
            yield row.reshape(shape)
        return

    with resolved.open("r", encoding="utf-8", errors="replace") as handle:
        emitted = 0
        for index, line in enumerate(handle):
            if limit is not None and emitted >= limit:
                return
            line = line.strip()
            if not line:
                continue
            values = np.fromstring(line, sep=",", dtype=np.float64)
            if values.size != expected:
                raise ValueError(
                    f"{resolved.name}: line {index + 1} has {values.size} values, "
                    f"expected {expected}"
                )
            if needs_normalization:
                values = values / 255.0
            emitted += 1
            yield values.reshape(shape)
