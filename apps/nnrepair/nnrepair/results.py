"""Reading the shipped experiment results.

The ``NNRepair/Results`` tree holds 345 CSVs produced by the original Java
runner. Their metadata lives entirely in directory and file names, e.g.::

    Results/Cifar-Adversarial/Lastlayer/CIFAR_LAST_LAYER_Eps0_01_ExpA_ADV_TEST.csv
            ^-- subject        ^-- layer                 ^-- eps ^-- exp ^-- dataset

This module turns that convention into a tidy DataFrame so the explorer can
filter and compare without re-deriving the naming rules everywhere.

Two file kinds share the tree:

* **Result files** — semicolon-separated, one row per combination method and
  per expert.
* **Sidecars** (``*_prec_f1.csv``) — ``key=[...]`` lines, parsed by
  :func:`~nnrepair.f1_selection.read_prec_f1`.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

__all__ = [
    "ResultFile",
    "describe_result_file",
    "discover_results",
    "load_result_csv",
    "load_results_index",
    "COMBINATION_METHODS",
]

#: Combination-method rows, as opposed to the per-expert ``L*`` rows.
COMBINATION_METHODS = ("NAIVE", "AVERAGE", "FULL", "PREC", "CONF", "VOTES", "PVC", "ORIG")

_EPS_RE = re.compile(r"_?Eps([0-9_.]+?)(?=_Exp|_TEST|_TRAINING|_ADV|_POISONED|$)", re.IGNORECASE)
_EXP_RE = re.compile(r"_(Exp[A-D])(?=_|$)", re.IGNORECASE)

# Longest first, so ADV_TRAINING is not truncated to TRAINING.
_DATASETS = (
    "POISONED_TRAINING", "POISONED_TEST",
    "ADV_TRAINING", "ADV_TEST",
    "TRAINING", "TEST",
)


@dataclass(frozen=True)
class ResultFile:
    """Metadata decoded from one result file's path.

    Attributes:
        path: Location on disk.
        subject: Model and fault kind, e.g. ``Cifar-Adversarial``.
        layer: ``Lastlayer`` or ``IntermediateLayer``.
        experiment: ``ExpA``-``ExpD``, the 0/10/50/100 passing-test scenarios.
        dataset: Which split was evaluated, e.g. ``ADV_TEST``.
        epsilon: FGSM perturbation size, for adversarial subjects only.
        selection: ``all``, ``f1``, or ``f1har`` — which experts were kept.
        is_sidecar: True for ``*_prec_f1.csv`` files.
        stem: Filename without extension.
    """

    path: Path
    subject: str
    layer: str
    experiment: str | None
    dataset: str | None
    epsilon: str | None
    selection: str
    is_sidecar: bool
    stem: str

    @property
    def passing_tests(self) -> int | None:
        """Passing tests used during repair, decoded from the experiment id.

        ExpA-D correspond to 0, 10, 50 and 100 passing tests respectively.
        """
        return {"ExpA": 0, "ExpB": 10, "ExpC": 50, "ExpD": 100}.get(self.experiment or "")


def describe_result_file(path: str | Path, results_root: str | Path) -> ResultFile:
    """Decode a result file's metadata from its path.

    Args:
        path: The CSV file.
        results_root: The ``Results`` directory it sits under.

    Returns:
        Parsed metadata. Unrecognised components come back as ``None`` rather
        than raising, since a few files predate the naming convention.
    """
    path = Path(path)
    relative = path.relative_to(results_root)
    parts = relative.parts

    subject = parts[0] if len(parts) > 1 else "Unknown"
    layer = parts[1] if len(parts) > 2 else "Unknown"

    stem = path.stem
    remainder = stem

    is_sidecar = remainder.endswith("_prec_f1")
    if is_sidecar:
        remainder = remainder[: -len("_prec_f1")]

    if remainder.endswith("_f1har"):
        selection = "f1har"
        remainder = remainder[: -len("_f1har")]
    elif remainder.endswith("_f1"):
        selection = "f1"
        remainder = remainder[: -len("_f1")]
    else:
        selection = "all"

    upper = remainder.upper()
    dataset = next((d for d in _DATASETS if upper.endswith("_" + d) or upper == d), None)

    exp_match = _EXP_RE.search(remainder)
    experiment = exp_match.group(1).replace("exp", "Exp") if exp_match else None
    if experiment:
        experiment = "Exp" + experiment[-1].upper()

    eps_match = _EPS_RE.search(remainder)
    epsilon = eps_match.group(1).strip("_").replace("_", ".") if eps_match else None

    return ResultFile(
        path=path,
        subject=subject,
        layer=layer,
        experiment=experiment,
        dataset=dataset,
        epsilon=epsilon,
        selection=selection,
        is_sidecar=is_sidecar,
        stem=stem,
    )


def discover_results(results_root: str | Path) -> list[ResultFile]:
    """Find and decode every CSV under a ``Results`` tree.

    Args:
        results_root: The ``Results`` directory.

    Returns:
        Metadata for each CSV, sorted by path. Empty if the directory is absent.
    """
    root = Path(results_root)
    if not root.is_dir():
        return []
    return [describe_result_file(p, root) for p in sorted(root.rglob("*.csv"))]


def load_result_csv(path: str | Path) -> pd.DataFrame:
    """Read one semicolon-separated result file.

    The runner writes blank cells for columns that do not apply to a row
    (combination rows have no confusion matrix; ``ORIG_L*`` rows have no
    overall accuracy), so numeric columns are coerced rather than trusted.

    Args:
        path: The result CSV.

    Returns:
        One row per combination method and expert, with a ``ROW_KIND`` column
        distinguishing ``combination``, ``expert`` and ``original``.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
    """
    frame = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False)
    frame.columns = [c.strip() for c in frame.columns]

    if "COMBINATION" not in frame.columns:
        raise ValueError(f"{path} is not a result CSV (no COMBINATION column)")

    frame["COMBINATION"] = frame["COMBINATION"].str.strip()
    frame = frame[frame["COMBINATION"] != ""]

    def row_kind(name: str) -> str:
        if name.startswith("ORIG_L"):
            return "original"
        if name.startswith("L") and name[1:].isdigit():
            return "expert"
        return "combination"

    frame["ROW_KIND"] = frame["COMBINATION"].map(row_kind)
    frame["LABEL"] = (
        frame["COMBINATION"]
        .str.extract(r"L(\d+)$", expand=False)
        .astype("Int64")
    )

    for column in frame.columns:
        if column in {"COMBINATION", "ROW_KIND", "LABEL"}:
            continue
        frame[column] = pd.to_numeric(frame[column].replace("", None), errors="coerce")

    return frame


@lru_cache(maxsize=8)
def load_results_index(results_root: str) -> pd.DataFrame:
    """Build one DataFrame spanning every result file.

    Sidecars are skipped; read those with
    :func:`~nnrepair.f1_selection.read_prec_f1`. Files that fail to parse are
    skipped rather than aborting the index, so one malformed artifact does not
    take the explorer down.

    Args:
        results_root: The ``Results`` directory, as a string so the cache key
            is hashable.

    Returns:
        Every result row, annotated with the metadata from its filename.
    """
    frames = []
    for result_file in discover_results(results_root):
        if result_file.is_sidecar:
            continue
        try:
            frame = load_result_csv(result_file.path)
        except (ValueError, pd.errors.ParserError, UnicodeDecodeError):
            continue

        metadata = asdict(result_file)
        metadata.pop("path")
        metadata["passing_tests"] = result_file.passing_tests
        for key, value in metadata.items():
            frame[key] = value
        frames.append(frame)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
