"""NNRepair — application entry point.

Declares the navigation explicitly with ``st.navigation`` rather than relying
on a ``pages/`` directory. Auto-discovery derives each sidebar label from its
filename, which would name the first entry after this file; naming the pages
here keeps the sidebar readable and independent of how the files are laid out
on disk.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="NNRepair",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = [
    st.Page("views/overview.py", title="NNRepair", icon="🔧", default=True),
    st.Page("views/results_explorer.py", title="Results Explorer", icon="📊"),
    st.Page("views/expert_analysis.py", title="Expert Analysis", icon="🎯"),
    st.Page("views/solver_output.py", title="Solver Output", icon="🧮"),
    st.Page("views/run_inference.py", title="Run Inference", icon="⚙️"),
]

st.navigation(PAGES).run()
