"""Per-expert quality: which repairs helped, and which should be dropped."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

import styles

from app_data import RESULTS_ROOT, results_index
from nnrepair.f1_selection import read_prec_f1, select_experts_by_harmonic_f1
from nnrepair.results import discover_results
from theme import INK, SERIES, bar_with_labels


styles.page_header(
    'Experts',
    'A repair produces one expert per label. Not all of them are improvements — this page shows which experts earn their place.',
    eyebrow='Analysis',
)

index = results_index()
if index.empty:
    st.error("No result files found under `data/Results/`.")
    st.stop()

expert_rows = index[index["ROW_KIND"] == "expert"].copy()
original_rows = index[index["ROW_KIND"] == "original"].copy()

if expert_rows.empty:
    st.warning("No per-expert rows in the result files.")
    st.stop()

# -- pick a run --------------------------------------------------------------

controls = st.columns([2, 3])
subject = controls[0].selectbox("Subject", sorted(expert_rows["subject"].unique()))

runs = sorted(expert_rows.loc[expert_rows["subject"] == subject, "stem"].unique())
run = controls[1].selectbox("Run", runs)

run_experts = expert_rows[(expert_rows["subject"] == subject) & (expert_rows["stem"] == run)]
run_original = original_rows[(original_rows["subject"] == subject) & (original_rows["stem"] == run)]

if run_experts.empty:
    st.warning("This run has no per-expert rows.")
    st.stop()

st.divider()

# -- repaired vs original F1, per label --------------------------------------

st.subheader("Repaired expert against the original network")
st.caption(
    "F1 for each label. The expert is a binary detector for its own label, so "
    "a repair that raises accuracy overall can still be worse for its target."
)

comparison = pd.concat(
    [
        run_experts[["LABEL", "F1"]].assign(Model="Repaired expert"),
        run_original[["LABEL", "F1"]].assign(Model="Original network"),
    ]
).dropna(subset=["LABEL", "F1"])

if comparison.empty:
    st.info("No F1 figures recorded for this run.")
else:
    comparison["Label"] = comparison["LABEL"].astype(int).astype(str)
    comparison["F1"] = comparison["F1"].round(2)

    bars = (
        alt.Chart(comparison)
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
        .properties(height=340)
        .configure_view(strokeWidth=0, fill=INK["surface"])
        .configure_axis(
            gridColor=INK["grid"], domainColor=INK["axis"], tickColor=INK["axis"],
            labelColor=INK["secondary"], titleColor=INK["secondary"],
            labelFontSize=11, titleFontSize=11, titleFontWeight="normal",
        )
        .configure_legend(labelColor=INK["secondary"], labelFontSize=11, symbolType="square")
    )
    st.altair_chart(bars, use_container_width=True)

    # Verdict per label.
    wide = comparison.pivot_table(index="Label", columns="Model", values="F1")
    if {"Repaired expert", "Original network"} <= set(wide.columns):
        wide["Delta"] = (wide["Repaired expert"] - wide["Original network"]).round(2)
        improved = wide[wide["Delta"] > 0].index.tolist()
        st.markdown(
            f"**{len(improved)} of {len(wide)} experts improve on the original**"
            + (f" — labels {', '.join(improved)}." if improved else ".")
        )
        with st.expander("Table view"):
            st.dataframe(wide.sort_index(key=lambda i: i.astype(int)), width='stretch')

st.divider()

# -- precision / recall / targeted accuracy ----------------------------------

st.subheader("Where each expert's errors come from")
st.caption(
    "Precision falls when an expert claims inputs belonging to other labels; "
    "recall falls when it misses its own. Targeted accuracy is its score on "
    "just the label it was repaired for."
)

metric = st.radio(
    "Metric",
    ["PREC", "RECALL", "F1", "TAR-ACC"],
    horizontal=True,
    format_func=lambda m: {
        "PREC": "Precision", "RECALL": "Recall", "F1": "F1", "TAR-ACC": "Targeted accuracy",
    }[m],
)

metric_frame = run_experts[["LABEL", metric]].dropna().copy()
if metric_frame.empty:
    st.info(f"No {metric} figures recorded for this run.")
else:
    metric_frame["Label"] = metric_frame["LABEL"].astype(int).astype(str)
    metric_frame[metric] = metric_frame[metric].round(2)
    metric_frame = metric_frame.sort_values("LABEL")

    st.altair_chart(
        bar_with_labels(
            metric_frame,
            x="Label",
            y=metric,
            y_title=f"{metric} (%)",
            tooltip=["Label", metric],
        ),
        use_container_width=True,
    )
    with st.expander("Table view"):
        st.dataframe(
            run_experts[["LABEL", "TP", "TN", "FP", "FN", "PREC", "RECALL", "F1", "TAR-ACC"]]
            .sort_values("LABEL"),
            hide_index=True,
            width='stretch',
        )

st.divider()

# -- harmonic F1 selection ---------------------------------------------------

st.subheader("Harmonic-F1 expert selection")
st.markdown(
    "An expert that fixes adversarial inputs by wrecking clean accuracy scores "
    "well on one dataset and badly on the other. Taking the **harmonic mean** of "
    "its F1 on both punishes that lopsidedness, and only experts that beat the "
    "original network on the mean are kept."
)

sidecars = [
    f for f in discover_results(RESULTS_ROOT)
    if f.is_sidecar and f.subject == subject and f.selection == "all"
]

adversarial_options = {f.stem: f for f in sidecars if f.dataset in {"ADV_TRAINING", "POISONED_TRAINING"}}
clean_options = {f.stem: f for f in sidecars if f.dataset == "TRAINING"}

if not adversarial_options or not clean_options:
    st.info(
        "This subject does not ship both an attacked-training and a clean-training "
        "sidecar, which the harmonic criterion needs."
    )
else:
    pick = st.columns(2)
    adv_key = pick[0].selectbox("Attacked training run", sorted(adversarial_options))
    clean_key = pick[1].selectbox("Clean training run", sorted(clean_options))

    adv_record = read_prec_f1(adversarial_options[adv_key].path)
    clean_record = read_prec_f1(clean_options[clean_key].path)

    if adv_record.f1_values.size == 0 or clean_record.f1_values.size == 0:
        st.warning("One of the selected sidecars has no F1 values.")
    else:
        selected, repaired, original = select_experts_by_harmonic_f1(adv_record, clean_record)

        harmonic = pd.DataFrame(
            {
                "Label": [str(i) for i in range(len(repaired))] * 2,
                "Harmonic F1": list(repaired.round(4)) + list(original.round(4)),
                "Model": ["Repaired expert"] * len(repaired) + ["Original network"] * len(original),
            }
        )

        chart = (
            alt.Chart(harmonic)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("Label:N", title="Label", axis=alt.Axis(labelAngle=0)),
                xOffset=alt.XOffset("Model:N"),
                y=alt.Y("Harmonic F1:Q", title="Harmonic mean of F1"),
                color=alt.Color(
                    "Model:N",
                    scale=alt.Scale(
                        domain=["Original network", "Repaired expert"],
                        range=[SERIES[0], SERIES[1]],
                    ),
                    legend=alt.Legend(title=None, orient="top"),
                ),
                tooltip=["Label", "Model", "Harmonic F1"],
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

        kept = ", ".join(str(i) for i in selected) if selected else "none"
        dropped = ", ".join(str(i) for i in range(len(repaired)) if i not in selected) or "none"
        summary = st.columns(2)
        summary[0].success(f"**Kept:** {kept}")
        summary[1].warning(f"**Dropped:** {dropped}")

        with st.expander("Table view"):
            st.dataframe(
                pd.DataFrame(
                    {
                        "Label": range(len(repaired)),
                        "Repaired harmonic F1": repaired.round(4),
                        "Original harmonic F1": original.round(4),
                        "Kept": [i in selected for i in range(len(repaired))],
                    }
                ),
                hide_index=True,
                width='stretch',
            )
