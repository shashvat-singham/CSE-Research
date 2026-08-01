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
import styles
from theme import INK, bar_with_labels

styles.page_header(
    "NNRepair",
    "Constraint-based repair of neural network classifiers. Browse the published "
    "results, decode the constraint solutions, and re-run the repaired networks "
    "against the full datasets.",
    eyebrow="Artifact companion",
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

styles.metric_row(
    [
        ("Subjects", str(index["subject"].nunique()), "model x fault kind"),
        ("Result files", f"{int((files['kind'] == 'result').sum()):,}", "published CSVs"),
        (
            "Experiment runs",
            f"{len(combination_rows.groupby(['subject', 'layer', 'stem'])):,}",
            "model x dataset",
        ),
        ("Measurements", f"{len(index):,}", "rows indexed"),
    ]
)

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
            "Used by": "Inference",
        },
        {
            "Artifact": "FGSM datasets (10 files, 10,000 inputs each)",
            "Size": "29 MB" if using_bundled_subset() else "941 MB",
            "Available": "Yes",
            "Used by": "Inference",
        },
    ]
)
st.dataframe(availability, hide_index=True, width='stretch')

if using_bundled_subset():
    st.caption(
        "Every page runs on complete data. The FGSM datasets ship losslessly "
        "compressed — 941 MB of CSV text becomes 29 MB, because each file is an "
        "8-bit image perturbed and clipped, so a few hundred distinct values "
        "cover all 7.8 million entries. Decoded values are bit-identical to the "
        "originals. The CIFAR weights are omitted: the artifact ships no CIFAR "
        "datasets to run them against."
    )
else:
    st.caption("Running against a full checkout — every artifact is available.")

