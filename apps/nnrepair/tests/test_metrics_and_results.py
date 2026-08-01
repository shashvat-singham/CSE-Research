"""Tests for metric bookkeeping, F1 selection, and result-file ingest."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from nnrepair.f1_selection import (
    harmonic_mean,
    read_prec_f1,
    select_experts_by_f1,
    select_experts_by_harmonic_f1,
)
from nnrepair.metrics import ConfusionCounts, PassFailCounts, round_half_up
from nnrepair.results import describe_result_file, discover_results, load_result_csv

ARTIFACT_ROOT = Path(__file__).resolve().parents[3] / "NNRepair"
RESULTS_ROOT = ARTIFACT_ROOT / "Results"

requires_artifacts = pytest.mark.skipif(
    not RESULTS_ROOT.is_dir(), reason="NNRepair/Results not present"
)


class TestRoundHalfUp:
    def test_rounds_half_away_from_zero_like_java(self):
        """Python's built-in round() gives 0.12 here; Java's HALF_UP gives 0.13."""
        assert round_half_up(0.125, 2) == 0.13
        assert round_half_up(0.135, 2) == 0.14

    def test_nan_passes_through(self):
        assert np.isnan(round_half_up(float("nan")))

    def test_rejects_negative_places(self):
        with pytest.raises(ValueError):
            round_half_up(1.0, -1)


class TestPassFailCounts:
    def test_accuracy_is_a_percentage(self):
        counts = PassFailCounts()
        for correct in [True] * 3 + [False]:
            counts.record(correct)
        assert counts.accuracy == 75.0

    def test_empty_accuracy_is_nan(self):
        assert np.isnan(PassFailCounts().accuracy)


class TestConfusionCounts:
    def test_true_positive_requires_predicting_own_label_correctly(self):
        counts = ConfusionCounts(label=3)
        counts.record(predicted=3, correct_label=3)
        assert (counts.tp, counts.fp, counts.fn, counts.tn) == (1, 0, 0, 0)
        assert counts.targeted_pass == 1

    def test_false_negative_when_own_label_is_missed(self):
        counts = ConfusionCounts(label=3)
        counts.record(predicted=8, correct_label=3)
        assert (counts.tp, counts.fp, counts.fn, counts.tn) == (0, 0, 1, 0)
        assert counts.targeted_fail == 1

    def test_false_positive_when_claiming_someone_elses_input(self):
        counts = ConfusionCounts(label=3)
        counts.record(predicted=3, correct_label=8)
        assert (counts.tp, counts.fp, counts.fn, counts.tn) == (0, 1, 0, 0)

    def test_true_negative_when_uninvolved(self):
        counts = ConfusionCounts(label=3)
        counts.record(predicted=8, correct_label=8)  # correct, not our label
        counts.record(predicted=5, correct_label=8)  # wrong, but not our label either
        assert counts.tn == 2
        assert (counts.tp, counts.fp, counts.fn) == (0, 0, 0)

    def test_targeted_accuracy_ignores_other_labels(self):
        counts = ConfusionCounts(label=3)
        counts.record(predicted=3, correct_label=3)
        counts.record(predicted=8, correct_label=3)
        counts.record(predicted=1, correct_label=1)  # not counted in targeted
        assert counts.targeted_total == 2
        assert counts.targeted_accuracy == 50.0

    def test_precision_recall_f1(self):
        counts = ConfusionCounts(label=1, tp=6, fp=2, fn=3)
        assert counts.precision == pytest.approx(0.75)
        assert counts.recall == pytest.approx(6 / 9)
        assert counts.f1 == pytest.approx(2 * 0.75 * (6 / 9) / (0.75 + 6 / 9))

    def test_metrics_are_nan_when_never_fired(self):
        counts = ConfusionCounts(label=1)
        assert np.isnan(counts.precision)
        assert np.isnan(counts.f1)

    def test_row_uses_rounded_percentages(self):
        counts = ConfusionCounts(label=2, tp=1, fp=1, fn=0, passed=1, failed=1)
        row = counts.as_row()
        assert row["COMBINATION"] == "L2"
        assert row["PREC"] == 50.0


class TestF1Selection:
    def test_harmonic_mean(self):
        np.testing.assert_allclose(
            harmonic_mean(np.array([0.5]), np.array([0.5])), [0.5]
        )

    def test_harmonic_mean_of_zero_pair_is_zero_not_nan(self):
        assert harmonic_mean(np.array([0.0]), np.array([0.0]))[0] == 0.0

    def test_harmonic_mean_punishes_lopsided_scores(self):
        """An expert great on one set and terrible on the other scores low."""
        lopsided = harmonic_mean(np.array([0.9]), np.array([0.1]))[0]
        balanced = harmonic_mean(np.array([0.5]), np.array([0.5]))[0]
        assert lopsided < balanced

    def test_read_prec_f1_by_key(self, tmp_path):
        path = tmp_path / "s_prec_f1.csv"
        path.write_text(
            "prec=[0.1, 0.2]\n"
            "f1Experts=[0, 1]\n"
            "f1_values=[0.3, 0.4]\n"
            "f1_values_original=[0.2, 0.5]\n",
            encoding="utf-8",
        )
        record = read_prec_f1(path)
        np.testing.assert_allclose(record.prec, [0.1, 0.2])
        assert record.f1_experts == [0, 1]

    def test_read_prec_f1_tolerates_missing_keys(self, tmp_path):
        path = tmp_path / "s_prec_f1.csv"
        path.write_text("prec=[0.1]\n", encoding="utf-8")
        assert read_prec_f1(path).f1_values.size == 0

    def test_select_by_f1_keeps_improvements_only(self, tmp_path):
        path = tmp_path / "s_prec_f1.csv"
        path.write_text(
            "f1_values=[0.3, 0.4]\nf1_values_original=[0.2, 0.5]\n", encoding="utf-8"
        )
        assert select_experts_by_f1(read_prec_f1(path)) == [0]

    def test_select_by_harmonic_f1(self, tmp_path):
        adv = tmp_path / "adv_prec_f1.csv"
        adv.write_text(
            "f1_values=[0.9, 0.9]\nf1_values_original=[0.5, 0.5]\n", encoding="utf-8"
        )
        clean = tmp_path / "clean_prec_f1.csv"
        # Expert 0 holds up on clean data; expert 1 collapses.
        clean.write_text(
            "f1_values=[0.9, 0.01]\nf1_values_original=[0.5, 0.5]\n", encoding="utf-8"
        )
        selected, repaired, original = select_experts_by_harmonic_f1(
            read_prec_f1(adv), read_prec_f1(clean)
        )
        assert selected == [0]
        assert repaired[1] < original[1]


class TestResultFileNaming:
    @pytest.mark.parametrize(
        "relative,expected",
        [
            (
                "Cifar-Adversarial/Lastlayer/CIFAR_LAST_LAYER_Eps0_01_ExpA_ADV_TEST.csv",
                {"subject": "Cifar-Adversarial", "layer": "Lastlayer", "experiment": "ExpA",
                 "dataset": "ADV_TEST", "selection": "all", "is_sidecar": False},
            ),
            (
                "Cifar-Poisoned/Lastlayer/POISONED_CIFAR_LAST_LAYER_ExpB_POISONED_TEST_f1.csv",
                {"experiment": "ExpB", "dataset": "POISONED_TEST", "selection": "f1",
                 "is_sidecar": False},
            ),
            (
                "MNIST-Adversarial/IntermediateLayer/ADVERSARIAL_PATTERN_Eps0_05_ExpA_ADV_TEST_f1har_prec_f1.csv",
                {"layer": "IntermediateLayer", "selection": "f1har", "is_sidecar": True,
                 "dataset": "ADV_TEST"},
            ),
            (
                "MNIST-LowQuality/IntermediateLayer/LOW_QUALITY_PATTERN_TEST_prec_f1.csv",
                {"experiment": None, "dataset": "TEST", "selection": "all", "is_sidecar": True},
            ),
        ],
    )
    def test_metadata_is_decoded_from_the_path(self, relative, expected):
        described = describe_result_file(Path("Results") / relative, Path("Results"))
        for key, value in expected.items():
            assert getattr(described, key) == value, key

    def test_adv_training_is_not_truncated_to_training(self):
        described = describe_result_file(
            Path("R/S/L/CIFAR_ExpA_ADV_TRAINING.csv"), Path("R")
        )
        assert described.dataset == "ADV_TRAINING"

    def test_passing_tests_decode_from_experiment_id(self):
        described = describe_result_file(Path("R/S/L/X_ExpC_TEST.csv"), Path("R"))
        assert described.passing_tests == 50


@requires_artifacts
class TestAgainstShippedResults:
    def test_discovers_the_shipped_csvs(self):
        files = discover_results(RESULTS_ROOT)
        assert len(files) > 300
        assert {f.subject for f in files} >= {
            "Cifar-Adversarial", "Cifar-Poisoned",
            "MNIST-Adversarial", "MNIST-LowQuality", "MNIST-Poisoned",
        }

    def test_every_non_sidecar_result_loads(self):
        failures = []
        for result_file in discover_results(RESULTS_ROOT):
            if result_file.is_sidecar:
                continue
            try:
                frame = load_result_csv(result_file.path)
            except Exception as error:  # noqa: BLE001 - reported in bulk below
                failures.append((result_file.path.name, error))
                continue
            if frame.empty:
                failures.append((result_file.path.name, "empty"))
        assert not failures, f"{len(failures)} result files failed: {failures[:5]}"

    def test_loaded_rows_are_classified(self):
        path = next(RESULTS_ROOT.rglob("*_ADV_TEST.csv"))
        frame = load_result_csv(path)
        assert set(frame["ROW_KIND"]) <= {"combination", "expert", "original"}

        # PREC and PVC are blank in runs with no training precision, so
        # accuracy is legitimately NaN on those rows; the rest are percentages.
        accuracy = frame.loc[frame["ROW_KIND"] == "combination", "ACCURACY"].dropna()
        assert not accuracy.empty
        assert accuracy.between(0, 100).all()

    def test_every_shipped_sidecar_parses(self):
        sidecars = [f for f in discover_results(RESULTS_ROOT) if f.is_sidecar]
        assert sidecars
        for sidecar in sidecars:
            read_prec_f1(sidecar.path)
