"""Inspect the Z3 models that define each repair."""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import styles

from app_data import Z3_ROOT, bundled_subset_note, have_z3_solutions, missing_artifact_note
from nnrepair.z3_solutions import parse_z3_model
from theme import INK, SERIES, bar_with_labels


styles.page_header(
    'Solver output',
    'Each repair is a satisfying assignment from Z3. This page decodes those models into the weight deltas they represent.',
    eyebrow='Artifacts',
)

if not have_z3_solutions():
    missing_artifact_note("Z3 solutions", Z3_ROOT)
    st.stop()

bundled_subset_note()


@st.cache_data(show_spinner=False)
def solution_tree() -> pd.DataFrame:
    """Index every solution file by subject, layer and experiment."""
    rows = []
    for path in sorted(Z3_ROOT.rglob("*.txt")):
        relative = path.relative_to(Z3_ROOT).parts
        if len(relative) < 4:
            continue
        rows.append(
            {
                "subject": relative[0],
                "layer": relative[1],
                "experiment": relative[2],
                "file": path.stem,
                "path": str(path),
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(show_spinner="Parsing solver model…")
def deltas_for(path: str) -> pd.DataFrame:
    """Decode one solution file into a tidy delta table."""
    bindings = parse_z3_model(path)
    rows = []
    for name, value in bindings.items():
        if not name.startswith("sym"):
            continue
        indices = name[3:].split("_")
        rows.append(
            {
                "variable": name,
                "out_index": int(indices[0]) if len(indices) > 1 else None,
                "in_index": int(indices[-1]),
                "delta": value,
            }
        )
    return pd.DataFrame(rows)


tree = solution_tree()
if tree.empty:
    st.warning("No solution files found under `Z3Solutions/`.")
    st.stop()

picker = st.columns(4)
subject = picker[0].selectbox("Subject", sorted(tree["subject"].unique()))
scoped = tree[tree["subject"] == subject]

layer = picker[1].selectbox("Repaired layer", sorted(scoped["layer"].unique()))
scoped = scoped[scoped["layer"] == layer]

experiment = picker[2].selectbox("Experiment", sorted(scoped["experiment"].unique()))
scoped = scoped[scoped["experiment"] == experiment]

solution_file = picker[3].selectbox("Solution", sorted(scoped["file"].unique()))
selected = scoped[scoped["file"] == solution_file].iloc[0]

st.divider()

deltas = deltas_for(selected["path"])
if deltas.empty:
    st.warning("This model binds no `sym` variables.")
    st.stop()

nonzero = deltas[deltas["delta"] != 0.0]

# -- headline: how surgical is this repair? ----------------------------------

metrics = st.columns(4)
metrics[0].metric("Weights in scope", f"{len(deltas):,}")
metrics[1].metric("Weights changed", f"{len(nonzero):,}")
metrics[2].metric(
    "Changed", f"{100 * len(nonzero) / len(deltas):.1f}%" if len(deltas) else "—"
)
metrics[3].metric(
    "Largest change", f"{nonzero['delta'].abs().max():.4f}" if not nonzero.empty else "0"
)

st.markdown(
    "A repair is meant to be **surgical** — the solver is asked for a satisfying "
    "assignment, and most candidate weights come back untouched at zero. The "
    "changed fraction above is the honest measure of how invasive this repair is."
)

st.divider()

# -- distribution of the non-zero deltas -------------------------------------

st.subheader("Distribution of applied deltas")

if nonzero.empty:
    st.info("Every weight in this model is zero — the solver found the network already satisfies its constraints.")
else:
    histogram = (
        alt.Chart(nonzero)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=SERIES[0])
        .encode(
            x=alt.X("delta:Q", bin=alt.Bin(maxbins=40), title="Weight delta"),
            y=alt.Y("count():Q", title="Weights"),
            tooltip=[alt.Tooltip("count():Q", title="Weights")],
        )
        .properties(height=300)
        .configure_view(strokeWidth=0, fill=INK["surface"])
        .configure_axis(
            gridColor=INK["grid"], domainColor=INK["axis"], tickColor=INK["axis"],
            labelColor=INK["secondary"], titleColor=INK["secondary"],
            labelFontSize=11, titleFontSize=11, titleFontWeight="normal",
        )
    )
    st.altair_chart(histogram, use_container_width=True)

    stats = pd.DataFrame(
        {
            "Statistic": ["Minimum", "Median", "Maximum", "Mean absolute"],
            "Value": [
                nonzero["delta"].min(),
                nonzero["delta"].median(),
                nonzero["delta"].max(),
                nonzero["delta"].abs().mean(),
            ],
        }
    ).round(6)
    with st.expander("Table view"):
        st.dataframe(stats, hide_index=True, width='stretch')

st.divider()

# -- comparing all experts in this experiment --------------------------------

st.subheader("How the ten experts compare")
st.caption("Non-zero weights per expert, within this experiment.")


@st.cache_data(show_spinner="Parsing all experts…")
def experiment_summary(paths: tuple[tuple[str, str], ...]) -> pd.DataFrame:
    rows = []
    for name, path in paths:
        frame = deltas_for(path)
        rows.append(
            {
                "Expert": name,
                "Changed": int((frame["delta"] != 0.0).sum()),
                "In scope": len(frame),
                "Max |delta|": float(frame["delta"].abs().max()) if not frame.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


paths = tuple((row["file"], row["path"]) for _, row in scoped.sort_values("file").iterrows())
summary = experiment_summary(paths)

st.altair_chart(
    bar_with_labels(
        summary,
        x="Expert",
        y="Changed",
        y_title="Non-zero weight deltas",
        label_format="d",
        tooltip=["Expert", "Changed", "In scope", "Max |delta|"],
    ),
    use_container_width=True,
)

with st.expander("Table view"):
    st.dataframe(summary.round(6), hide_index=True, width='stretch')

st.divider()

# -- raw model ---------------------------------------------------------------

with st.expander(f"Decoded variables — {solution_file}"):
    st.dataframe(
        deltas.sort_values("delta", key=lambda s: s.abs(), ascending=False).round(8),
        hide_index=True,
        width='stretch',
    )
    st.download_button(
        "Download decoded deltas",
        deltas.to_csv(index=False).encode("utf-8"),
        file_name=f"{solution_file}_deltas.csv",
        mime="text/csv",
    )

with st.expander("Raw solver output"):
    text = open(selected["path"], encoding="utf-8", errors="replace").read()
    st.code(text[:20000] + ("\n… truncated …" if len(text) > 20000 else ""), language="lisp")
