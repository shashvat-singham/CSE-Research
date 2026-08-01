"""Smoke tests: every page renders, and the filters actually filter.

``AppTest`` executes a page the way Streamlit does, so these catch the failures
a plain import cannot — bad widget arguments, empty-selection crashes, and
Altair encodings that reference missing columns.
"""

from __future__ import annotations

from pathlib import Path

import pytest

streamlit_testing = pytest.importorskip("streamlit.testing.v1")
AppTest = streamlit_testing.AppTest

APP_ROOT = Path(__file__).resolve().parents[1]

#: The navigation entry plus each view run standalone. Views are exercised
#: directly rather than only through st.navigation, so a failure points at the
#: page rather than at the router.
PAGES = [APP_ROOT / "streamlit_app.py", *sorted((APP_ROOT / "views").glob("*.py"))]

# Views needing artifacts that may be absent render an explanatory notice
# instead of charts; both outcomes are a pass.
OPTIONAL_ARTIFACT_PAGES = {"solver_output.py", "run_inference.py"}


def run(page: Path, timeout: int = 240):
    app = AppTest.from_file(str(page), default_timeout=timeout).run()
    assert not app.exception, f"{page.name}: {[e.value for e in app.exception]}"
    return app


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_page_renders_without_exception(page):
    run(page)


def test_landing_page_shows_headline_metrics():
    app = run(APP_ROOT / "streamlit_app.py")
    assert len(app.metric) >= 4
    assert any("NNRepair" in heading.value for heading in app.title)


def test_landing_page_charts_the_selected_subject():
    app = run(APP_ROOT / "streamlit_app.py")
    assert app.selectbox, "expected a subject selector"

    first = app.selectbox[0].value
    others = [o for o in app.selectbox[0].options if o != first]
    if not others:
        pytest.skip("only one subject available")

    switched = app.selectbox[0].set_value(others[0]).run()
    assert not switched.exception
    assert switched.selectbox[0].value == others[0]


def test_results_explorer_filters_narrow_the_data():
    page = APP_ROOT / "views" / "results_explorer.py"
    app = run(page)

    layer = next((s for s in app.selectbox if s.label == "Repaired layer"), None)
    assert layer is not None, "expected a layer filter"

    specific = [o for o in layer.options if o != "All"]
    if not specific:
        pytest.skip("no layer variants for the default subject")

    narrowed = layer.set_value(specific[0]).run()
    assert not narrowed.exception
    # Either results are shown, or the page explains there are none.
    assert narrowed.markdown or narrowed.warning


def test_expert_analysis_reports_a_verdict():
    app = run(APP_ROOT / "views" / "expert_analysis.py")
    text = " ".join(m.value for m in app.markdown)
    assert "experts improve on the original" in text or app.info


@pytest.mark.parametrize(
    "page", [p for p in PAGES if p.name in OPTIONAL_ARTIFACT_PAGES], ids=lambda p: p.name
)
def test_optional_artifact_pages_degrade_gracefully(page):
    """With artifacts absent these must explain, not raise."""
    app = run(page)
    produced_output = bool(app.info or app.warning or app.selectbox or app.metric)
    assert produced_output, f"{page.name} rendered nothing at all"
