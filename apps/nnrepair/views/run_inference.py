"""Run the ported networks live, on real weights and real inputs.

This is the page that exercises the Python port end to end: load extracted
weights, decode a Z3 model into deltas, run the original and every repaired
expert over a slice of a dataset, and combine their verdicts.
"""

from __future__ import annotations

import time
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import styles

from app_data import (
    NN_CODE_ROOT,
    Z3_ROOT,
    bundled_subset_note,
    have_weights,
    have_z3_solutions,
    missing_artifact_note,
)
from nnrepair.combination import CombinationMethod
from nnrepair.datasets import load_inputs
from nnrepair.experiments import Subject, read_inputs, run_experiment
from theme import INK, SERIES, bar_with_labels


styles.page_header(
    'Inference',
    'Runs the repaired networks with the ported implementation over a full dataset, rather than reading numbers someone else computed.',
    eyebrow='Execution',
)

if not have_weights():
    missing_artifact_note("Extracted network weights", NN_CODE_ROOT)
    st.stop()
if not have_z3_solutions():
    missing_artifact_note("Z3 solutions", Z3_ROOT)
    st.stop()

bundled_subset_note()


@st.cache_data(show_spinner=False)
def available_models() -> pd.DataFrame:
    """Weight directories that hold a complete MNIST0 or CIFAR10 parameter set."""
    rows = []
    for params in sorted(NN_CODE_ROOT.glob("*/params")):
        names = {p.name for p in params.glob("*.txt")}
        if {"weights0.txt", "weights2.txt", "weights6.txt", "weights8.txt"} <= names:
            model = "mnist0"
        elif {"weights11.txt", "weights13.txt"} <= names:
            model = "cifar10"
        else:
            continue
        rows.append(
            {
                "name": params.parent.name,
                "model": model,
                "params": str(params),
                "root": str(params.parent),
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def available_datasets(model_root: str) -> pd.DataFrame:
    """Input datasets under a model directory, each paired with its labels.

    A split's labels live beside its inputs — ``data/`` holds the test set,
    ``val-data/`` the validation set — and the two must not be crossed. Pairing
    them here means the page cannot offer a mismatched combination.

    Datasets may be either the original ``.txt`` or the compressed ``.npz``;
    both are read transparently, so only one entry per dataset is listed even
    when both forms are on disk.
    """
    rows = []
    for split_dir, split in ((Path(model_root) / "data", "test"),
                             (Path(model_root) / "val-data", "validation")):
        if not split_dir.is_dir():
            continue

        labels = next(
            (p for p in sorted(split_dir.glob("*.txt")) if "label" in p.name.lower()), None
        )
        if labels is None:
            continue

        seen: set[str] = set()
        for candidate in sorted(split_dir.iterdir()):
            if candidate.suffix not in {".txt", ".npz"}:
                continue
            if "label" in candidate.name.lower():
                continue
            if candidate.stem in seen:
                continue
            seen.add(candidate.stem)
            rows.append(
                {
                    "label": f"{split} · {candidate.stem}",
                    "split": split,
                    "inputs": str(candidate),
                    "labels": str(labels),
                    "compressed": candidate.suffix == ".npz",
                }
            )
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def count_rows(path: str) -> int:
    """Number of inputs in a dataset, without decoding the whole thing."""
    file = Path(path)
    if file.suffix == ".npz":
        with np.load(file) as archive:
            return int(archive["codes"].shape[0])
    with file.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for line in handle if line.strip())


@st.cache_data(show_spinner=False)
def peek_range(path: str, rows: int = 8) -> tuple[float, float]:
    """Observed value range over the first few rows, for the 0–255 check."""
    sample = load_inputs(path, limit=rows)
    if sample.size == 0:
        return (0.0, 0.0)
    return (float(sample.min()), float(sample.max()))


@st.cache_data(show_spinner=False)
def repair_directories() -> pd.DataFrame:
    """Z3 solution directories, with the layer each targets."""
    rows = []
    for directory in sorted(p for p in Z3_ROOT.glob("*/*/*") if p.is_dir()):
        files = {p.name for p in directory.glob("*.txt")}
        if any(n.startswith("solution") for n in files):
            kind, prefix = "last", "solution"
        elif any(n.startswith("label") for n in files):
            kind, prefix = "intermediate", "label"
        else:
            continue
        relative = directory.relative_to(Z3_ROOT).parts
        subject = relative[0]
        # A solution is only meaningful against the architecture it was solved
        # for: CIFAR's final layer is 512 wide, MNIST0's is 128, so crossing
        # them indexes past the end of the tensor.
        architecture = "cifar10" if subject.lower().startswith("cifar") else "mnist0"
        rows.append(
            {
                "label": "/".join(relative),
                "path": str(directory),
                "kind": kind,
                "prefix": prefix,
                "subject": subject,
                "architecture": architecture,
            }
        )
    return pd.DataFrame(rows)


models = available_models()
repairs = repair_directories()

if models.empty or repairs.empty:
    st.warning("No complete weight set or solution directory found.")
    st.stop()

# -- configuration -----------------------------------------------------------

st.subheader("Configuration")

config = st.columns(2)
model_name = config[0].selectbox("Network weights", models["name"].tolist())
model_row = models[models["name"] == model_name].iloc[0]

# Only offer solutions solved for the selected architecture.
compatible = repairs[repairs["architecture"] == model_row["model"]]
if compatible.empty:
    st.warning(
        f"No Z3 solutions available for the {model_row['model']} architecture. "
        f"`{model_name}` cannot be paired with any of the bundled repairs."
    )
    st.stop()

repair_label = config[1].selectbox(
    "Repair (Z3 solutions)",
    compatible["label"].tolist(),
    help="Filtered to solutions solved for the selected architecture.",
)
repair_row = compatible[compatible["label"] == repair_label].iloc[0]

# The solution directory determines which layer was repaired — an
# intermediate-layer solution cannot be applied to the last layer. Deriving it
# removes the mismatch rather than leaving it to the reader to avoid.
if model_row["model"] == "mnist0":
    repaired_layer_id = 8 if repair_row["kind"] == "last" else 6
    layer_description = (
        "Last layer — dense_2, 128→10" if repaired_layer_id == 8
        else "Intermediate — dense_1, 576→128"
    )
else:
    repaired_layer_id = 13
    layer_description = "Last layer — dense_2, 512→10"

data_config = st.columns(3)
data_config[0].markdown(
    f"**Repaired layer**  \n{layer_description}",
    help="Determined by the solution directory, which fixes which layer was solved for.",
)

datasets = available_datasets(model_row["root"])
if datasets.empty:
    st.warning(
        f"`{model_row['name']}` ships no input datasets. Only the MNIST0 "
        "adversarial subject has them; the others provide weights alone."
    )
    st.stop()

dataset_label = data_config[1].selectbox(
    "Input dataset",
    datasets["label"].tolist(),
    help="Labels are paired automatically with each split.",
)
dataset_row = datasets[datasets["label"] == dataset_label].iloc[0]

available_rows = count_rows(dataset_row["inputs"])
data_config[2].markdown(
    f"**Labels**  \n`{Path(dataset_row['labels']).name}`",
    help="Determined by the split, so test inputs cannot be scored against validation labels.",
)

run_config = st.columns([2, 2, 3])
sample_size = run_config[0].number_input(
    "Inputs to evaluate",
    min_value=10,
    max_value=int(available_rows),
    value=int(available_rows),
    step=500,
    help=f"The full split is {available_rows:,} inputs, at roughly 450 per second.",
)

# Normalisation is a real trap: the FGSM files are already in [0, 1], and
# dividing by 255 again silently reduces the network to chance.
low, high = peek_range(dataset_row["inputs"])
looks_normalized = high <= 1.0
normalize = run_config[1].checkbox(
    "Divide inputs by 255",
    value=not looks_normalized,
    help="Raw MNIST/CIFAR values are 0–255; the FGSM files are already 0–1.",
)
run_config[2].caption(
    f"Observed range **{low:.3g} – {high:.3g}** over the first rows. "
    + ("Already normalised, so leave this unchecked." if looks_normalized
       else "Looks like raw 0–255 values.")
)

if st.button("Run inference", type="primary"):
    subject = Subject(
        name=f"{model_name}_{repair_label.replace('/', '_')}_{dataset_row['split']}",
        model=model_row["model"],
        params_path=model_row["params"],
        repair_path=repair_row["path"],
        repaired_layer_id=repaired_layer_id,
        solution_file_name_prefix=repair_row["prefix"],
        input_file_path=dataset_row["inputs"],
        label_file_path=dataset_row["labels"],
        needs_normalization=normalize,
    )

    progress = st.progress(0.0, text="Loading weights and decoding solver output…")

    def report(done: int, total: int) -> None:
        progress.progress(min(done / total, 1.0), text=f"Evaluated {done:,} of {total:,} inputs")

    started = time.perf_counter()
    try:
        result = run_experiment(
            subject, CombinationMethod.ALL, stop_after=int(sample_size), progress=report
        )
    except (FileNotFoundError, ValueError) as error:
        progress.empty()
        st.error(f"Could not run this configuration: {error}")
        st.stop()

    elapsed = time.perf_counter() - started
    progress.empty()
    st.session_state["last_result"] = result
    st.session_state["last_elapsed"] = elapsed

result = st.session_state.get("last_result")
if result is None:
    st.info("Choose a configuration and press **Run inference**.")
    st.stop()

elapsed = st.session_state.get("last_elapsed", 0.0)

st.divider()
st.subheader("Results")
st.caption(
    f"{result.evaluated:,} inputs in {elapsed:.1f}s "
    f"({result.evaluated / elapsed:.0f} per second)."
)

# -- accuracy by strategy ----------------------------------------------------

accuracy = pd.DataFrame(
    [
        {"Strategy": method.value, "Accuracy": counts.accuracy, "Pass": counts.passed,
         "Fail": counts.failed}
        for method, counts in result.combination_counts.items()
        if counts.total
    ]
)

if accuracy.empty:
    st.warning("No combination method produced a verdict.")
    st.stop()

accuracy["Accuracy"] = accuracy["Accuracy"].round(2)

st.altair_chart(
    bar_with_labels(
        accuracy,
        x="Strategy",
        y="Accuracy",
        color="Strategy",
        color_domain=accuracy["Strategy"].tolist(),
        y_title="Accuracy (%)",
        tooltip=["Strategy", "Accuracy", "Pass", "Fail"],
    ),
    use_container_width=True,
)

baseline = accuracy.loc[accuracy["Strategy"] == "ORIG", "Accuracy"]
if not baseline.empty:
    best = accuracy.loc[accuracy["Accuracy"].idxmax()]
    delta = best["Accuracy"] - baseline.iloc[0]
    if delta > 0:
        st.success(
            f"**{best['Strategy']}** reaches **{best['Accuracy']:.2f}%**, "
            f"**+{delta:.2f} points** over the unrepaired network."
        )
    else:
        st.warning(
            f"No strategy beat the unrepaired network's **{baseline.iloc[0]:.2f}%** "
            "on this slice."
        )

with st.expander("Table view"):
    st.dataframe(accuracy, hide_index=True, width='stretch')

st.divider()

# -- per-expert breakdown ----------------------------------------------------

st.subheader("Per-expert breakdown")

experts = pd.DataFrame(
    [
        {
            "Label": expert_id,
            "Precision": counts.precision * 100,
            "Recall": counts.recall * 100,
            "F1": counts.f1 * 100,
            "Targeted accuracy": counts.targeted_accuracy,
            "TP": counts.tp, "FP": counts.fp, "FN": counts.fn, "TN": counts.tn,
        }
        for expert_id, counts in sorted(result.expert_counts.items())
    ]
).round(2)

original = pd.DataFrame(
    [
        {"Label": expert_id, "F1": counts.f1 * 100}
        for expert_id, counts in sorted(result.original_counts.items())
    ]
).round(2)

compare = pd.concat(
    [
        experts[["Label", "F1"]].assign(Model="Repaired expert"),
        original.assign(Model="Original network"),
    ]
).dropna(subset=["F1"])

if not compare.empty:
    compare["Label"] = compare["Label"].astype(int).astype(str)
    chart = (
        alt.Chart(compare)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Label:N", title="Label", axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset("Model:N"),
            y=alt.Y("F1:Q", title="F1 (%)"),
            color=alt.Color(
                "Model:N",
                scale=alt.Scale(
                    domain=["Original network", "Repaired expert"],
                    range=[SERIES[0], SERIES[1]],
                ),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=["Label", "Model", "F1"],
        )
        .properties(height=320)
        .configure_view(strokeWidth=0, fill=INK["surface"])
        .configure_axis(
            gridColor=INK["grid"], domainColor=INK["axis"], tickColor=INK["axis"],
            labelColor=INK["secondary"], titleColor=INK["secondary"],
            labelFontSize=11, titleFontSize=11, titleFontWeight="normal",
        )
        .configure_legend(labelColor=INK["secondary"], labelFontSize=11, symbolType="square")
    )
    st.altair_chart(chart, use_container_width=True)

st.dataframe(experts, hide_index=True, width='stretch')

rows = pd.DataFrame(result.rows())
st.download_button(
    "Download result CSV",
    rows.to_csv(index=False, sep=";").encode("utf-8"),
    file_name=f"{result.subject.name}.csv",
    mime="text/csv",
)
