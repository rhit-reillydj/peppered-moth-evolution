"""
app.py — Peppered Moth Evolution Simulator

Rules for HTML in this file:
  - Only ever pass a SINGLE, self-contained HTML element to st.markdown().
  - Never embed one HTML-returning function inside another HTML string.
  - Use native Streamlit components (st.write, st.progress, st.caption,
    st.divider, st.info) for everything that doesn't need colour.
"""

import os
import sys
import pickle

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

from precompute import run_all, save, OUTPUT_PATH, SCENARIO_ORDER
from ea.scenarios import ScenarioResult
from ea.core import BARK_COLOR
from viz.charts import (
    make_fitness_chart,
    make_diversity_chart,
    make_population_timeline,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Peppered Moth Evolution",
    page_icon="🦋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  .stTabs [data-baseweb="tab"] { font-size: 15px; font-weight: 600; }
  .bio-box {
    background: #1e2d1a;
    border-left: 4px solid #8BC34A;
    border-radius: 0 8px 8px 0;
    padding: 16px 20px;
    margin: 10px 0;
    font-size: 14px;
    color: #d4e8c8;
    line-height: 1.75;
  }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_results() -> dict[str, ScenarioResult] | None:
    if not os.path.exists(OUTPUT_PATH):
        return None
    with open(OUTPUT_PATH, "rb") as f:
        return pickle.load(f)


def ensure_results() -> dict[str, ScenarioResult]:
    results = load_results()
    if results is None:
        with st.spinner("Running simulations for the first time — about 15 seconds…"):
            results = run_all()
            save(results)
        load_results.clear()
        results = load_results()
    return results


# ---------------------------------------------------------------------------
# Colour circle — the ONLY HTML helper; always called as its own st.markdown()
# ---------------------------------------------------------------------------

def colour_circle(color: tuple[int, int, int], size: int = 72, highlight: bool = False) -> None:
    """Render a filled circle in the given RGB colour. Never embed in other HTML."""
    r, g, b = color
    border = "3px solid #8BC34A" if highlight else "2px solid #3A3A3C"
    st.markdown(
        f'<div style="width:{size}px;height:{size}px;'
        f'background:rgb({r},{g},{b});border-radius:50%;'
        f'margin:0 auto 6px auto;border:{border};'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.5);"></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Overview card — pure native Streamlit components
# ---------------------------------------------------------------------------

def render_overview_card(result: ScenarioResult) -> None:
    colour_circle(result.best_final_color, size=68)
    st.markdown(f"<p style='text-align:center;font-weight:700;margin:4px 0 2px 0;'>{result.name}</p>",
                unsafe_allow_html=True)
    st.progress(result.best_final_fitness)
    st.caption(f"Best fitness: {result.best_final_fitness:.1%}")


# ---------------------------------------------------------------------------
# Deep-dive panel — one per tab
# ---------------------------------------------------------------------------

def render_deep_dive(result: ScenarioResult) -> None:

    # ── Condition label + one-line description ──────────────────────────
    st.info(f"**Hardy-Weinberg condition tested:** {result.hw_condition}")
    st.write(result.description)

    st.divider()

    # ── Moth vs. bark colour comparison ────────────────────────────────
    st.subheader("Evolved Moth vs. Target Bark")

    col_moth, col_bark, col_gap = st.columns([1, 1, 4])

    with col_moth:
        r, g, b = result.best_final_color
        colour_circle(result.best_final_color, size=90, highlight=True)
        st.caption(f"**Best moth**  \nRGB({r}, {g}, {b})")
        st.caption(f"Fitness: **{result.best_final_fitness:.1%}**")

    with col_bark:
        br, bg, bb = BARK_COLOR
        colour_circle(BARK_COLOR, size=90)
        st.caption(f"**Bark target**  \nRGB({br}, {bg}, {bb})")

    st.divider()

    # ── Fitness and diversity charts ────────────────────────────────────
    st.subheader("Population Statistics Over 150 Generations")

    col_fit, col_div = st.columns(2)
    with col_fit:
        st.plotly_chart(
            make_fitness_chart(result),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with col_div:
        st.plotly_chart(
            make_diversity_chart(result),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # ── Population timeline (optional detail) ───────────────────────────
    with st.expander("Show population colour timeline (all moths across every generation)"):
        st.caption(
            "Each row is one generation (top = gen 0, bottom = gen 150). "
            "Each column is one moth, sorted brightest to darkest. "
            "Cell colour = that moth's actual body colour."
        )
        st.plotly_chart(
            make_population_timeline(result),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.divider()

    # ── Biology explanation ─────────────────────────────────────────────
    st.subheader("🔬 What This Means Biologically")
    st.markdown(
        f'<div class="bio-box">{result.biology_explanation}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    results = ensure_results()

    # ── Hero ───────────────────────────────────────────────────────────
    st.title("🦋 Peppered Moth Evolution Simulator")
    st.write(
        "Each moth carries a genome encoding its body colour. "
        "Moths that match the dark tree bark survive; visible ones get eaten. "
        "We run six simulations — one with all evolutionary forces active, "
        "then one for each **Hardy-Weinberg condition** — to show what "
        "happens when each evolutionary driver is removed."
    )

    with st.expander("📖  Background: Hardy-Weinberg Equilibrium"):
        st.markdown("""
Hardy and Weinberg (1908) showed that allele frequencies in a population
stay **constant** — no evolution — when all five conditions below are met.
Violate any one of them and evolution begins.

| HW Condition | Evolutionary force it removes |
|---|---|
| No mutation | No new alleles can arise |
| Infinite population | No genetic drift |
| Random mating | No sexual / mate-choice selection |
| No gene flow | No migration in or out |
| No natural selection | No differential survival |

Each tab below enforces one condition while leaving the rest active,
so you can isolate exactly what each force contributes.
        """)

    st.divider()

    # ── Overview — 2 rows of 3 ─────────────────────────────────────────
    st.header("All Six Scenarios at a Glance")

    # Bark reference
    bark_col, _ = st.columns([1, 5])
    with bark_col:
        br, bg, bb = BARK_COLOR
        colour_circle(BARK_COLOR, size=32)
        st.caption(f"Bark target: RGB({br}, {bg}, {bb})")

    st.write("")   # small spacer

    row1 = SCENARIO_ORDER[:3]
    row2 = SCENARIO_ORDER[3:]

    cols1 = st.columns(3, gap="medium")
    for col, key in zip(cols1, row1):
        with col:
            render_overview_card(results[key])

    st.write("")
    cols2 = st.columns(3, gap="medium")
    for col, key in zip(cols2, row2):
        with col:
            render_overview_card(results[key])

    st.divider()

    # ── Deep-dive tabs ─────────────────────────────────────────────────
    st.header("Deep Dive — Select a Scenario")
    st.caption("Click any tab to explore that scenario's results in detail.")

    tab_labels = [results[k].name for k in SCENARIO_ORDER]
    tabs = st.tabs(tab_labels)

    for tab, key in zip(tabs, SCENARIO_ORDER):
        with tab:
            render_deep_dive(results[key])


if __name__ == "__main__":
    main()
