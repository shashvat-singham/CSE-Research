"""NNRepair — application entry point.

Declares the navigation explicitly with ``st.navigation`` rather than relying
on a ``pages/`` directory. Auto-discovery derives each sidebar label from its
filename, which would name the first entry after this file; naming the pages
here keeps the sidebar readable and independent of how the files are laid out
on disk.
"""

from __future__ import annotations

import streamlit as st

import styles

st.set_page_config(
    page_title="NNRepair",
    layout="wide",
    initial_sidebar_state="expanded",
)

styles.apply()

# No icons: the sidebar reads as a contents list, and emoji beside every entry
# undercuts that.
PAGES = [
    st.Page("views/overview.py", title="Overview", default=True),
    st.Page("views/results_explorer.py", title="Results"),
    st.Page("views/expert_analysis.py", title="Experts"),
    st.Page("views/solver_output.py", title="Solver output"),
    st.Page("views/run_inference.py", title="Inference"),
]

with st.sidebar:
    st.markdown(
        "<div style='font-weight:600;font-size:0.95rem;letter-spacing:-0.01em'>NNRepair</div>"
        "<div style='font-size:0.74rem;color:#898781;margin-bottom:0.6rem'>"
        "Constraint-based repair of<br>neural network classifiers</div>",
        unsafe_allow_html=True,
    )

st.navigation(PAGES).run()
