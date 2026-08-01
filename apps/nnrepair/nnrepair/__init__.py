"""NNRepair — constraint-based repair of neural network classifiers.

A Python port of the Java artifact under ``NNRepair/CombinationCode``, plus
loaders for the shipped experiment results.

The pipeline the paper describes, and what each module covers:

============================  ==================================================
Module                        Role
============================  ==================================================
:mod:`.z3_solutions`          Parse solver output into weight-delta tensors.
:mod:`.models`                Run the original and repaired networks.
:mod:`.combination`           Decide a label from the experts' verdicts.
:mod:`.metrics`               Score those decisions.
:mod:`.f1_selection`          Drop experts that make their label worse.
:mod:`.experiments`           Drive the above over a dataset.
:mod:`.results`               Read the 345 result CSVs already in the repo.
============================  ==================================================

Only :mod:`.results` is needed to browse existing results; the rest require
the large weight dumps under ``NN-Code``, which are not distributed with the
deployed app.
"""

from __future__ import annotations

__version__ = "1.0.0"

from .combination import (
    AVERAGE_REPAIR_SLOT,
    FULL_REPAIR_SLOT,
    ORIGINAL_SLOT,
    CombinationMethod,
    combine_experts,
    select_label_with_max_confidence,
)
from .f1_selection import (
    PrecF1Record,
    read_prec_f1,
    select_experts_by_f1,
    select_experts_by_harmonic_f1,
)
from .metrics import ConfusionCounts, PassFailCounts, round_half_up
from .results import discover_results, load_result_csv, load_results_index
from .z3_solutions import (
    load_repaired_weights_cifar10,
    load_repaired_weights_mnist0,
    parse_z3_model,
)

__all__ = [
    "__version__",
    "AVERAGE_REPAIR_SLOT",
    "FULL_REPAIR_SLOT",
    "ORIGINAL_SLOT",
    "CombinationMethod",
    "ConfusionCounts",
    "PassFailCounts",
    "PrecF1Record",
    "combine_experts",
    "discover_results",
    "load_repaired_weights_cifar10",
    "load_repaired_weights_mnist0",
    "load_result_csv",
    "load_results_index",
    "parse_z3_model",
    "read_prec_f1",
    "round_half_up",
    "select_experts_by_f1",
    "select_experts_by_harmonic_f1",
    "select_label_with_max_confidence",
]
