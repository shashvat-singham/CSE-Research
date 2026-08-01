"""Expert combination strategies.

Python port of ``CombinationCode/module4_combination/ExpertCombination.java``.

NNRepair repairs a classifier by producing one *expert* per label: expert ``k``
is the network with weight deltas that were solved for label ``k``. At
inference time every expert scores the input, and these strategies decide which
single label the ensemble commits to.

An expert "claims" an input when its own argmax equals its own label — expert 3
claiming means "I, the specialist for 3s, think this is a 3". The strategies
differ only in how they break ties between multiple simultaneous claims.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum

import numpy as np

__all__ = [
    "CombinationMethod",
    "select_label_with_max_confidence",
    "collect_expert_claims",
    "combine_by_naive",
    "combine_by_precision",
    "combine_by_votes",
    "combine_by_confidence",
    "combine_by_pvc",
    "combine_experts",
]

#: Slot holding the *full* repair (all labels repaired in one solver call).
FULL_REPAIR_SLOT = 10
#: Slot holding the element-wise average of the per-expert weight deltas.
AVERAGE_REPAIR_SLOT = 11
#: Slot holding the unrepaired network's output.
ORIGINAL_SLOT = -1


class CombinationMethod(str, Enum):
    """Supported expert-combination methods.

    Mirrors ``ExpertCombination.COMBINATION_METHOD``. Inherits from ``str`` so
    values render as plain names in CSV output and Streamlit widgets, matching
    the Java ``enum.toString()`` used by the original result files.
    """

    NAIVE = "NAIVE"
    AVERAGE = "AVERAGE"
    FULL = "FULL"
    PREC = "PREC"
    CONF = "CONF"
    VOTES = "VOTES"
    PVC = "PVC"
    ORIG = "ORIG"
    ALL = "ALL"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value

    @classmethod
    def selectable(cls) -> list["CombinationMethod"]:
        """Every method except the ``ALL`` meta-selector."""
        return [m for m in cls if m is not cls.ALL]


def select_label_with_max_confidence(values: Sequence[float] | np.ndarray) -> int:
    """Return the index of the highest score.

    Ties go to the lowest index, matching the Java loop's strict ``>``
    comparison and ``np.argmax``'s first-max rule.
    """
    return int(np.argmax(np.asarray(values, dtype=np.float64)))


def collect_expert_claims(
    expert_ids: Sequence[int],
    result: Mapping[int, np.ndarray],
) -> list[int]:
    """Return the experts whose argmax is their own label.

    Preserves the order of ``expert_ids``, because several tie-breaks below
    fall back to "the first claim" and the Java code relies on that ordering.
    """
    return [
        expert_id
        for expert_id in expert_ids
        if select_label_with_max_confidence(result[expert_id]) == expert_id
    ]


def combine_by_naive(expert_claims: Sequence[int], orig_label: int) -> int:
    """NAIVE: accept a claim only when exactly one expert makes it.

    Any disagreement — zero claims or several — defers to the original network.
    """
    if len(expert_claims) == 1:
        return expert_claims[0]
    return orig_label


def combine_by_precision(
    expert_claims: Sequence[int],
    orig_label: int,
    train_precision: Sequence[float] | np.ndarray,
) -> int:
    """PREC: among claimants, trust the one most precise on training data."""
    if not expert_claims:
        return orig_label
    if len(expert_claims) == 1:
        return expert_claims[0]

    max_expert_id = expert_claims[0]
    max_precision = train_precision[max_expert_id]
    for expert_id in expert_claims:
        if train_precision[expert_id] > max_precision:
            max_precision = train_precision[expert_id]
            max_expert_id = expert_id
    return max_expert_id


def combine_by_votes(
    result: Mapping[int, np.ndarray],
    expert_claims: Sequence[int],
    orig_label: int,
    expert_ids: Sequence[int],
    number_of_final_labels: int,
) -> int:
    """VOTES: among claimants, pick whichever collected most votes.

    Every expert votes for its own argmax — including experts that did not
    claim — so a claimant wins by being corroborated from the outside.
    """
    if not expert_claims:
        return orig_label
    if len(expert_claims) == 1:
        return expert_claims[0]

    votes = np.zeros(number_of_final_labels, dtype=np.int64)
    for expert_id in expert_ids:
        votes[select_label_with_max_confidence(result[expert_id])] += 1

    max_voted_expert_id = expert_claims[0]
    for expert_id in expert_claims:
        if votes[expert_id] > votes[max_voted_expert_id]:
            max_voted_expert_id = expert_id
    return max_voted_expert_id


def combine_by_confidence(
    result: Mapping[int, np.ndarray],
    expert_claims: Sequence[int],
    orig_label: int,
) -> int:
    """CONF: among claimants, pick the one most confident in its own label."""
    if not expert_claims:
        return orig_label
    if len(expert_claims) == 1:
        return expert_claims[0]

    highest_id = expert_claims[0]
    highest_value = result[highest_id][highest_id]
    for expert_id in expert_claims:
        confidence = result[expert_id][expert_id]
        if confidence > highest_value:
            highest_value = confidence
            highest_id = expert_id
    return highest_id


def combine_by_pvc(
    result: Mapping[int, np.ndarray],
    expert_claims: Sequence[int],
    orig_label: int,
    train_precision: Sequence[float] | np.ndarray,
    expert_ids: Sequence[int],
    number_of_final_labels: int,
) -> int:
    """PVC: majority vote over the PREC, VOTES and CONF verdicts."""
    if not expert_claims:
        return orig_label
    if len(expert_claims) == 1:
        return expert_claims[0]

    score_per_expert: dict[int, int] = {expert_id: 0 for expert_id in expert_claims}

    for verdict in (
        combine_by_precision(expert_claims, orig_label, train_precision),
        combine_by_votes(result, expert_claims, orig_label, expert_ids, number_of_final_labels),
        combine_by_confidence(result, expert_claims, orig_label),
    ):
        score_per_expert[verdict] = score_per_expert.get(verdict, 0) + 1

    # Java iterates a HashMap and keeps the first strict maximum. Iterating in
    # claim order is deterministic and agrees whenever there is a unique
    # winner, which a 3-way vote over <=3 candidates guarantees unless all
    # three verdicts differ — in which case Java's own answer was
    # hash-order-dependent and any claimant is equally defensible.
    max_score = -1
    max_score_expert = -1
    for expert_id, score in score_per_expert.items():
        if score > max_score:
            max_score = score
            max_score_expert = expert_id
    return max_score_expert


def combine_experts(
    comb_method: CombinationMethod,
    result: Mapping[int, np.ndarray],
    orig_label: int,
    train_precision: Sequence[float] | np.ndarray,
    expert_ids: Sequence[int],
    optimized: bool,
    number_of_final_labels: int,
) -> dict[CombinationMethod, int]:
    """Apply one combination method, or all of them when given ``ALL``.

    Args:
        comb_method: A single method, or ``ALL`` to evaluate every method.
        result: Scores per slot — expert ids, plus ``ORIGINAL_SLOT`` and (when
            not ``optimized``) ``FULL_REPAIR_SLOT`` / ``AVERAGE_REPAIR_SLOT``.
        orig_label: Label chosen by the unrepaired network.
        train_precision: Per-expert training precision. Empty disables the
            precision-dependent methods (PREC, PVC), as in the Java original.
        expert_ids: Experts participating in this run.
        optimized: Skip the FULL and AVERAGE slots, which the optimized
            pipeline does not compute.
        number_of_final_labels: Output-layer width.

    Returns:
        The label chosen by each evaluated method.
    """
    combined: dict[CombinationMethod, int] = {}
    wants_all = comb_method is CombinationMethod.ALL

    def wants(method: CombinationMethod) -> bool:
        return wants_all or comb_method is method

    if wants(CombinationMethod.ORIG):
        combined[CombinationMethod.ORIG] = orig_label

    expert_claims = collect_expert_claims(expert_ids, result)

    if not optimized:
        if wants(CombinationMethod.AVERAGE):
            combined[CombinationMethod.AVERAGE] = select_label_with_max_confidence(
                result[AVERAGE_REPAIR_SLOT]
            )
        if wants(CombinationMethod.FULL):
            combined[CombinationMethod.FULL] = select_label_with_max_confidence(
                result[FULL_REPAIR_SLOT]
            )

    if wants(CombinationMethod.NAIVE):
        combined[CombinationMethod.NAIVE] = combine_by_naive(expert_claims, orig_label)

    if wants(CombinationMethod.PREC) and len(train_precision) > 0:
        combined[CombinationMethod.PREC] = combine_by_precision(
            expert_claims, orig_label, train_precision
        )

    if wants(CombinationMethod.CONF):
        combined[CombinationMethod.CONF] = combine_by_confidence(
            result, expert_claims, orig_label
        )

    if wants(CombinationMethod.VOTES):
        combined[CombinationMethod.VOTES] = combine_by_votes(
            result, expert_claims, orig_label, expert_ids, number_of_final_labels
        )

    if wants(CombinationMethod.PVC) and len(train_precision) > 0:
        combined[CombinationMethod.PVC] = combine_by_pvc(
            result, expert_claims, orig_label, train_precision, expert_ids,
            number_of_final_labels,
        )

    return combined
