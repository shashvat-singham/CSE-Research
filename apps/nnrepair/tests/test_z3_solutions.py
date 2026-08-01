"""Tests for Z3 model parsing, including against the shipped solution files."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from nnrepair.z3_solutions import (
    LayerNotRepairableError,
    LayerNotSupportedError,
    load_deltas_intermediate_layer,
    load_deltas_last_layer,
    load_repaired_weights_cifar10,
    load_repaired_weights_mnist0,
    parse_z3_model,
)

ARTIFACT_ROOT = Path(__file__).resolve().parents[3] / "NNRepair"
Z3_SOLUTIONS = ARTIFACT_ROOT / "Z3Solutions"

requires_artifacts = pytest.mark.skipif(
    not Z3_SOLUTIONS.is_dir(), reason="NNRepair/Z3Solutions not present"
)


def write_model(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(f"sat\n(model \n{body}\n)\n", encoding="utf-8")
    return path


class TestParseZ3Model:
    def test_plain_decimal(self, tmp_path):
        path = write_model(tmp_path, "m.txt", "  (define-fun sym1 () Real\n    0.5)")
        assert parse_z3_model(path) == {"sym1": 0.5}

    def test_rational(self, tmp_path):
        path = write_model(tmp_path, "m.txt", "  (define-fun sym1 () Real\n    (/ 1.0 4.0))")
        assert parse_z3_model(path) == {"sym1": 0.25}

    def test_negated_rational(self, tmp_path):
        path = write_model(
            tmp_path, "m.txt", "  (define-fun sym1 () Real\n    (- (/ 3.0 4.0)))"
        )
        assert parse_z3_model(path) == {"sym1": -0.75}

    def test_rational_wrapped_across_lines(self, tmp_path):
        """The layout that defeated the Java's dot-counting heuristic."""
        path = write_model(
            tmp_path,
            "m.txt",
            "  (define-fun sym124_77 () Real\n"
            "    (- (/ 31846372968901674513178938196695296413998307233287.0\n"
            "      40833421639270264105187176303690000000000000000000.0)))",
        )
        assert parse_z3_model(path)["sym124_77"] == pytest.approx(-0.7799094881207413)

    def test_big_rational_keeps_precision(self, tmp_path):
        """Exact rational arithmetic before the single narrowing to float."""
        path = write_model(
            tmp_path,
            "m.txt",
            "  (define-fun sym1 () Real\n"
            "    (/ 5162714909122858188565007232753.0 13572855171074818750000000000000.0))",
        )
        assert parse_z3_model(path)["sym1"] == pytest.approx(0.3803705885055892, abs=1e-16)

    def test_unsat_is_rejected(self, tmp_path):
        path = tmp_path / "u.txt"
        path.write_text("unsat\n", encoding="utf-8")
        with pytest.raises(ValueError, match="satisfiable"):
            parse_z3_model(path)

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            parse_z3_model(tmp_path / "nope.txt")


class TestDeltaLoading:
    def test_last_layer_names_yield_input_index_only(self, tmp_path):
        write_model(
            tmp_path,
            "solution3.txt",
            "  (define-fun sym42 () Real\n    0.25)\n"
            "  (define-fun y3_1 () Real\n    9.0)",
        )
        deltas = load_deltas_last_layer(tmp_path, "solution", 3)
        assert len(deltas) == 1, "y variables are solver scratch and must be ignored"
        assert (deltas[0].out_index, deltas[0].in_index, deltas[0].value) == (None, 42, 0.25)

    def test_intermediate_names_yield_both_indices(self, tmp_path):
        write_model(tmp_path, "label3.txt", "  (define-fun sym124_77 () Real\n    0.5)")
        deltas = load_deltas_intermediate_layer(tmp_path, 3)
        assert (deltas[0].out_index, deltas[0].in_index) == (124, 77)

    def test_full_repair_reads_full_txt(self, tmp_path):
        write_model(tmp_path, "full.txt", "  (define-fun sym1 () Real\n    1.0)")
        assert load_deltas_last_layer(tmp_path, "solution", 10, number_of_experts=10)


class TestWeightAssembly:
    def _write_expert_solutions(self, tmp_path):
        for expert in range(10):
            write_model(
                tmp_path, f"solution{expert}.txt", f"  (define-fun sym{expert} () Real\n    1.0)"
            )

    def test_mnist_last_layer_shape_and_placement(self, tmp_path):
        self._write_expert_solutions(tmp_path)
        deltas = load_repaired_weights_mnist0(tmp_path, "solution", 8, range(10))
        assert deltas.shape == (12, 128, 10)
        # Expert k's delta lands on its own output column.
        assert deltas[3, 3, 3] == 1.0
        assert deltas[3, 3, 4] == 0.0

    def test_average_slot_is_the_mean_of_experts(self, tmp_path):
        self._write_expert_solutions(tmp_path)
        deltas = load_repaired_weights_mnist0(tmp_path, "solution", 8, range(10))
        np.testing.assert_allclose(deltas[11], deltas[:10].mean(axis=0))

    def test_cifar_last_layer_shape(self, tmp_path):
        self._write_expert_solutions(tmp_path)
        deltas = load_repaired_weights_cifar10(tmp_path, "solution", 13, range(10))
        assert deltas.shape == (12, 512, 10)

    def test_unimplemented_layers_are_flagged_distinctly(self, tmp_path):
        with pytest.raises(LayerNotSupportedError):
            load_repaired_weights_mnist0(tmp_path, "solution", 0, [])
        with pytest.raises(LayerNotRepairableError):
            load_repaired_weights_mnist0(tmp_path, "solution", 7, [])


@requires_artifacts
class TestAgainstShippedArtifacts:
    def test_every_shipped_solution_parses(self):
        files = sorted(Z3_SOLUTIONS.rglob("*.txt"))
        assert files, "expected solution files under Z3Solutions"
        for path in files:
            bindings = parse_z3_model(path)
            assert bindings, f"{path} produced no bindings"

    def test_last_layer_solutions_are_mostly_sparse(self):
        """A repair adjusts a handful of weights, not the whole layer."""
        path = next(Z3_SOLUTIONS.glob("*/Lastlayer/*/solution0.txt"))
        bindings = parse_z3_model(path)
        syms = {k: v for k, v in bindings.items() if k.startswith("sym")}
        assert syms
        assert sum(1 for v in syms.values() if v != 0.0) < len(syms)

    def test_values_are_finite(self):
        path = next(Z3_SOLUTIONS.glob("*/IntermediateLayer/*/label0.txt"))
        assert all(np.isfinite(v) for v in parse_z3_model(path).values())
