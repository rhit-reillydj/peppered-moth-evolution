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
    # Re-compute if the file is missing OR if any expected scenario key is absent
    # (handles stale cached pickles after new scenarios are added)
    if results is None or not all(k in results for k in SCENARIO_ORDER):
        with st.spinner("Running simulations — about 15 seconds…"):
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

    with st.expander("🧬  How the Simulation Works — A Biologist's Guide"):
        st.markdown("""
This simulation is called an **Evolutionary Algorithm (EA)** — a computer
program that mimics the core mechanics of natural selection to solve problems.
Here's every piece of it explained in biological terms.
        """)

        st.markdown("---")

        st.markdown("#### 🦋  The Population")
        st.markdown("""
We start with a **population of 100 digital moths**. Just like a real peppered
moth population, these individuals vary in appearance and compete for survival
in the same environment — a dark, soot-covered tree trunk.

Each moth exists only as a string of genetic information. We never simulate
behaviour, movement, or physiology. The only thing that matters is **colour**,
because colour determines survival.
        """)

        st.markdown("#### 🧬  The Genome")
        st.markdown("""
Each moth carries a **genome of exactly 24 bits** — a sequence of zeros and
ones, like a simplified chromosome. The genome is divided into three equal
segments of 8 bits each:

- **Bits 1–8** encode the moth's *red* pigment intensity (0–255)
- **Bits 9–16** encode *green* pigment intensity (0–255)
- **Bits 17–24** encode *blue* pigment intensity (0–255)

Together these three values produce the moth's body colour — its **phenotype**.
A genome of all zeros produces a jet-black moth; a genome of all ones produces
a pure-white moth. Every shade in between is possible.

Think of it like a real organism where a handful of loci on three separate
chromosomes interact to produce coat colour — except here we've stripped it
down to the simplest possible version so we can watch evolution unfold clearly.
        """)

        st.markdown("#### 🎯  Fitness")
        st.markdown("""
The environment is a dark tree trunk with a specific target colour:
**RGB (40, 40, 40)** — a deep, sooty grey. Predators (birds) scan the bark and
eat any moth that stands out visually.

A moth's **fitness** is how closely its colour matches the bark. We measure the
straight-line distance between the moth's colour and the bark colour in
three-dimensional colour space (red, green, blue axes). A moth whose colour is
identical to the bark has **fitness = 100%**. A pure-white moth on dark bark
has fitness close to **0%**.

> **Fitness = 1 ÷ (1 + colour distance from bark)**

A moth identical to the bark has distance = 0, so fitness = 1 ÷ 1 = **100%**. A pure-white moth has a large distance, so fitness collapses toward 0%.

This is directly analogous to camouflage fitness in the real peppered moth
(*Biston betularia*) story: well-camouflaged moths survive; conspicuous moths
are eaten before they can reproduce.
        """)

        st.markdown("#### 🏆  Selection — Survival of the Fittest")
        st.markdown("""
To choose which moths get to reproduce, we use **tournament selection**, which
mirrors predation in a patchy environment:

1. Pick **3 moths at random** from the population (a small "encounter group")
2. The **best-camouflaged** of those 3 wins the tournament and is selected as a parent
3. Repeat to choose a second parent

This means fit individuals are *more likely* — but not guaranteed — to
reproduce, exactly as in nature. A slightly less-fit moth can still breed if
the random draw happens not to include its better-camouflaged rivals. Fitness
is probabilistic, not deterministic.
        """)

        st.markdown("#### 💑  Mating — Crossover (Recombination)")
        st.markdown("""
Once two parent moths are selected, they **mate** to produce an offspring. We
simulate **single-point crossover**, which is analogous to chromosomal
recombination during meiosis:

1. A random position along the 24-bit genome is chosen as the **crossover point**
2. The offspring inherits the **first segment** of its genome from Parent A
3. The offspring inherits the **second segment** from Parent B

For example, if the crossover point is at position 10:

| | Bits 1–10 | Bits 11–24 |
|---|---|---|
| **Parent A** | `0110 1001 10` | `10 1101 1010 1100` |
| **Parent B** | `1001 0011 01` | `00 1010 0101 0011` |
| **Offspring** | `0110 1001 10` *(from A)* | `00 1010 0101 0011` *(from B)* |

The offspring gets a **mixture of both parents' colour genetics** — just as
a real moth chick inherits a blend of melanin-production alleles from both
parents. This shuffles existing variation into new combinations every generation.
        """)

        st.markdown("#### ☢️  Mutation")
        st.markdown("""
After crossover, each bit in the offspring's genome has a **2% chance of
flipping** (0 → 1, or 1 → 0). This is the computational equivalent of a
**point mutation** — a spontaneous change at a single nucleotide position.

Mutation is the *only source of genuinely new information* in the system. Without
it, the simulation can only rearrange alleles already present in the founding
population. With it, novel colour variants can appear that were never present
in any ancestor — exactly as new pigmentation alleles arise in real populations
through mutation.

A 2% per-bit rate means that, on average, about **half a bit flips per
offspring**, producing a very slight colour shift. Occasionally a cluster of
mutations will cause a dramatic colour jump — the equivalent of a large-effect
mutation in a real organism.
        """)

        st.markdown("#### 🔄  Generations")
        st.markdown("""
We run the simulation for **150 generations**. Each generation works like this:

1. **Evaluate** every moth's camouflage fitness against the bark
2. **Select** parent pairs using tournament selection
3. **Mate** each pair (crossover) to produce offspring
4. **Mutate** each offspring's genome at 2% per bit
5. **Elitism** — the single best-camouflaged moth is copied unchanged into the
   next generation (so we never accidentally lose the best individual found so far)
6. **Replace** the old population with the new offspring

After 150 of these cycles, the population has had ample opportunity to adapt.
We then record the best individual from the final generation as the
**"winning" moth** for that scenario.

---
*The six scenarios below each modify one of these mechanics to test what happens
when a Hardy-Weinberg condition is enforced — removing one evolutionary driver
at a time.*
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

    # Row 1: the six individual-condition scenarios
    row1 = SCENARIO_ORDER[:3]
    row2 = SCENARIO_ORDER[3:6]

    cols1 = st.columns(3, gap="medium")
    for col, key in zip(cols1, row1):
        with col:
            render_overview_card(results[key])

    st.write("")
    cols2 = st.columns(3, gap="medium")
    for col, key in zip(cols2, row2):
        with col:
            render_overview_card(results[key])

    # Row 3: the "all conditions" scenario — centred, full-width highlight
    st.write("")
    st.markdown("**All Five Conditions Enforced Simultaneously ↓**")
    col_all, col_gap = st.columns([1, 2])
    with col_all:
        render_overview_card(results["all_conditions"])

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
