"""Tests for the expert-combination strategies."""

from __future__ import annotations

import numpy as np
import pytest

from nnrepair.combination import (
    AVERAGE_REPAIR_SLOT,
    FULL_REPAIR_SLOT,
    ORIGINAL_SLOT,
    CombinationMethod,
    collect_expert_claims,
    combine_by_confidence,
    combine_by_naive,
    combine_by_precision,
    combine_by_pvc,
    combine_by_votes,
    combine_experts,
    select_label_with_max_confidence,
)

EXPERT_IDS = list(range(10))


def scores(**overrides: float) -> np.ndarray:
    """Build a 10-way score vector, zero except where overridden."""
    values = np.zeros(10)
    for key, value in overrides.items():
        values[int(key.lstrip("l"))] = value
    return values


def test_select_label_with_max_confidence_breaks_ties_to_lowest_index():
    """Java's strict `>` keeps the first maximum; argmax must agree."""
    assert select_label_with_max_confidence([5.0, 5.0, 1.0]) == 0


def test_collect_expert_claims_keeps_only_self_votes():
    result = {
        0: scores(l0=9.0),   # claims
        1: scores(l4=9.0),   # votes for 4, does not claim
        2: scores(l2=3.0),   # claims
    }
    assert collect_expert_claims([0, 1, 2], result) == [0, 2]


def test_collect_expert_claims_preserves_input_order():
    result = {i: scores(**{f"l{i}": 1.0}) for i in range(4)}
    assert collect_expert_claims([3, 1, 2, 0], result) == [3, 1, 2, 0]


class TestNaive:
    def test_single_claim_wins(self):
        assert combine_by_naive([7], orig_label=2) == 7

    def test_no_claim_defers_to_original(self):
        assert combine_by_naive([], orig_label=2) == 2

    def test_multiple_claims_defer_to_original(self):
        assert combine_by_naive([3, 7], orig_label=2) == 2


class TestPrecision:
    def test_picks_most_precise_claimant(self):
        precision = np.zeros(10)
        precision[3] = 0.5
        precision[7] = 0.9
        assert combine_by_precision([3, 7], orig_label=2, train_precision=precision) == 7

    def test_ties_keep_the_first_claimant(self):
        precision = np.full(10, 0.5)
        assert combine_by_precision([3, 7], orig_label=2, train_precision=precision) == 3

    def test_empty_claims_defer_to_original(self):
        assert combine_by_precision([], orig_label=2, train_precision=np.zeros(10)) == 2


class TestVotes:
    def test_claimant_with_most_outside_votes_wins(self):
        # Experts 3 and 7 both claim; experts 0,1,2 all vote for 7.
        result = {i: scores(l7=9.0) for i in EXPERT_IDS}
        result[3] = scores(l3=9.0)
        result[7] = scores(l7=9.0)
        assert combine_by_votes(result, [3, 7], 2, EXPERT_IDS, 10) == 7

    def test_single_claim_short_circuits(self):
        result = {i: scores(l0=1.0) for i in EXPERT_IDS}
        assert combine_by_votes(result, [5], 2, EXPERT_IDS, 10) == 5


class TestConfidence:
    def test_most_self_confident_claimant_wins(self):
        result = {i: scores() for i in EXPERT_IDS}
        result[3] = scores(l3=2.0)
        result[7] = scores(l7=8.0)
        assert combine_by_confidence(result, [3, 7], orig_label=2) == 7

    def test_empty_claims_defer_to_original(self):
        assert combine_by_confidence({}, [], orig_label=4) == 4


class TestPVC:
    def test_majority_of_three_verdicts_wins(self):
        """PREC and CONF both say 7, VOTES says 3, so 7 takes it."""
        result = {i: scores(l3=9.0) for i in EXPERT_IDS}  # everyone votes 3
        result[3] = scores(l3=1.0)
        result[7] = scores(l7=8.0)                        # 7 is most confident
        precision = np.zeros(10)
        precision[7] = 0.99                               # 7 is most precise
        assert combine_by_pvc(result, [3, 7], 2, precision, EXPERT_IDS, 10) == 7

    def test_single_claim_short_circuits(self):
        assert combine_by_pvc({}, [5], 2, np.zeros(10), EXPERT_IDS, 10) == 5


class TestCombineExperts:
    @pytest.fixture
    def result(self):
        # Every non-claiming expert must point somewhere other than itself.
        # An all-zero vector would argmax to 0, making expert 0 a claimant by
        # tie-break and turning this into a two-claim case.
        values = {i: scores(l9=1.0) for i in EXPERT_IDS}
        values[9] = scores(l0=1.0)
        values[4] = scores(l4=9.0)  # the sole claimant
        values[ORIGINAL_SLOT] = scores(l1=5.0)
        values[FULL_REPAIR_SLOT] = scores(l6=5.0)
        values[AVERAGE_REPAIR_SLOT] = scores(l8=5.0)
        return values

    def test_fixture_has_exactly_one_claimant(self, result):
        assert collect_expert_claims(EXPERT_IDS, result) == [4]

    def test_all_evaluates_every_method(self, result):
        combined = combine_experts(
            CombinationMethod.ALL, result, 1, np.zeros(10), EXPERT_IDS, False, 10
        )
        assert set(combined) == set(CombinationMethod.selectable())

    def test_all_reads_the_full_and_average_slots(self, result):
        combined = combine_experts(
            CombinationMethod.ALL, result, 1, np.zeros(10), EXPERT_IDS, False, 10
        )
        assert combined[CombinationMethod.FULL] == 6
        assert combined[CombinationMethod.AVERAGE] == 8
        assert combined[CombinationMethod.ORIG] == 1
        assert combined[CombinationMethod.NAIVE] == 4

    def test_optimized_skips_full_and_average(self, result):
        combined = combine_experts(
            CombinationMethod.ALL, result, 1, np.zeros(10), EXPERT_IDS, True, 10
        )
        assert CombinationMethod.FULL not in combined
        assert CombinationMethod.AVERAGE not in combined

    def test_empty_train_precision_disables_prec_and_pvc(self, result):
        """Matches the Java's `trainPrecision.length > 0` guard."""
        combined = combine_experts(
            CombinationMethod.ALL, result, 1, np.array([]), EXPERT_IDS, False, 10
        )
        assert CombinationMethod.PREC not in combined
        assert CombinationMethod.PVC not in combined

    def test_single_method_returns_only_that_method(self, result):
        combined = combine_experts(
            CombinationMethod.NAIVE, result, 1, np.zeros(10), EXPERT_IDS, False, 10
        )
        assert set(combined) == {CombinationMethod.NAIVE}


def test_method_renders_as_bare_name_for_csv():
    """Result CSVs contain `NAIVE`, not `CombinationMethod.NAIVE`."""
    assert f"{CombinationMethod.NAIVE}" == "NAIVE"
    assert CombinationMethod.ALL not in CombinationMethod.selectable()
