"""Running a repair evaluation end to end.

Python port of ``CombinationCode/module4_combination/Experiments.java``.

The Java encoded its 100-odd experiment configurations as ``enum`` constants
with absolute Windows paths baked in
(``C:\\Users\\mlast\\Desktop\\experiments\\...``), which meant the file only
ran on its author's machine. :class:`Subject` takes those same fields as
ordinary arguments instead, and :func:`subjects_from_artifact` derives the
configurations from the repository layout.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np

from .combination import CombinationMethod, combine_experts, select_label_with_max_confidence
from .metrics import ConfusionCounts, OriginalConfusionCounts, PassFailCounts, round_half_up
from .models.cifar10 import CIFAR10InternalData, CIFAR10Network
from .models.mnist0 import MNIST0InternalData, MNIST0Network
from .z3_solutions import load_repaired_weights_cifar10, load_repaired_weights_mnist0

__all__ = [
    "Subject",
    "ExperimentResult",
    "run_experiment",
    "read_inputs",
    "read_labels",
    "RESULT_COLUMNS",
]

RESULT_COLUMNS = [
    "COMBINATION", "ACCURACY", "PASS", "FAIL", "TAR-ACC", "TAR-PASS", "TAR-FAIL",
    "TP", "TN", "FP", "FN", "PREC", "RECALL", "F1",
]

ModelKind = Literal["mnist0", "cifar10"]

_INPUT_SHAPES: dict[ModelKind, tuple[int, int, int]] = {
    "mnist0": (28, 28, 1),
    "cifar10": (32, 32, 3),
}


@dataclass(frozen=True)
class Subject:
    """One experiment configuration.

    Attributes:
        name: Identifier used for output filenames, e.g.
            ``POISONED_CIFAR_LAST_LAYER_ExpA_TEST``.
        model: Which network architecture to build.
        params_path: Directory of extracted ``weights*.txt`` / ``biases*.txt``.
        repair_path: Directory of Z3 solution files for this repair.
        solution_file_name_prefix: Filename stem for last-layer solutions.
        repaired_layer_id: Layer the repair targets.
        input_file_path: CSV of flattened input images, one per line.
        label_file_path: One integer label per line.
        needs_normalization: Divide inputs by 255.
        train_precision: Per-expert training precision, required by the PREC
            and PVC methods. Empty disables them.
        f1_selected_experts: Expert subset chosen by plain-F1 selection.
        f1_harmonic_selected_experts: Subset chosen by harmonic-F1 selection.
        output_path: Directory for result CSVs. ``None`` skips writing.
    """

    name: str
    model: ModelKind
    params_path: Path
    repair_path: Path
    repaired_layer_id: int
    input_file_path: Path
    label_file_path: Path
    solution_file_name_prefix: str = "solution"
    needs_normalization: bool = True
    train_precision: Sequence[float] = field(default_factory=tuple)
    f1_selected_experts: Sequence[int] = field(default_factory=tuple)
    f1_harmonic_selected_experts: Sequence[int] = field(default_factory=tuple)
    output_path: Path | None = None

    @property
    def input_shape(self) -> tuple[int, int, int]:
        return _INPUT_SHAPES[self.model]


@dataclass
class ExperimentResult:
    """Outcome of one :func:`run_experiment` call.

    Attributes:
        subject: The configuration that produced this.
        combination_counts: Accuracy per combination method.
        expert_counts: Confusion counts per repaired expert.
        original_counts: Confusion counts for the unrepaired network per label.
        evaluated: Number of inputs scored.
    """

    subject: Subject
    combination_counts: dict[CombinationMethod, PassFailCounts]
    expert_counts: dict[int, ConfusionCounts]
    original_counts: dict[int, OriginalConfusionCounts]
    evaluated: int

    def rows(self) -> list[dict[str, object]]:
        """Render every row of the result CSV, in the Java's order."""
        rows: list[dict[str, object]] = []
        for method in CombinationMethod.selectable():
            counts = self.combination_counts.get(method)
            if counts is None or counts.total == 0:
                continue
            rows.append(
                {
                    **{column: "" for column in RESULT_COLUMNS},
                    "COMBINATION": method.value,
                    "ACCURACY": round_half_up(counts.accuracy),
                    "PASS": counts.passed,
                    "FAIL": counts.failed,
                }
            )
        rows.extend(counts.as_row() for counts in self.expert_counts.values())
        rows.extend(counts.as_row() for counts in self.original_counts.values())
        return rows

    def prec_f1(self) -> dict[str, list]:
        """Build the ``*_prec_f1.csv`` sidecar contents."""
        expert_ids = sorted(self.expert_counts)
        f1_values = [self.expert_counts[i].f1 for i in expert_ids]
        f1_original = [self.original_counts[i].f1 for i in expert_ids]
        return {
            "prec": [self.expert_counts[i].precision for i in expert_ids],
            "f1Experts": [
                expert_id
                for expert_id, repaired, original in zip(expert_ids, f1_values, f1_original)
                if repaired > original
            ],
            "f1_values": f1_values,
            "f1_values_original": f1_original,
        }

    def write(self, output_path: Path | None = None, suffix: str = "") -> list[Path]:
        """Write the result CSV and its ``_prec_f1`` sidecar.

        Args:
            output_path: Target directory; defaults to the subject's.
            suffix: Filename suffix, e.g. ``"_f1"`` or ``"_f1har"``.

        Returns:
            The files written; empty when no output directory is configured.
        """
        directory = output_path or self.subject.output_path
        if directory is None:
            return []
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        result_file = directory / f"{self.subject.name}{suffix}.csv"
        with result_file.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS, delimiter=";")
            writer.writeheader()
            writer.writerows(self.rows())

        sidecar = directory / f"{self.subject.name}{suffix}_prec_f1.csv"
        values = self.prec_f1()
        sidecar.write_text(
            "".join(f"{key}={list(value)}\n" for key, value in values.items()),
            encoding="utf-8",
        )
        return [result_file, sidecar]


def read_labels(path: str | Path, limit: int | None = None) -> np.ndarray:
    """Read one integer label per line."""
    labels = np.loadtxt(path, dtype=np.int64, ndmin=1)
    return labels[:limit] if limit is not None else labels


def read_inputs(
    path: str | Path,
    shape: tuple[int, int, int],
    needs_normalization: bool,
    limit: int | None = None,
) -> Iterator[np.ndarray]:
    """Stream input images from a CSV of flattened pixels.

    These files reach 94 MB, so they are read line by line rather than loaded
    whole — the Java did the same, and it keeps the Streamlit app's memory flat.

    Args:
        path: CSV file, one flattened image per line.
        shape: Target ``(H, W, C)``.
        needs_normalization: Divide by 255.
        limit: Stop after this many images.

    Yields:
        Arrays of the requested shape.

    Raises:
        ValueError: If a line's pixel count does not match ``shape``.
    """
    expected = int(np.prod(shape))
    with Path(path).open("r", encoding="utf-8", errors="replace") as handle:
        for index, line in enumerate(handle):
            if limit is not None and index >= limit:
                return
            line = line.strip()
            if not line:
                continue
            values = np.fromstring(line, sep=",", dtype=np.float64)
            if values.size != expected:
                raise ValueError(
                    f"{path}: line {index + 1} has {values.size} values, expected {expected}"
                )
            if needs_normalization:
                values = values / 255.0
            yield values.reshape(shape)


def _build_model(subject: Subject, expert_ids: Sequence[int], number_of_experts: int):
    """Load weights and repair deltas, and construct the network."""
    if subject.model == "mnist0":
        internal = MNIST0InternalData.from_directory(subject.params_path)
        deltas = load_repaired_weights_mnist0(
            subject.repair_path,
            subject.solution_file_name_prefix,
            subject.repaired_layer_id,
            expert_ids,
            number_of_experts,
        )
        return MNIST0Network(internal, deltas)

    internal = CIFAR10InternalData.from_directory(subject.params_path)
    deltas = load_repaired_weights_cifar10(
        subject.repair_path,
        subject.solution_file_name_prefix,
        subject.repaired_layer_id,
        expert_ids,
        number_of_experts,
    )
    return CIFAR10Network(internal, deltas)


def run_experiment(
    subject: Subject,
    comb_method: CombinationMethod = CombinationMethod.ALL,
    stop_after: int | None = None,
    use_f1_selection: bool = False,
    use_f1_harmonic_selection: bool = False,
    number_of_experts: int = 10,
    progress: object | None = None,
) -> ExperimentResult:
    """Evaluate a repaired network over a dataset.

    Args:
        subject: The configuration to run.
        comb_method: A single combination method, or ``ALL``.
        stop_after: Evaluate at most this many inputs.
        use_f1_selection: Restrict to the subject's plain-F1 expert subset.
        use_f1_harmonic_selection: Restrict to the harmonic-F1 subset.
        number_of_experts: Expert count for the architecture.
        progress: Optional callable invoked as ``progress(done, total)``.

    Returns:
        The collected metrics.

    Raises:
        ValueError: If both selection modes are requested at once.
        FileNotFoundError: If weights, solutions or datasets are missing.
    """
    if use_f1_selection and use_f1_harmonic_selection:
        raise ValueError("Choose at most one of f1 selection and f1-harmonic selection.")

    if use_f1_selection:
        expert_ids = list(subject.f1_selected_experts)
    elif use_f1_harmonic_selection:
        expert_ids = list(subject.f1_harmonic_selected_experts)
    else:
        expert_ids = list(range(number_of_experts))

    model = _build_model(subject, expert_ids, number_of_experts)

    labels = read_labels(subject.label_file_path, stop_after)
    total = len(labels)

    combination_counts = {method: PassFailCounts() for method in CombinationMethod.selectable()}
    expert_counts = {i: ConfusionCounts(label=i) for i in expert_ids}
    original_counts = {i: OriginalConfusionCounts(label=i) for i in expert_ids}

    train_precision = np.asarray(subject.train_precision, dtype=np.float64)

    evaluated = 0
    inputs = read_inputs(
        subject.input_file_path, subject.input_shape, subject.needs_normalization, stop_after
    )
    for index, image in enumerate(inputs):
        if index >= total:
            break

        result = model.run(image, subject.repaired_layer_id, expert_ids)
        correct_label = int(labels[index])
        orig_label = select_label_with_max_confidence(result[-1])

        for method, label in combine_experts(
            comb_method, result, orig_label, train_precision, expert_ids, False, number_of_experts
        ).items():
            combination_counts[method].record(label == correct_label)

        for expert_id in expert_ids:
            predicted = select_label_with_max_confidence(result[expert_id])
            expert_counts[expert_id].record(predicted, correct_label)
            original_counts[expert_id].record(orig_label, correct_label)

        evaluated += 1
        if progress is not None and callable(progress):
            progress(evaluated, total)

    return ExperimentResult(
        subject=subject,
        combination_counts=combination_counts,
        expert_counts=expert_counts,
        original_counts=original_counts,
        evaluated=evaluated,
    )
