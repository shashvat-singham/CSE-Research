"""Locating and caching the artifact data the pages read.

The deployed bundle carries only the result CSVs (1.5 MB). The Z3 solutions
(14 MB) and weight dumps (954 MB) are optional: pages that need them check
availability first and explain what is missing rather than raising.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from nnrepair.results import discover_results, load_results_index

APP_ROOT = Path(__file__).resolve().parent

#: Result CSVs, bundled with the app.
RESULTS_ROOT = APP_ROOT / "data" / "Results"

#: Trimmed artifact subset shipped with the deployed app — the Z3 solutions in
#: full, plus the MNIST0 weights and a slice of one FGSM test set. Enough for
#: every page to work; the remaining ~940 MB of datasets stays out.
BUNDLED_ARTIFACT_ROOT = APP_ROOT / "data" / "NNRepair"


def _looks_like_artifact_tree(path: Path) -> bool:
    """Whether ``path`` is really the artifact tree and not a lookalike.

    Checking the directory name alone is not enough. On a case-insensitive
    filesystem — Windows, and macOS by default — a candidate named
    ``NNRepair`` also matches this app's own lowercase ``nnrepair`` Python
    package, so the search would happily "find" the source tree. Requiring one
    of the artifact's actual subdirectories rules that out.
    """
    return path.is_dir() and any(
        (path / marker).is_dir() for marker in ("Z3Solutions", "NN-Code", "Constraints", "Results")
    )


def _locate_artifact_root() -> Path:
    """Find the optional ``NNRepair`` artifact tree.

    Three deployments, three layouts:

    * **Docker** — the artifacts are bind-mounted, and
      ``NNREPAIR_ARTIFACT_ROOT`` says where.
    * **Monorepo checkout** — the app lives at ``apps/nnrepair``, so the
      artifacts are two levels up.
    * **Standalone repo** — the app is the repository root and the artifacts
      are simply absent.

    Returns:
        The first candidate that holds a recognisable artifact tree, or the
        monorepo path as a non-existent default so callers still have a
        sensible path to name when reporting the absence.
    """
    override = os.environ.get("NNREPAIR_ARTIFACT_ROOT")
    if override:
        return Path(override)

    monorepo = (
        APP_ROOT.parents[1] / "NNRepair" if len(APP_ROOT.parents) > 1 else APP_ROOT / "NNRepair"
    )

    # The full checkout wins when present — it has every subject and the
    # complete datasets. The bundled copy under data/ is the trimmed subset
    # shipped with the deployed app.
    for candidate in (monorepo, BUNDLED_ARTIFACT_ROOT, APP_ROOT / "NNRepair"):
        if _looks_like_artifact_tree(candidate):
            return candidate

    return monorepo


#: Optional artifacts, present only in a full checkout or a Docker mount.
ARTIFACT_ROOT = _locate_artifact_root()
REPO_ROOT = ARTIFACT_ROOT.parent
Z3_ROOT = ARTIFACT_ROOT / "Z3Solutions"
CONSTRAINTS_ROOT = ARTIFACT_ROOT / "Constraints"
NN_CODE_ROOT = ARTIFACT_ROOT / "NN-Code"

SUBJECT_BLURBS = {
    "MNIST-LowQuality": "An MNIST model trained to low accuracy — the baseline "
    "case where the network is simply weak rather than attacked.",
    "MNIST-Poisoned": "An MNIST model with a backdoor trigger planted during "
    "training; it misclassifies whenever the trigger pattern is present.",
    "MNIST-Adversarial": "An MNIST model evaluated under FGSM perturbations at "
    "several epsilon values.",
    "Cifar-Poisoned": "A CIFAR-10 model carrying a training-time backdoor.",
    "Cifar-Adversarial": "A CIFAR-10 model evaluated under FGSM perturbations.",
}

METHOD_BLURBS = {
    "ORIG": "The unrepaired network — the baseline every other row is judged against.",
    "NAIVE": "Accept an expert only when exactly one claims the input.",
    "AVERAGE": "One network using the element-wise mean of all experts' deltas.",
    "FULL": "One network repaired for every label in a single solver call.",
    "PREC": "Among claimants, trust the one most precise on training data.",
    "CONF": "Among claimants, trust the one most confident in its own label.",
    "VOTES": "Among claimants, trust the one the other experts corroborate.",
    "PVC": "Majority vote over the PREC, VOTES and CONF verdicts.",
}


@st.cache_data(show_spinner="Reading result files…")
def results_index() -> pd.DataFrame:
    """Every result row across all subjects, with filename metadata attached."""
    return load_results_index(str(RESULTS_ROOT))


@st.cache_data(show_spinner=False)
def result_files() -> pd.DataFrame:
    """One row per result file, for the file browser."""
    rows = []
    for described in discover_results(RESULTS_ROOT):
        rows.append(
            {
                "subject": described.subject,
                "layer": described.layer,
                "experiment": described.experiment,
                "passing_tests": described.passing_tests,
                "dataset": described.dataset,
                "epsilon": described.epsilon,
                "selection": described.selection,
                "kind": "sidecar" if described.is_sidecar else "result",
                "file": described.stem,
                "path": str(described.path),
            }
        )
    return pd.DataFrame(rows)


def have_z3_solutions() -> bool:
    """Whether the 14 MB solver-output tree is present."""
    return Z3_ROOT.is_dir()


def have_weights() -> bool:
    """Whether any extracted weight dump is present."""
    return NN_CODE_ROOT.is_dir() and any(NN_CODE_ROOT.glob("*/params/weights0.txt"))


def using_bundled_subset() -> bool:
    """Whether the artifacts in use are the trimmed copy shipped with the app.

    True on the hosted deployment, false in a full checkout. Pages use this to
    say plainly that they are showing a subset rather than letting a visitor
    assume the missing subjects and inputs simply do not exist.
    """
    try:
        return ARTIFACT_ROOT.resolve() == BUNDLED_ARTIFACT_ROOT.resolve()
    except OSError:
        return False


def bundled_subset_note() -> None:
    """State what the shipped subset contains, when running on it."""
    if not using_bundled_subset():
        return
    st.caption(
        "Running on the artifact subset bundled with this deployment: all 290 "
        "Z3 solutions, the MNIST0 adversarial weights, and the first 1,000 "
        "inputs of the FGSM ε=0.05 test set. The remaining ~940 MB of datasets "
        "and the CIFAR weights are not hosted — clone the repository for those."
    )


def missing_artifact_note(what: str, path: Path) -> None:
    """Explain an optional artifact's absence instead of failing."""
    st.info(
        f"**{what} not available in this deployment.**\n\n"
        f"This page needs `{path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path}`, "
        "which is excluded from the hosted bundle because of its size. "
        "Clone the repository and run the app locally to use this page."
    )


def selection_label(selection: str) -> str:
    """Human-readable name for an expert-selection mode."""
    return {
        "all": "All 10 experts",
        "f1": "F1-selected experts",
        "f1har": "Harmonic-F1-selected experts",
    }.get(selection, selection)
