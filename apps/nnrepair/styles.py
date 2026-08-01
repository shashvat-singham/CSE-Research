"""Visual design for the app.

Streamlit's defaults read as a prototype: oversized headings, rounded pill
buttons, heavy shadows, wide gutters. This module replaces that with the
conventions of a technical document — a tight type scale, hairline rules
instead of cards, tabular figures for anything numeric, and colour reserved for
the one or two things that carry meaning.

The palette matches ``theme.py``, which is validated for colour-vision
deficiency against the light surface, so the chrome and the charts stay one
system.
"""

from __future__ import annotations

import streamlit as st

__all__ = ["apply", "page_header", "metric_row", "section"]

_CSS = """
<style>
/* ---------------------------------------------------------------------------
   Type scale. Streamlit's default h1 is 2.75rem, which reads as a landing
   page. Research tooling wants headings that separate sections without
   shouting.
   --------------------------------------------------------------------------- */
html, body, [class*="st-"] {
  font-feature-settings: "kern" 1, "liga" 1;
}

.block-container {
  padding-top: 2.5rem;
  padding-bottom: 4rem;
  max-width: 1180px;
}

h1, h2, h3, h4 {
  font-weight: 600 !important;
  letter-spacing: -0.011em;
  color: var(--nn-ink);
}
h1 { font-size: 1.6rem !important; line-height: 1.25 !important; margin-bottom: 0.15rem !important; }
h2 { font-size: 1.12rem !important; margin-top: 2.2rem !important; margin-bottom: 0.5rem !important; }
h3 { font-size: 0.97rem !important; margin-top: 1.4rem !important; }

p, li, label, .stMarkdown { color: var(--nn-ink-2); }

/* Numbers must line up in columns. */
code, pre, .stDataFrame, [data-testid="stMetricValue"] {
  font-variant-numeric: tabular-nums;
}

code {
  font-size: 0.83em !important;
  background: var(--nn-surface-2) !important;
  border: 1px solid var(--nn-line);
  border-radius: 3px;
  padding: 0.08em 0.34em !important;
  color: var(--nn-ink) !important;
}

/* ---------------------------------------------------------------------------
   Page header: a title with a rule under it, the way a paper section opens.
   --------------------------------------------------------------------------- */
.nn-header { margin-bottom: 1.6rem; }
.nn-header .nn-eyebrow {
  font-size: 0.7rem;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--nn-muted);
  margin-bottom: 0.35rem;
}
.nn-header .nn-lede {
  font-size: 0.94rem;
  color: var(--nn-ink-2);
  max-width: 68ch;
  margin-top: 0.35rem;
}
.nn-rule {
  border: 0;
  border-top: 1px solid var(--nn-line);
  margin: 1.1rem 0 0 0;
}

/* ---------------------------------------------------------------------------
   Metrics as a specimen row: hairline separators, label above value, no card.
   --------------------------------------------------------------------------- */
.nn-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  border: 1px solid var(--nn-line);
  border-radius: 6px;
  overflow: hidden;
  margin: 0.4rem 0 0.2rem 0;
}
.nn-metric {
  flex: 1 1 0;
  min-width: 130px;
  padding: 0.7rem 0.95rem;
  border-right: 1px solid var(--nn-line);
}
.nn-metric:last-child { border-right: 0; }
.nn-metric .k {
  font-size: 0.68rem;
  letter-spacing: 0.055em;
  text-transform: uppercase;
  color: var(--nn-muted);
  white-space: nowrap;
}
.nn-metric .v {
  font-size: 1.32rem;
  font-weight: 600;
  color: var(--nn-ink);
  font-variant-numeric: tabular-nums;
  line-height: 1.25;
  margin-top: 0.12rem;
}
.nn-metric .s { font-size: 0.72rem; color: var(--nn-muted); }

/* ---------------------------------------------------------------------------
   Controls. Flat, square-ish, no shadow — they are instruments, not calls to
   action.
   --------------------------------------------------------------------------- */
.stButton > button, .stDownloadButton > button {
  border-radius: 5px !important;
  border: 1px solid var(--nn-line-strong) !important;
  box-shadow: none !important;
  font-weight: 500 !important;
  font-size: 0.86rem !important;
  padding: 0.36rem 0.85rem !important;
  transition: background-color 120ms ease, border-color 120ms ease;
}
.stButton > button[kind="primary"] {
  background: var(--nn-accent) !important;
  border-color: var(--nn-accent) !important;
  color: #fff !important;
}
.stButton > button[kind="primary"]:hover { filter: brightness(1.07); }
.stButton > button:not([kind="primary"]):hover { background: var(--nn-surface-2) !important; }

div[data-baseweb="select"] > div,
.stTextInput input,
.stNumberInput input {
  border-radius: 5px !important;
  border-color: var(--nn-line-strong) !important;
  box-shadow: none !important;
  font-size: 0.86rem !important;
}

.stSelectbox label, .stNumberInput label, .stRadio label, .stCheckbox label,
.stTextInput label, .stSlider label {
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.02em;
  color: var(--nn-ink-2) !important;
}

/* ---------------------------------------------------------------------------
   Tables and charts sit inside hairline frames, not shadowed cards.
   --------------------------------------------------------------------------- */
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border: 1px solid var(--nn-line);
  border-radius: 6px;
}
[data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] {
  border: 1px solid var(--nn-line);
  border-radius: 6px;
  padding: 0.6rem 0.4rem 0.2rem 0.4rem;
  background: var(--nn-surface);
}

/* Callouts: a left rule rather than a filled block. */
[data-testid="stAlert"] {
  border-radius: 0 5px 5px 0 !important;
  border-left-width: 3px !important;
  font-size: 0.86rem;
  padding: 0.65rem 0.9rem !important;
}

details > summary { font-size: 0.85rem; color: var(--nn-ink-2); }
[data-testid="stCaptionContainer"], .stCaption {
  font-size: 0.78rem !important;
  color: var(--nn-muted) !important;
}

hr { margin: 1.9rem 0 !important; border-color: var(--nn-line) !important; }

/* ---------------------------------------------------------------------------
   Sidebar: a table of contents.
   --------------------------------------------------------------------------- */
section[data-testid="stSidebar"] {
  border-right: 1px solid var(--nn-line);
  background: var(--nn-surface-2);
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.6rem; }
section[data-testid="stSidebar"] a { font-size: 0.86rem !important; border-radius: 4px !important; }

/* Streamlit's own chrome adds nothing here. */
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; }
[data-testid="stToolbar"] { right: 0.6rem; }
</style>
"""

# Declared separately so the tokens can be read by name above.
_TOKENS = """
<style>
:root {
  --nn-surface:      #fcfcfb;
  --nn-surface-2:    #f5f5f2;
  --nn-ink:          #0b0b0b;
  --nn-ink-2:        #52514e;
  --nn-muted:        #898781;
  --nn-line:         #e1e0d9;
  --nn-line-strong:  #c9c8c0;
  --nn-accent:       #2a78d6;
}
</style>
"""


def apply() -> None:
    """Install the stylesheet. Call once, from the entry point."""
    st.markdown(_TOKENS + _CSS, unsafe_allow_html=True)


def page_header(title: str, lede: str = "", eyebrow: str = "") -> None:
    """Render a page title with an optional kicker and standfirst.

    Args:
        title: The page name.
        lede: One or two sentences on what the page is for.
        eyebrow: Small uppercase label above the title, for context.
    """
    parts = ['<div class="nn-header">']
    if eyebrow:
        parts.append(f'<div class="nn-eyebrow">{eyebrow}</div>')
    parts.append(f"<h1>{title}</h1>")
    if lede:
        parts.append(f'<div class="nn-lede">{lede}</div>')
    parts.append('<hr class="nn-rule" /></div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


def metric_row(metrics: list[tuple[str, str]] | list[tuple[str, str, str]]) -> None:
    """Render figures as one hairline-separated strip.

    Args:
        metrics: ``(label, value)`` or ``(label, value, sublabel)`` tuples.
    """
    cells = []
    for metric in metrics:
        label, value = metric[0], metric[1]
        sub = metric[2] if len(metric) > 2 else ""
        sub_html = f'<div class="s">{sub}</div>' if sub else ""
        cells.append(
            f'<div class="nn-metric"><div class="k">{label}</div>'
            f'<div class="v">{value}</div>{sub_html}</div>'
        )
    st.markdown(f'<div class="nn-metrics">{"".join(cells)}</div>', unsafe_allow_html=True)


def section(title: str, note: str = "") -> None:
    """Open a section with a heading and an optional explanatory line."""
    st.markdown(f"## {title}")
    if note:
        st.caption(note)
