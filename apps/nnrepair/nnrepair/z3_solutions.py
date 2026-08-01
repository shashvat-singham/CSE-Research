"""Parsing of Z3 model output into weight-delta tensors.

Python port of ``CombinationCode/module4_combination/Z3SolutionParsing.java``.

The solver emits an SMT-LIB model per repaired label::

    sat
    (model
      (define-fun sym302 () Real
        0.0)
      (define-fun sym223 () Real
        (/ 5162714909122858188565007232753.0 13572855171074818750000000000000.0))
      (define-fun y9_9 () Real
        (- (/ 175375542468231.0 5000000000000.0)))
      ...

``sym`` variables carry the weight deltas we want. Last-layer models name them
``sym<input_index>``; intermediate-layer models name them
``sym<output_index>_<input_index>``. ``y`` variables are solver scratch and are
ignored.

The Java original walked this format line-by-line, counting ``.`` characters to
guess whether a rational had spilled onto a second line. That heuristic breaks
on any reformatting of the solver output — and the intermediate-layer files in
this repository *do* wrap long rationals across lines. This port tokenises the
s-expressions properly instead, which is format-independent and yields the same
numbers. Rationals are evaluated exactly via :class:`~fractions.Fraction`
before the single narrowing conversion to float, so the hundred-digit integers
Z3 emits do not lose precision the way ``a/b`` on two pre-rounded floats does.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np

__all__ = [
    "Delta",
    "parse_z3_model",
    "load_deltas_last_layer",
    "load_deltas_intermediate_layer",
    "load_repaired_weights_mnist0",
    "load_repaired_weights_cifar10",
    "LayerNotRepairableError",
    "LayerNotSupportedError",
    "SolutionShapeMismatchError",
]

_TOKEN_RE = re.compile(r"\(|\)|[^\s()]+")
_SYM_LAST_RE = re.compile(r"^sym(\d+)$")
_SYM_INTER_RE = re.compile(r"^sym(\d+)_(\d+)$")


class LayerNotSupportedError(NotImplementedError):
    """A layer the original artifact never implemented a loader for."""


class LayerNotRepairableError(ValueError):
    """A layer that holds no weights, so it cannot carry a repair delta."""


class SolutionShapeMismatchError(ValueError):
    """Solver output does not fit the layer it is being applied to.

    Almost always means solutions from one architecture are being applied to
    another — CIFAR's final layer is 512 wide against MNIST0's 128, so a CIFAR
    solution indexes far past the end of an MNIST0 tensor.
    """


def _place(
    weight_delta: np.ndarray,
    slot: int,
    row: int,
    column: int,
    value: float,
    *,
    source: Path,
) -> None:
    """Write one delta, reporting an out-of-range index in useful terms.

    Raises:
        SolutionShapeMismatchError: If the index falls outside the tensor.
    """
    _, rows, columns = weight_delta.shape
    if not (0 <= row < rows and 0 <= column < columns):
        raise SolutionShapeMismatchError(
            f"{source.name} references weight [{row}, {column}], but the layer "
            f"being repaired is {rows}x{columns}. These solutions were solved "
            f"for a different network — check that the solution directory "
            f"({source.parent}) matches the weights and layer you selected."
        )
    weight_delta[slot, row, column] = value


@dataclass(frozen=True)
class Delta:
    """One solved weight delta.

    Attributes:
        out_index: Output-neuron index. For last-layer models the solver does
            not name it (there is one model per label), so it is ``None``.
        in_index: Index of the incoming weight being adjusted.
        value: The delta to add to the original weight.
    """

    out_index: int | None
    in_index: int
    value: float


def _parse_sexpr(tokens: Sequence[str], start: int) -> tuple[object, int]:
    """Parse one s-expression, returning it and the index just past it.

    Iterative over siblings and recursive over nesting depth. Z3 models are
    flat lists of shallow terms, so depth stays in single digits.
    """
    if start >= len(tokens):
        raise ValueError("Unexpected end of Z3 model")

    token = tokens[start]
    if token != "(":
        return token, start + 1

    items: list[object] = []
    index = start + 1
    while index < len(tokens) and tokens[index] != ")":
        item, index = _parse_sexpr(tokens, index)
        items.append(item)
    if index >= len(tokens):
        raise ValueError("Unbalanced parentheses in Z3 model")
    return items, index + 1


def _eval_numeric(node: object) -> Fraction:
    """Evaluate an SMT-LIB numeric term to an exact rational.

    Handles the three shapes Z3 produces for ``Real`` values: a decimal
    literal, ``(/ numerator denominator)``, and ``(- x)``.
    """
    if isinstance(node, str):
        return Fraction(node)

    if isinstance(node, list) and node:
        op = node[0]
        if op == "-":
            if len(node) == 2:
                return -_eval_numeric(node[1])
            # n-ary subtraction, for completeness.
            total = _eval_numeric(node[1])
            for operand in node[2:]:
                total -= _eval_numeric(operand)
            return total
        if op == "/":
            numerator = _eval_numeric(node[1])
            denominator = _eval_numeric(node[2])
            if denominator == 0:
                raise ValueError("Z3 model contains a division by zero")
            return numerator / denominator
        if op == "+":
            return sum((_eval_numeric(x) for x in node[1:]), Fraction(0))
        if op == "*":
            product = Fraction(1)
            for operand in node[1:]:
                product *= _eval_numeric(operand)
            return product
        if len(node) == 1:
            return _eval_numeric(node[0])

    raise ValueError(f"Unsupported numeric term in Z3 model: {node!r}")


def parse_z3_model(path: str | Path) -> dict[str, float]:
    """Read a Z3 solution file and return every ``define-fun`` binding.

    Args:
        path: Path to a solver output file beginning with ``sat``.

    Returns:
        Variable name to value, in file order.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If the file is not a satisfiable model.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")

    stripped = text.lstrip()
    if stripped.startswith("unsat") or stripped.startswith("unknown"):
        raise ValueError(f"{path} does not contain a satisfiable model")

    model_start = text.find("(model")
    if model_start == -1:
        raise ValueError(f"{path} contains no (model ...) block")

    tokens = _TOKEN_RE.findall(text[model_start:])
    model, _ = _parse_sexpr(tokens, 0)
    if not isinstance(model, list):
        raise ValueError(f"{path} contains a malformed (model ...) block")

    bindings: dict[str, float] = {}
    for form in model:
        # (define-fun NAME () Real VALUE)
        if (
            isinstance(form, list)
            and len(form) >= 5
            and form[0] == "define-fun"
            and isinstance(form[1], str)
        ):
            bindings[form[1]] = float(_eval_numeric(form[4]))
    return bindings


def load_deltas_last_layer(
    path: str | Path,
    solution_file_name_prefix: str,
    label: int,
    number_of_experts: int = 10,
) -> list[Delta]:
    """Load last-layer deltas for one expert.

    Args:
        path: Directory holding the solution files.
        solution_file_name_prefix: Filename stem, typically ``"solution"``.
        label: Expert label, or ``number_of_experts`` for the full repair.
        number_of_experts: Expert count; selects the ``full.txt`` filename.

    Returns:
        One :class:`Delta` per ``sym`` variable, with ``out_index`` unset.
    """
    directory = Path(path)
    if label == number_of_experts:
        solution_file = directory / "full.txt"
    else:
        solution_file = directory / f"{solution_file_name_prefix}{label}.txt"

    deltas = []
    for name, value in parse_z3_model(solution_file).items():
        match = _SYM_LAST_RE.match(name)
        if match:
            deltas.append(Delta(out_index=None, in_index=int(match.group(1)), value=value))
    return deltas


def load_deltas_intermediate_layer(
    path: str | Path,
    label: int,
    number_of_experts: int = 10,
) -> list[Delta]:
    """Load intermediate-layer deltas for one expert.

    Intermediate solutions are named ``label<N>.txt`` rather than
    ``solution<N>.txt``, matching the artifact's directory layout.
    """
    directory = Path(path)
    if label == number_of_experts:
        solution_file = directory / "full.txt"
    else:
        solution_file = directory / f"label{label}.txt"

    deltas = []
    for name, value in parse_z3_model(solution_file).items():
        match = _SYM_INTER_RE.match(name)
        if match:
            deltas.append(
                Delta(
                    out_index=int(match.group(1)),
                    in_index=int(match.group(2)),
                    value=value,
                )
            )
    return deltas


def _finalize(weight_delta: np.ndarray, expert_ids: Sequence[int], number_of_experts: int) -> np.ndarray:
    """Fill the AVERAGE slot with the mean of the per-expert deltas."""
    if len(expert_ids) > 0:
        weight_delta[number_of_experts + 1] = weight_delta[list(expert_ids)].sum(axis=0) / len(
            expert_ids
        )
    return weight_delta


def load_repaired_weights_mnist0(
    path: str | Path,
    solution_file_name_prefix: str,
    repaired_layer_id: int,
    expert_ids: Sequence[int],
    number_of_experts: int = 10,
    *,
    include_full_repair: bool = True,
) -> np.ndarray:
    """Assemble the MNIST0 weight-delta tensor from solver output.

    Args:
        path: Directory holding the solution files.
        solution_file_name_prefix: Filename stem for last-layer solutions.
        repaired_layer_id: ``6`` (dense_1, 576x128) or ``8`` (dense_2, 128x10).
        expert_ids: Experts to load.
        number_of_experts: Expert count; sizes the slot dimension.
        include_full_repair: Load ``full.txt`` into the FULL slot. The Java
            original had this commented out for the last layer because the
            artifact ships no ``full.txt`` there; we skip it automatically when
            the file is absent rather than requiring the caller to know.

    Returns:
        Array of shape ``(number_of_experts + 2, fan_in, fan_out)``. Slots
        ``0..n-1`` are the experts, slot ``n`` the full repair, slot ``n+1``
        the average.

    Raises:
        LayerNotSupportedError: For layers 0 and 2 (convolutional), which the
            original artifact never implemented.
        LayerNotRepairableError: For any layer holding no weights.
    """
    if repaired_layer_id in (0, 2):
        raise LayerNotSupportedError(
            f"Layer {repaired_layer_id} not supported yet (convolutional repair "
            "was left unimplemented in the original artifact)."
        )

    directory = Path(path)

    if repaired_layer_id == 6:
        weight_delta = np.zeros((number_of_experts + 2, 576, 128), dtype=np.float64)
        for expert_id in expert_ids:
            source = directory / f"label{expert_id}.txt"
            for delta in load_deltas_intermediate_layer(path, expert_id, number_of_experts):
                _place(weight_delta, expert_id, delta.in_index, delta.out_index,
                       delta.value, source=source)
        if include_full_repair and (directory / "full.txt").exists():
            for delta in load_deltas_intermediate_layer(path, number_of_experts, number_of_experts):
                _place(weight_delta, number_of_experts, delta.in_index, delta.out_index,
                       delta.value, source=directory / "full.txt")
        return _finalize(weight_delta, expert_ids, number_of_experts)

    if repaired_layer_id == 8:
        weight_delta = np.zeros((number_of_experts + 2, 128, 10), dtype=np.float64)
        for expert_id in expert_ids:
            source = directory / f"{solution_file_name_prefix}{expert_id}.txt"
            for delta in load_deltas_last_layer(
                path, solution_file_name_prefix, expert_id, number_of_experts
            ):
                # One model per label, so the delta lands in that label's column.
                _place(weight_delta, expert_id, delta.in_index, expert_id,
                       delta.value, source=source)
        return _finalize(weight_delta, expert_ids, number_of_experts)

    raise LayerNotRepairableError(f"Layer {repaired_layer_id} cannot be repaired!")


def load_repaired_weights_cifar10(
    path: str | Path,
    solution_file_name_prefix: str,
    repaired_layer_id: int,
    expert_ids: Sequence[int],
    number_of_experts: int = 10,
) -> np.ndarray:
    """Assemble the CIFAR10 weight-delta tensor from solver output.

    Args:
        repaired_layer_id: ``13`` (dense_2, 512x10) is the only supported layer.

    Returns:
        Array of shape ``(number_of_experts + 2, 512, 10)``.

    Raises:
        LayerNotSupportedError: For layers 0, 2, 5, 7 and 11, which the
            original artifact never implemented.
        LayerNotRepairableError: For any layer holding no weights.
    """
    if repaired_layer_id in (0, 2, 5, 7, 11):
        raise LayerNotSupportedError(
            f"Layer {repaired_layer_id} not supported yet (left unimplemented "
            "in the original artifact)."
        )

    if repaired_layer_id == 13:
        directory = Path(path)
        weight_delta = np.zeros((number_of_experts + 2, 512, 10), dtype=np.float64)
        for expert_id in expert_ids:
            source = directory / f"{solution_file_name_prefix}{expert_id}.txt"
            for delta in load_deltas_last_layer(
                path, solution_file_name_prefix, expert_id, number_of_experts
            ):
                _place(weight_delta, expert_id, delta.in_index, expert_id,
                       delta.value, source=source)
        return _finalize(weight_delta, expert_ids, number_of_experts)

    raise LayerNotRepairableError(f"Layer {repaired_layer_id} cannot be repaired!")
