"""Selecting which experts to keep, by F1 score.

Python port of ``CombinationCode/module4_combination/F1SelectionHarmonic.java``.

Not every repaired expert is an improvement — some make their label worse than
the original network did. These helpers read the ``*_prec_f1.csv`` sidecar
files the experiment runner emits and return the experts worth keeping.

Two criteria:

* **Plain F1** — keep expert ``k`` when its repaired F1 on one dataset beats
  the original network's F1 for label ``k``.
* **Harmonic F1** — keep expert ``k`` when the harmonic mean of its F1 on the
  *adversarial* training set and on the *clean* training set beats the same
  mean for the original. This is the stricter test: an expert that fixes
  adversarial inputs by wrecking clean accuracy scores well on one set and
  badly on the mean, so it is dropped.

The Java ``main`` hardcoded one subject and an absolute path on the author's
machine. Here the paths are arguments.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

__all__ = [
    "PrecF1Record",
    "read_prec_f1",
    "harmonic_mean",
    "select_experts_by_f1",
    "select_experts_by_harmonic_f1",
]

_ARRAY_LINE_RE = re.compile(r"^(?P<key>[A-Za-z0-9_]+)\s*=\s*(?P<value>\[.*\])\s*$")


@dataclass(frozen=True)
class PrecF1Record:
    """Contents of one ``*_prec_f1.csv`` sidecar file.

    Attributes:
        prec: Per-expert precision of the repaired network.
        f1_values: Per-expert F1 of the repaired network.
        f1_values_original: Per-label F1 of the unrepaired network.
        f1_experts: Experts the runner already flagged as improvements.
    """

    prec: np.ndarray
    f1_values: np.ndarray
    f1_values_original: np.ndarray
    f1_experts: list[int]


def read_prec_f1(path: str | Path) -> PrecF1Record:
    """Parse a ``*_prec_f1.csv`` sidecar.

    The format is one ``key=[...]`` assignment per line, e.g.::

        prec=[0.3659, 0.4353, ...]
        f1Experts=[0, 1, 2, 3, 4, 6, 7, 8, 9]
        f1_values=[0.3937, 0.5320, ...]

    The Java parsed these with fixed substring offsets (``line.substring(11)``)
    and a hardcoded ten-element loop. This reads them by key, so a missing or
    reordered line is a clear error rather than a silent misparse.

    Args:
        path: The sidecar file.

    Returns:
        The parsed record. Absent keys yield empty arrays.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
    """
    values: dict[str, list[float]] = {}
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        match = _ARRAY_LINE_RE.match(line.strip())
        if match:
            try:
                parsed = ast.literal_eval(match.group("value"))
            except (ValueError, SyntaxError):
                continue
            if isinstance(parsed, list):
                values[match.group("key")] = parsed

    def array(key: str) -> np.ndarray:
        return np.asarray(values.get(key, []), dtype=np.float64)

    return PrecF1Record(
        prec=array("prec"),
        f1_values=array("f1_values"),
        f1_values_original=array("f1_values_original"),
        f1_experts=[int(x) for x in values.get("f1Experts", [])],
    )


def harmonic_mean(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Element-wise ``2ab / (a + b)``.

    Returns ``0`` where ``a + b`` is zero. The Java produced ``NaN`` there,
    and ``NaN > NaN`` is false, so both drop the expert — but ``0`` keeps the
    returned array usable for plotting.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    total = a + b
    return np.divide(2.0 * a * b, total, out=np.zeros_like(total), where=total != 0)


def select_experts_by_f1(record: PrecF1Record) -> list[int]:
    """Return experts whose repaired F1 beats the original's."""
    if record.f1_values.size == 0 or record.f1_values_original.size == 0:
        return []
    return [
        i
        for i in range(min(record.f1_values.size, record.f1_values_original.size))
        if record.f1_values[i] > record.f1_values_original[i]
    ]


def select_experts_by_harmonic_f1(
    adversarial: PrecF1Record,
    clean: PrecF1Record,
) -> tuple[list[int], np.ndarray, np.ndarray]:
    """Return experts that improve the harmonic mean of both datasets' F1.

    Args:
        adversarial: Record from the adversarial (or poisoned) training set.
        clean: Record from the clean training set.

    Returns:
        A tuple of the selected expert ids, the repaired harmonic F1 per
        expert, and the original harmonic F1 per label.
    """
    repaired = harmonic_mean(adversarial.f1_values, clean.f1_values)
    original = harmonic_mean(
        adversarial.f1_values_original, clean.f1_values_original
    )
    selected = [i for i in range(repaired.size) if repaired[i] > original[i]]
    return selected, repaired, original


def format_selection(selected: Sequence[int]) -> str:
    """Render a selection the way the Java printed it, e.g. ``[0, 1, 4]``."""
    return "[" + ", ".join(str(i) for i in selected) + "]"
