"""Rewrite the artifact's CSV input datasets in the compressed codebook form.

The MNIST inputs ship as 90 MB CSV files, ten of them. Each is an 8-bit image
perturbed by FGSM and clipped, so the array draws on only a few hundred
distinct values and compresses to about 3 MB without losing anything. See
:mod:`nnrepair.datasets`.

Usage::

    python tools/compress_datasets.py <NNRepair/NN-Code dir> [--out DIR] [--check]

``--check`` re-reads each output and asserts it reproduces the text exactly.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nnrepair.datasets import compress_dataset, load_inputs  # noqa: E402


def find_datasets(root: Path) -> list[Path]:
    """Return the CSV input files under an ``NN-Code`` tree.

    Label files are excluded: they are a few kilobytes and stay as text.
    """
    return sorted(
        path
        for path in root.rglob("*.txt")
        if path.parent.name in {"data", "val-data"} and "label" not in path.name.lower()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="NN-Code directory to scan")
    parser.add_argument("--out", type=Path, help="Mirror outputs here instead of alongside")
    parser.add_argument("--check", action="store_true", help="Verify each output round-trips")
    args = parser.parse_args()

    datasets = find_datasets(args.root)
    if not datasets:
        print(f"No input datasets found under {args.root}", file=sys.stderr)
        return 1

    total_before = total_after = 0

    for source in datasets:
        if args.out:
            destination = args.out / source.relative_to(args.root).with_suffix(".npz")
            destination.parent.mkdir(parents=True, exist_ok=True)
        else:
            destination = None

        started = time.perf_counter()
        written = compress_dataset(source, destination)
        elapsed = time.perf_counter() - started

        before = source.stat().st_size
        after = written.stat().st_size
        total_before += before
        total_after += after

        note = ""
        if args.check:
            reference = np.loadtxt(source, delimiter=",", dtype=np.float64, ndmin=2)
            if not np.array_equal(load_inputs(written), reference):
                print(f"  MISMATCH for {source.name}", file=sys.stderr)
                return 2
            note = "  verified exact"

        print(
            f"{source.name:44s} {before / 1e6:7.1f} MB -> {after / 1e6:5.1f} MB "
            f"({before / after:4.1f}x, {elapsed:4.1f}s){note}"
        )

    print(
        f"\ntotal {total_before / 1e6:.0f} MB -> {total_after / 1e6:.0f} MB "
        f"({total_before / total_after:.1f}x)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
