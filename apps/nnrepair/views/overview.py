"""NNRepair — landing page.

Explains what the artifact contains and gives a headline read on whether the
repairs worked, before the deeper pages.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app_data import (
    METHOD_BLURBS,
    SUBJECT_BLURBS,
    have_weights,
    have_z3_solutions,
    result_files,
    results_index,
    using_bundled_subset,
)
from theme import INK, bar_with_labels


st.title("NNRepair")
st.markdown(
    "**Constraint-based repair of neural network classifiers.** "
    "An interactive companion to the artifact: browse the published results, "
    "inspect the constraint solutions, and re-run the repaired networks."
)

index = results_index()
files = result_files()

if index.empty:
    st.error(
        "No result files found. Expected CSVs under `data/Results/`. "
        "If you are running locally, copy them from `NNRepair/Results`."
    )
    st.stop()

# -- headline numbers --------------------------------------------------------

combination_rows = index[index["ROW_KIND"] == "combination"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Subjects", index["subject"].nunique())
col2.metric("Result files", int((files["kind"] == "result").sum()))
col3.metric("Experiment runs", len(combination_rows.groupby(["subject", "layer", "stem"])))
col4.metric("Measurements", f"{len(index):,}")

st.divider()

# -- what the method does ----------------------------------------------------

left, right = st.columns([3, 2], gap="large")

with left:
    st.subheader("How the repair works")
    st.markdown(
        """
Rather than retraining, NNRepair encodes a *repair* as a constraint problem
over one layer's weights and hands it to Z3.

1. **Fault localisation** picks a layer to repair — an intermediate dense layer
   or the final classification layer.
2. **Constraint generation** builds, for each label `k`, a formula asserting
   that the network classifies label-`k` inputs correctly while leaving a set
   of already-passing tests undisturbed.
3. **Solving** yields a set of weight *deltas* per label. Each patched network
   is an **expert** for its label.
4. **Combination** merges the ten experts back into one classifier — the step
   this app spends most of its time on, because it is where the accuracy
   actually comes from.

Experiments **ExpA**–**ExpD** vary how many already-passing tests the
constraints must preserve: 0, 10, 50 and 100 respectively. More preserved tests
means a more conservative repair.
        """
    )

with right:
    st.subheader("Combination strategies")
    for method, blurb in METHOD_BLURBS.items():
        st.markdown(f"**{method}** — {blurb}")

st.divider()

# -- headline chart ----------------------------------------------------------

st.subheader("Does the repair beat the original network?")
st.caption(
    "Mean accuracy across every run of each subject, by combination strategy. "
    "ORIG is the unrepaired baseline. Bars above it are a real improvement."
)

subject = st.selectbox(
    "Subject",
    sorted(index["subject"].unique()),
    help="Model architecture and the kind of fault being repaired.",
)
st.caption(SUBJECT_BLURBS.get(subject, ""))

subject_rows = combination_rows[combination_rows["subject"] == subject]
summary = (
    subject_rows.groupby("COMBINATION", as_index=False)["ACCURACY"]
    .mean()
    .dropna(subset=["ACCURACY"])
)

if summary.empty:
    st.warning("No accuracy figures recorded for this subject.")
else:
    order = [m for m in METHOD_BLURBS if m in set(summary["COMBINATION"])]
    summary["COMBINATION"] = pd.Categorical(summary["COMBINATION"], order, ordered=True)
    summary = summary.sort_values("COMBINATION")
    summary["ACCURACY"] = summary["ACCURACY"].round(2)

    st.altair_chart(
        bar_with_labels(
            summary,
            x="COMBINATION",
            y="ACCURACY",
            color="COMBINATION",
            color_domain=order,
            x_title="",
            y_title="Mean accuracy (%)",
            tooltip=["COMBINATION", "ACCURACY"],
        ),
        use_container_width=True,
    )

    baseline = summary.loc[summary["COMBINATION"] == "ORIG", "ACCURACY"]
    if not baseline.empty:
        best = summary.loc[summary["ACCURACY"].idxmax()]
        delta = best["ACCURACY"] - baseline.iloc[0]
        verdict = (
            f"Best strategy is **{best['COMBINATION']}** at **{best['ACCURACY']:.2f}%**, "
            f"{'up' if delta >= 0 else 'down'} **{abs(delta):.2f} points** on the "
            f"unrepaired network's {baseline.iloc[0]:.2f}%."
        )
        st.markdown(verdict)

    with st.expander("Table view"):
        st.dataframe(summary, hide_index=True, width='stretch')

st.divider()

# -- what is available in this deployment ------------------------------------

st.subheader("What this deployment includes")

availability = pd.DataFrame(
    [
        {
            "Artifact": "Experiment results (345 CSVs)",
            "Size": "1.5 MB",
            "Available": "Yes",
            "Used by": "Results Explorer, Expert Analysis",
        },
        {
            "Artifact": "Z3 solutions (290 files, all 5 subjects)",
            "Size": "14 MB",
            "Available": "Yes" if have_z3_solutions() else "Clone to enable",
            "Used by": "Solver Output",
        },
        {
            "Artifact": "MNIST0 adversarial weights",
            "Size": "1.6 MB",
            "Available": "Yes" if have_weights() else "Clone to enable",
            "Used by": "Run Inference",
        },
        {
            "Artifact": "Full MNIST/CIFAR datasets & CIFAR weights",
            "Size": "954 MB",
            "Available": "Full dataset" if not using_bundled_subset() else "1,000-input slice",
            "Used by": "Run Inference",
        },
    ]
)
st.dataframe(availability, hide_index=True, width='stretch')

if using_bundled_subset():
    st.caption(
        "Every page works here. The one thing this deployment trims is the raw "
        "input data: ten of those files are 94 MB each, so Run Inference ships "
        "with the first 1,000 inputs of the FGSM ε=0.05 test set rather than "
        "all 10,000, and without the CIFAR weights. Clone the repository for "
        "the complete set."
    )
else:
    st.caption("Running against a full checkout — every artifact is available.")

