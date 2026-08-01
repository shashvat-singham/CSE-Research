"""Filter and compare the published experiment results."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from app_data import SUBJECT_BLURBS, results_index, selection_label
from theme import INK, SEQUENTIAL, bar_with_labels, categorical_scale

st.set_page_config(page_title="Results Explorer — NNRepair", page_icon="📊", layout="wide")

st.title("Results Explorer")
st.caption(
    "Every published run, filterable. Each run is one repaired model evaluated "
    "on one dataset; rows are the combination strategies and the individual experts."
)

index = results_index()
if index.empty:
    st.error("No result files found under `data/Results/`.")
    st.stop()

combination_rows = index[index["ROW_KIND"] == "combination"].copy()

# -- filters, in one row above the charts ------------------------------------

filter_row = st.columns([2, 2, 2, 2, 2])

subjects = sorted(index["subject"].unique())
subject = filter_row[0].selectbox("Subject", subjects)

scoped = combination_rows[combination_rows["subject"] == subject]

layers = sorted(scoped["layer"].dropna().unique())
layer = filter_row[1].selectbox("Repaired layer", ["All"] + layers)
if layer != "All":
    scoped = scoped[scoped["layer"] == layer]

datasets = sorted(scoped["dataset"].dropna().unique())
dataset = filter_row[2].selectbox("Dataset", ["All"] + datasets)
if dataset != "All":
    scoped = scoped[scoped["dataset"] == dataset]

selections = sorted(scoped["selection"].dropna().unique())
selection = filter_row[3].selectbox(
    "Expert selection", ["All"] + selections, format_func=lambda s: selection_label(s) if s != "All" else "All"
)
if selection != "All":
    scoped = scoped[scoped["selection"] == selection]

epsilons = sorted(scoped["epsilon"].dropna().unique())
if epsilons:
    epsilon = filter_row[4].selectbox("Epsilon", ["All"] + epsilons)
    if epsilon != "All":
        scoped = scoped[scoped["epsilon"] == epsilon]
else:
    filter_row[4].markdown(
        f"<p style='color:{INK['muted']};font-size:0.8rem;margin-top:2rem'>No epsilon variants</p>",
        unsafe_allow_html=True,
    )

st.caption(SUBJECT_BLURBS.get(subject, ""))

scoped = scoped.dropna(subset=["ACCURACY"])
if scoped.empty:
    st.warning("No runs match this filter combination.")
    st.stop()

st.markdown(f"**{len(scoped)}** measurements across **{scoped['stem'].nunique()}** runs.")

st.divider()

# -- accuracy by strategy ----------------------------------------------------

st.subheader("Accuracy by combination strategy")

method_order = [m for m in
                ["ORIG", "NAIVE", "AVERAGE", "FULL", "PREC", "CONF", "VOTES", "PVC"]
                if m in set(scoped["COMBINATION"])]

by_method = (
    scoped.groupby("COMBINATION", as_index=False)
    .agg(ACCURACY=("ACCURACY", "mean"), RUNS=("ACCURACY", "size"))
)
by_method["COMBINATION"] = pd.Categorical(by_method["COMBINATION"], method_order, ordered=True)
by_method = by_method.sort_values("COMBINATION").dropna(subset=["COMBINATION"])
by_method["ACCURACY"] = by_method["ACCURACY"].round(2)

st.altair_chart(
    bar_with_labels(
        by_method,
        x="COMBINATION",
        y="ACCURACY",
        color="COMBINATION",
        color_domain=method_order,
        y_title="Mean accuracy (%)",
        tooltip=["COMBINATION", "ACCURACY", "RUNS"],
    ),
    use_container_width=True,
)

with st.expander("Table view"):
    st.dataframe(by_method, hide_index=True, width='stretch')

st.divider()

# -- effect of preserved passing tests ---------------------------------------

st.subheader("Effect of preserved passing tests")
st.caption(
    "ExpA through ExpD preserve 0, 10, 50 and 100 already-passing tests during "
    "repair. A conservative repair should trade peak accuracy for stability."
)

by_experiment = scoped.dropna(subset=["experiment"])
if by_experiment.empty:
    st.info("This subject has no ExpA–ExpD variants.")
else:
    grouped = (
        by_experiment.groupby(["experiment", "COMBINATION"], as_index=False)["ACCURACY"]
        .mean()
        .round(2)
    )
    grouped = grouped[grouped["COMBINATION"].isin(method_order)]

    lines = (
        alt.Chart(grouped)
        .mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=60, filled=True))
        .encode(
            x=alt.X("experiment:N", title="", sort=["ExpA", "ExpB", "ExpC", "ExpD"],
                    axis=alt.Axis(labelAngle=0)),
            y=alt.Y("ACCURACY:Q", title="Mean accuracy (%)", scale=alt.Scale(zero=False)),
            color=alt.Color("COMBINATION:N", scale=categorical_scale(method_order),
                            legend=alt.Legend(title=None, orient="top")),
            tooltip=["experiment", "COMBINATION", "ACCURACY"],
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
    st.altair_chart(lines, use_container_width=True)

    with st.expander("Table view"):
        st.dataframe(
            grouped.pivot(index="experiment", columns="COMBINATION", values="ACCURACY"),
            width='stretch',
        )

st.divider()

# -- strategy vs dataset heatmap ---------------------------------------------

st.subheader("Strategy against dataset")
st.caption(
    "Where a repair helps and where it costs. Poisoned and adversarial splits "
    "are the ones the repair targets; clean splits show the collateral damage."
)

heat_source = combination_rows[combination_rows["subject"] == subject].dropna(
    subset=["ACCURACY", "dataset"]
)
if heat_source.empty:
    st.info("No dataset breakdown available for this subject.")
else:
    heat = (
        heat_source.groupby(["dataset", "COMBINATION"], as_index=False)["ACCURACY"]
        .mean()
        .round(2)
    )
    heat = heat[heat["COMBINATION"].isin(method_order)]

    cells = (
        alt.Chart(heat)
        .mark_rect(stroke=INK["surface"], strokeWidth=2, cornerRadius=3)
        .encode(
            x=alt.X("COMBINATION:N", title="", sort=method_order, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("dataset:N", title=""),
            color=alt.Color(
                "ACCURACY:Q",
                scale=alt.Scale(range=SEQUENTIAL),
                legend=alt.Legend(title="Accuracy (%)", orient="right"),
            ),
            tooltip=["dataset", "COMBINATION", "ACCURACY"],
        )
    )
    # Direct labels: the relief the low-contrast palette slots require.
    text = cells.mark_text(fontSize=10).encode(
        text=alt.Text("ACCURACY:Q", format=".1f"),
        color=alt.condition(
            alt.datum.ACCURACY > heat["ACCURACY"].median(),
            alt.value("#ffffff"),
            alt.value(INK["primary"]),
        ),
    )

    st.altair_chart(
        (cells + text)
        .properties(height=max(200, 42 * heat["dataset"].nunique()))
        .configure_view(strokeWidth=0, fill=INK["surface"])
        .configure_axis(
            grid=False, domainColor=INK["axis"], tickColor=INK["axis"],
            labelColor=INK["secondary"], labelFontSize=11,
        )
        .configure_legend(labelColor=INK["secondary"], titleColor=INK["secondary"], labelFontSize=10),
        use_container_width=True,
    )

    with st.expander("Table view"):
        st.dataframe(
            heat.pivot(index="dataset", columns="COMBINATION", values="ACCURACY"),
            width='stretch',
        )

st.divider()

# -- raw rows ----------------------------------------------------------------

with st.expander("Raw measurements for this filter"):
    columns = [
        "stem", "layer", "experiment", "dataset", "epsilon", "selection",
        "COMBINATION", "ACCURACY", "PASS", "FAIL",
    ]
    st.dataframe(
        scoped[[c for c in columns if c in scoped.columns]].sort_values(["stem", "COMBINATION"]),
        hide_index=True,
        width='stretch',
    )
    st.download_button(
        "Download as CSV",
        scoped.to_csv(index=False).encode("utf-8"),
        file_name=f"nnrepair_{subject}_filtered.csv",
        mime="text/csv",
    )
