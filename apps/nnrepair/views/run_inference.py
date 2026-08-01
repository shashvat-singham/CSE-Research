"""Run the ported networks live, on real weights and real inputs.

This is the page that exercises the Python port end to end: load extracted
weights, decode a Z3 model into deltas, run the original and every repaired
expert over a slice of a dataset, and combine their verdicts.
"""

from __future__ import annotations

import time

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from app_data import (
    NN_CODE_ROOT,
    Z3_ROOT,
    bundled_subset_note,
    have_weights,
    have_z3_solutions,
    missing_artifact_note,
)
from nnrepair.combination import CombinationMethod
from nnrepair.experiments import Subject, read_inputs, run_experiment
from theme import INK, SERIES, bar_with_labels


st.title("Run Inference")
st.caption(
    "Execute the repaired networks with the ported implementation, rather than "
    "reading numbers someone else computed."
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
        datasets = sorted(
            p.name for p in (params.parent / "data").glob("*.txt")
        ) if (params.parent / "data").is_dir() else []
        rows.append(
            {
                "name": params.parent.name,
                "model": model,
                "params": str(params),
                "data_dir": str(params.parent / "data"),
                "datasets": datasets,
            }
        )
    return pd.DataFrame(rows)


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
        rows.append(
            {
                "label": "/".join(relative),
                "path": str(directory),
                "kind": kind,
                "prefix": prefix,
                "subject": relative[0],
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

repair_label = config[1].selectbox("Repair (Z3 solutions)", repairs["label"].tolist())
repair_row = repairs[repairs["label"] == repair_label].iloc[0]

if model_row["model"] == "mnist0":
    layer_options = {"Last layer (dense_2, 128→10)": 8, "Intermediate (dense_1, 576→128)": 6}
    default_layer = 0 if repair_row["kind"] == "last" else 1
else:
    layer_options = {"Last layer (dense_2, 512→10)": 13}
    default_layer = 0

data_config = st.columns(3)
layer_choice = data_config[0].selectbox(
    "Repaired layer", list(layer_options), index=default_layer
)
repaired_layer_id = layer_options[layer_choice]

datasets = list(model_row["datasets"])
label_files = [d for d in datasets if "label" in d.lower()]
input_files = [d for d in datasets if "label" not in d.lower()]

if not input_files or not label_files:
    st.warning(
        f"`{model_row['name']}` has no `data/` directory with both inputs and labels. "
        "Pick another weight set."
    )
    st.stop()

input_file = data_config[1].selectbox("Input dataset", input_files)
label_file = data_config[2].selectbox("Labels", label_files)

run_config = st.columns([2, 2, 3])
sample_size = run_config[0].number_input(
    "Inputs to evaluate", min_value=10, max_value=10_000, value=500, step=50,
    help="Roughly 450 MNIST inputs per second.",
)

# Normalisation is a real trap here: the FGSM files are already in [0, 1],
# so dividing by 255 silently reduces the network to chance.
peek = np.fromstring(
    open(f"{model_row['data_dir']}/{input_file}", encoding="utf-8").readline(), sep=","
)
looks_normalized = peek.size > 0 and peek.max() <= 1.0
normalize = run_config[1].checkbox(
    "Divide inputs by 255",
    value=not looks_normalized,
    help="Raw MNIST/CIFAR CSVs are 0–255; the FGSM files are already 0–1.",
)
run_config[2].caption(
    f"Detected range of the first row: **{peek.min():.3g} – {peek.max():.3g}**. "
    + ("Already normalised, so leave the box unchecked." if looks_normalized
       else "Looks like raw 0–255 values.")
)

if st.button("Run inference", type="primary"):
    subject = Subject(
        name=f"{model_name}_{repair_label.replace('/', '_')}",
        model=model_row["model"],
        params_path=model_row["params"],
        repair_path=repair_row["path"],
        repaired_layer_id=repaired_layer_id,
        solution_file_name_prefix=repair_row["prefix"],
        input_file_path=f"{model_row['data_dir']}/{input_file}",
        label_file_path=f"{model_row['data_dir']}/{label_file}",
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
