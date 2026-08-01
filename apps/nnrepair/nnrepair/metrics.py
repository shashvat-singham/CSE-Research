"""Per-expert classification bookkeeping.

Python port of the counter maps threaded through ``Experiments.java``.

Each expert is a *binary* detector for its own label, so it gets a confusion
matrix rather than a plain accuracy. For expert ``k`` on an input whose true
label is ``y`` and on which the expert predicted ``p``:

======================  ==========================================
Outcome                 Condition
======================  ==========================================
True positive           ``p == y == k``
False negative          ``p != y`` and ``y == k``
False positive          ``p != y`` and ``p == k``
True negative           everything else
======================  ==========================================

"Targeted" accuracy restricts attention to inputs where ``y == k`` — the label
the expert was actually repaired for, and the number the paper reports.
"""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

import numpy as np

__all__ = ["ConfusionCounts", "PassFailCounts", "round_half_up"]


def round_half_up(value: float, places: int = 2) -> float:
    """Round half away from zero, matching Java's ``BigDecimal.HALF_UP``.

    Python's built-in :func:`round` uses banker's rounding, so ``round(0.125,
    2)`` is ``0.12`` where Java gives ``0.13``. Result files in this repository
    were produced with the Java behaviour, so reproducing them requires it.

    ``NaN`` passes through unchanged, as it does in the Java.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return float("nan")
    if places < 0:
        raise ValueError("places must be non-negative")
    quantum = Decimal(1).scaleb(-places)
    return float(Decimal(repr(float(value))).quantize(quantum, rounding=ROUND_HALF_UP))


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Divide, yielding ``NaN`` on a zero denominator as Java's doubles do."""
    if denominator == 0:
        return float("nan")
    return numerator / denominator


@dataclass
class PassFailCounts:
    """Overall correct/incorrect tallies."""

    passed: int = 0
    failed: int = 0

    def record(self, correct: bool) -> None:
        if correct:
            self.passed += 1
        else:
            self.failed += 1

    @property
    def total(self) -> int:
        return self.passed + self.failed

    @property
    def accuracy(self) -> float:
        """Percentage correct, or ``NaN`` when nothing was evaluated."""
        return _safe_ratio(self.passed, self.total) * 100.0


@dataclass
class ConfusionCounts:
    """Confusion matrix and targeted tallies for one expert.

    Attributes:
        label: The label this expert specialises in.
    """

    label: int
    passed: int = 0
    failed: int = 0
    targeted_pass: int = 0
    targeted_fail: int = 0
    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0

    def record(self, predicted: int, correct_label: int) -> None:
        """Fold in one prediction."""
        is_correct = predicted == correct_label
        is_own_label = correct_label == self.label

        if is_correct:
            self.passed += 1
            if is_own_label:
                self.tp += 1
                self.targeted_pass += 1
            else:
                self.tn += 1
        else:
            self.failed += 1
            if is_own_label:
                self.fn += 1
                self.targeted_fail += 1
            elif predicted == self.label:
                self.fp += 1
            else:
                self.tn += 1

    @property
    def total(self) -> int:
        return self.passed + self.failed

    @property
    def accuracy(self) -> float:
        return _safe_ratio(self.passed, self.total) * 100.0

    @property
    def targeted_total(self) -> int:
        return self.targeted_pass + self.targeted_fail

    @property
    def targeted_accuracy(self) -> float:
        """Accuracy restricted to inputs whose true label is this expert's."""
        return _safe_ratio(self.targeted_pass, self.targeted_total) * 100.0

    @property
    def precision(self) -> float:
        """``TP / (TP + FP)`` as a fraction, ``NaN`` if the expert never fired."""
        return _safe_ratio(self.tp, self.tp + self.fp)

    @property
    def recall(self) -> float:
        """``TP / (TP + FN)`` as a fraction."""
        return _safe_ratio(self.tp, self.tp + self.fn)

    @property
    def f1(self) -> float:
        """Harmonic mean of precision and recall, as a fraction."""
        precision = self.precision
        recall = self.recall
        return _safe_ratio(2 * precision * recall, precision + recall)

    def as_row(self, name: str | None = None) -> dict[str, object]:
        """Render as one result-CSV row, percentages rounded like the Java."""
        return {
            "COMBINATION": name if name is not None else f"L{self.label}",
            "ACCURACY": round_half_up(self.accuracy),
            "PASS": self.passed,
            "FAIL": self.failed,
            "TAR-ACC": round_half_up(self.targeted_accuracy),
            "TAR-PASS": self.targeted_pass,
            "TAR-FAIL": self.targeted_fail,
            "TP": self.tp,
            "TN": self.tn,
            "FP": self.fp,
            "FN": self.fn,
            "PREC": round_half_up(self.precision * 100.0),
            "RECALL": round_half_up(self.recall * 100.0),
            "F1": round_half_up(self.f1 * 100.0),
        }


@dataclass
class OriginalConfusionCounts(ConfusionCounts):
    """Confusion counts for the *unrepaired* network, scoped to one label.

    Identical bookkeeping to :class:`ConfusionCounts`, but the overall
    pass/fail columns are left blank in the CSV because they would repeat the
    same original-model accuracy on every row.
    """

    _blank: tuple[str, ...] = field(
        default=("ACCURACY", "PASS", "FAIL"), repr=False, compare=False
    )

    def as_row(self, name: str | None = None) -> dict[str, object]:
        row = super().as_row(name if name is not None else f"ORIG_L{self.label}")
        for column in self._blank:
            row[column] = ""
        return row
