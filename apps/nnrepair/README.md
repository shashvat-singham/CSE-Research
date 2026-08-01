# NNRepair

An interactive companion to the NNRepair artifact, plus a Python port of its
Java implementation.

**Live: https://nnrepair.streamlit.app**

Deploys to Streamlit Community Cloud from
[shashvat-singham/nnrepair-app](https://github.com/shashvat-singham/nnrepair-app),
a split-out copy of this directory that avoids cloning the 954 MB of research
data in the parent repository.

> **Python 3.14 note.** Streamlit Community Cloud builds on Python 3.14, where
> Altair 5.5 fails to import: it guards its PEP 728 `TypedDict`s with
> `sys.version_info >= (3, 14)`, expecting `closed=True` to have reached the
> stdlib `typing` module in that release. It did not, so that branch raises
> `TypeError` at import. `requirements.txt` therefore floors Altair at 6.2.2,
> which moved the guard to `>= (3, 15)`. Do not cap it below 6 again.

## Running it

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

```bash
pip install -e ".[dev]"
pytest
```

## Pages

| Page | Needs |
|---|---|
| Overview | bundled result CSVs |
| Results Explorer | bundled result CSVs |
| Expert Analysis | bundled result CSVs |
| Solver Output | `NNRepair/Z3Solutions` (14 MB, local checkout) |
| Run Inference | `NNRepair/NN-Code` weights and datasets (954 MB, local checkout) |

The result CSVs are copied into `data/Results` so the hosted app is
self-contained. The last two pages detect their artifacts and explain the
absence rather than failing.

## The Python port

`nnrepair/` is a port of the eleven Java files in
`NNRepair/CombinationCode/module4_combination`.

| Java | Python |
|---|---|
| `ExpertCombination.java` | `combination.py` |
| `Z3SolutionParsing.java` | `z3_solutions.py` |
| `MNIST0_InternalData.java`, `CIFAR10_InternalData.java` | `models/internal_data.py` |
| `MNIST0_DNNt_Original.java`, `MNIST0_DNNt_Combined.java` | `models/mnist0.py` |
| `CIFAR10_DNNt_Original.java`, `CIFAR10_DNNt_Combined.java` | `models/cifar10.py` |
| `F1SelectionHarmonic.java` | `f1_selection.py` |
| `Experiments.java` | `experiments.py`, `metrics.py` |

`MNIST0_DNNt_pattern_based.java` duplicates the combined model with a fixed
expert set; that is `expert_ids` here rather than a separate class.

### What the port changes deliberately

**Layers are NumPy, not nested loops.** The Java spells each layer out as four
to six nested `for` loops over scalar doubles. `models/layers.py` expresses the
same operations as array ops. `tests/test_layers.py` and `tests/test_networks.py`
check them against literal transcriptions of the Java loops; on real weights and
real inputs the two agree to **1.6e-14**, which is float64 rounding.

**Experts are evaluated in one batched matmul.** A repair only perturbs one
dense layer, so every expert shares the trunk. The Java recomputed the whole
network twelve times per input; the port computes the trunk once and diverges in
a single `einsum`. 10,000 MNIST inputs across twelve variants take ~22 s.

**Z3 output is parsed as s-expressions.** The Java walked the solver output
line by line, counting `.` characters to guess whether a rational had wrapped
onto a second line:

```java
if (line.chars().filter(ch -> ch == '.').count() == 1) {
    line = brread.readLine();
}
```

The intermediate-layer files in this repository *do* wrap long rationals, so
that heuristic is load-bearing and fragile. `z3_solutions.py` tokenises the
model properly, which is format-independent. It also evaluates rationals as
`fractions.Fraction` before the single narrowing to `float` — Z3 emits
hundred-digit numerators, and dividing two pre-rounded floats loses precision
the exact path keeps. All 290 shipped solution files parse.

**Paths are arguments.** `Experiments.java` encoded ~100 configurations as
`enum` constants with absolute paths (`C:\Users\mlast\Desktop\experiments\...`),
so it only ran on its author's machine. `Subject` takes them as fields.

**Rounding follows Java, not Python.** `BigDecimal.HALF_UP` rounds half away
from zero; Python's `round()` uses banker's rounding, so `round(0.125, 2)` is
`0.12` where Java gives `0.13`. `metrics.round_half_up` reproduces the Java,
because the shipped CSVs were produced with it.

**Unimplemented layers raise distinct errors.** The Java threw
`RuntimeException("Layer N not supported yet!")` for convolutional repair and
`RuntimeException("Layer N cannot be repaired!")` for weightless layers. These
are now `LayerNotSupportedError` and `LayerNotRepairableError`, so a caller can
tell "nobody wrote this yet" from "this is not a thing".

### One behaviour left as-is

`combineExpertsByPVC` breaks a three-way tie by iterating a Java `HashMap` and
keeping the first maximum, which is hash-order dependent. The port iterates in
claim order. The two agree whenever there is a unique winner — which a 3-way
vote over ≤3 candidates guarantees unless all three verdicts differ, and in that
case the Java's own answer was not well-defined either.

## A discrepancy worth knowing about

Running the port on `MNIST-Adversarial / Lastlayer / eps.05_ExpA` against the
FGSM ε=0.05 test set reproduces the *shape* of the published result but not the
exact numbers:

| Strategy | Ported | Shipped CSV |
|---|---|---|
| ORIG | 29.92 | 28.37 |
| NAIVE | 29.92 | 28.38 |
| AVERAGE | 30.43 | 28.71 |
| CONF | **38.15** | **36.17** |
| VOTES | 29.96 | 28.38 |

The ordering, the size of CONF's lead, and `NAIVE == VOTES` all match. The level
is ~1.5 points high across the board.

**This is not a porting error.** `ORIG` involves no repair deltas at all — it is
the unrepaired network — so a gap there is upstream of every combination
strategy. On the same weights and inputs the port's forward pass agrees with a
literal transcription of `MNIST0_DNNt_Original.run()` to 1.6e-14, and no other
epsilon or dataset in the repository lands nearer to 2837/10000.

The likely cause is that the weight dumps and FGSM files committed here are not
byte-identical to the ones that produced the shipped CSVs — FGSM perturbations
depend on the model that generated them, so a regeneration produces a different
test set. Worth confirming against the original authors before quoting either
set of numbers.

Note also that the FGSM files are **already normalised to [0, 1]**. Passing
`needs_normalization=True` for them divides by 255 again and drops the network
to ~10% — chance. The Run Inference page detects the range and sets the default
accordingly.

## Charts

`theme.py` holds a categorical palette validated for colour-vision deficiency
against the light surface `#fcfcfb` (worst adjacent CVD ΔE 9.1, normal-vision
ΔE 19.6). Three slots sit below 3:1 contrast on that surface, so every chart
ships direct value labels and a table view — identity is never carried by hue
alone. The app pins Streamlit's light theme in `.streamlit/config.toml` so the
rendered colours are the ones that were actually validated.
