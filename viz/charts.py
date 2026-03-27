"""
viz/charts.py

All visualisation helpers for the Streamlit app.
Returns Plotly figures or plain HTML strings — never imports Streamlit directly.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import plotly.graph_objects as go
import plotly.express as px

if TYPE_CHECKING:
    from ea.scenarios import ScenarioResult

# ---------------------------------------------------------------------------
# Colour palette used across all charts
# ---------------------------------------------------------------------------

BARK_COLOR = (40, 40, 40)

_BG       = "#1C1C1E"
_BG2      = "#2C2C2E"
_TEXT     = "#F5F5F5"
_GRID     = "#3A3A3C"
_GREEN    = "#8BC34A"
_YELLOW   = "#FFD54F"
_RED      = "#EF5350"
_BLUE     = "#42A5F5"
_PURPLE   = "#AB47BC"

_LAYOUT_BASE = dict(
    paper_bgcolor=_BG,
    plot_bgcolor=_BG2,
    font=dict(color=_TEXT, family="sans-serif", size=13),
    margin=dict(l=50, r=20, t=50, b=50),
)

_AXIS_STYLE = dict(gridcolor=_GRID, zerolinecolor=_GRID)


# ---------------------------------------------------------------------------
# HTML colour helpers
# ---------------------------------------------------------------------------

def rgb_to_css(color: tuple[int, int, int]) -> str:
    return f"rgb({color[0]},{color[1]},{color[2]})"


def moth_swatch_html(
    color: tuple[int, int, int],
    size: int = 90,
    label: str = "",
    border: bool = False,
) -> str:
    """
    Return an HTML string rendering a filled circle of the given colour.
    Optionally adds a label below.
    """
    css_color = rgb_to_css(color)
    border_style = f"border: 3px solid {_GREEN};" if border else ""
    html = f"""
    <div style="text-align:center;">
      <div style="
        width:{size}px; height:{size}px;
        background-color:{css_color};
        border-radius:50%;
        margin:auto;
        {border_style}
        box-shadow: 0 0 12px rgba(0,0,0,0.6);
      "></div>
      {"<p style='margin-top:6px; font-size:12px; color:#aaa;'>" + label + "</p>" if label else ""}
    </div>
    """
    return html


def bark_swatch_html(size: int = 40) -> str:
    """Small swatch showing the bark target colour."""
    return moth_swatch_html(BARK_COLOR, size=size, label="Bark target")


def fitness_bar_html(fitness: float) -> str:
    """
    A horizontal progress bar coloured red → yellow → green based on fitness.
    fitness is expected in [0, 1].
    """
    pct = int(fitness * 100)
    if fitness >= 0.75:
        bar_color = _GREEN
    elif fitness >= 0.45:
        bar_color = _YELLOW
    else:
        bar_color = _RED

    return f"""
    <div style="background:#3A3A3C; border-radius:4px; height:10px; width:100%; margin:6px 0;">
      <div style="
        width:{pct}%;
        height:10px;
        background:{bar_color};
        border-radius:4px;
        transition: width 0.3s ease;
      "></div>
    </div>
    <p style="margin:0; font-size:13px; color:#aaa; text-align:center;">
      Fitness: <strong style="color:{_TEXT};">{fitness:.2%}</strong>
    </p>
    """


# ---------------------------------------------------------------------------
# Fitness over generations chart
# ---------------------------------------------------------------------------

def make_fitness_chart(result: "ScenarioResult") -> go.Figure:
    """
    Line chart showing max, average, and min fitness over all generations.
    Shaded area between max and min shows the spread of the population.
    """
    gens  = [s.generation for s in result.generations]
    maxes = [s.max_fitness for s in result.generations]
    avgs  = [s.avg_fitness for s in result.generations]
    mins  = [s.min_fitness for s in result.generations]

    fig = go.Figure()

    # Shaded band between min and max
    fig.add_trace(go.Scatter(
        x=gens + gens[::-1],
        y=maxes + mins[::-1],
        fill="toself",
        fillcolor="rgba(139,195,74,0.12)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        showlegend=False,
        name="Range",
    ))

    # Min fitness
    fig.add_trace(go.Scatter(
        x=gens, y=mins,
        mode="lines",
        line=dict(color=_RED, width=1.5, dash="dot"),
        name="Min fitness",
    ))

    # Avg fitness
    fig.add_trace(go.Scatter(
        x=gens, y=avgs,
        mode="lines",
        line=dict(color=_YELLOW, width=2),
        name="Avg fitness",
    ))

    # Max fitness
    fig.add_trace(go.Scatter(
        x=gens, y=maxes,
        mode="lines",
        line=dict(color=_GREEN, width=2.5),
        name="Max fitness",
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="Fitness Over Generations", font=dict(size=15)),
        xaxis=dict(title="Generation", **_AXIS_STYLE),
        yaxis=dict(title="Fitness (0 = no camouflage, 1 = perfect)", range=[0, 1.05], **_AXIS_STYLE),
        legend=dict(
            bgcolor="rgba(0,0,0,0.3)",
            bordercolor=_GRID,
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
    )
    return fig


# ---------------------------------------------------------------------------
# Diversity over generations chart
# ---------------------------------------------------------------------------

def make_diversity_chart(result: "ScenarioResult") -> go.Figure:
    """
    Line chart showing population colour diversity over all generations.
    Higher diversity = more colour variety in the gene pool.
    """
    gens  = [s.generation for s in result.generations]
    divs  = [s.diversity  for s in result.generations]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=gens, y=divs,
        mode="lines",
        fill="tozeroy",
        fillcolor="rgba(66,165,245,0.15)",
        line=dict(color=_BLUE, width=2.5),
        name="Diversity",
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text="Genetic Diversity Over Generations", font=dict(size=15)),
        xaxis=dict(title="Generation", **_AXIS_STYLE),
        yaxis=dict(title="Colour diversity (avg std dev across RGB)", **_AXIS_STYLE),
        legend=dict(bgcolor="rgba(0,0,0,0.3)"),
        hovermode="x unified",
    )
    return fig


# ---------------------------------------------------------------------------
# Population timeline — the "painting"
# ---------------------------------------------------------------------------

def make_population_timeline(result: "ScenarioResult") -> go.Figure:
    """
    Heatmap where:
      - Y-axis = generation (0 at top)
      - X-axis = individual index (sorted by fitness within each generation)
      - Cell colour = that moth's actual RGB colour

    The result looks like a painting that shows how the colour distribution
    shifts (or doesn't) over time.

    We sample every N-th generation so the image stays readable without
    being enormous.
    """
    # Sample at most 60 generations for display (keep rendering fast)
    all_snaps = result.generations
    total = len(all_snaps)
    step  = max(1, total // 60)
    snaps = all_snaps[::step]

    # Build the colour matrix: rows = generations, cols = individuals
    # Each cell is encoded as an RGBA integer for Plotly
    z_rgb: list[list[str]] = []          # HTML colour strings
    hover: list[list[str]] = []

    for snap in snaps:
        # Sort individuals by fitness (lightest first → darkest last)
        colors_sorted = sorted(
            snap.population_colors,
            key=lambda c: (c[0] + c[1] + c[2]),   # brightest first
            reverse=True,
        )
        row_colors = [rgb_to_css(c) for c in colors_sorted]
        row_hover  = [
            f"Gen {snap.generation}<br>RGB({c[0]},{c[1]},{c[2]})"
            for c in colors_sorted
        ]
        z_rgb.append(row_colors)
        hover.append(row_hover)

    # Plotly doesn't natively support per-cell custom colours in a heatmap,
    # so we build it as a scatter heatmap using a 2D image trace.
    # The cleanest approach: encode colours as a flat image using go.Image.
    import numpy as np

    n_rows = len(snaps)
    n_cols = len(snaps[0].population_colors)

    img = np.zeros((n_rows, n_cols, 3), dtype=np.uint8)
    y_labels = []

    for row_i, snap in enumerate(snaps):
        colors_sorted = sorted(
            snap.population_colors,
            key=lambda c: (c[0] + c[1] + c[2]),
            reverse=True,
        )
        for col_i, color in enumerate(colors_sorted):
            img[row_i, col_i] = color
        y_labels.append(snap.generation)

    fig = go.Figure(go.Image(z=img))

    # Overlay y-axis tick labels (generation numbers)
    tick_step = max(1, n_rows // 8)
    tick_vals = list(range(0, n_rows, tick_step))
    tick_text = [str(y_labels[i]) for i in tick_vals]

    timeline_layout = {k: v for k, v in _LAYOUT_BASE.items() if k != "margin"}
    fig.update_layout(
        **timeline_layout,
        title=dict(
            text="Population Colour Evolution  (top = generation 0, bottom = final)",
            font=dict(size=15),
        ),
        xaxis=dict(
            title="Individual moths (brightest → darkest, left → right)",
            showticklabels=False,
            gridcolor="rgba(0,0,0,0)",
            zerolinecolor="rgba(0,0,0,0)",
        ),
        yaxis=dict(
            title="Generation",
            tickmode="array",
            tickvals=tick_vals,
            ticktext=tick_text,
            gridcolor="rgba(0,0,0,0)",
            zerolinecolor="rgba(0,0,0,0)",
            autorange="reversed",
        ),
        margin=dict(l=60, r=20, t=60, b=60),
    )
    return fig


# ---------------------------------------------------------------------------
# Comparison bar chart (all 6 scenarios side by side)
# ---------------------------------------------------------------------------

_SCENARIO_ORDER = [
    "normal",
    "no_mutation",
    "small_pool",
    "random_mating",
    "no_migration",
    "equal_reproduction",
]


def make_comparison_bar(results: dict) -> go.Figure:
    """
    Horizontal bar chart comparing the final best fitness of all 6 scenarios.
    """
    names    = [results[k].name               for k in _SCENARIO_ORDER if k in results]
    fitnesses= [results[k].best_final_fitness  for k in _SCENARIO_ORDER if k in results]

    colors = [
        _GREEN if f >= 0.75 else (_YELLOW if f >= 0.45 else _RED)
        for f in fitnesses
    ]

    fig = go.Figure(go.Bar(
        x=fitnesses,
        y=names,
        orientation="h",
        marker_color=colors,
        text=[f"{f:.1%}" for f in fitnesses],
        textposition="outside",
        cliponaxis=False,
    ))

    bar_layout = {k: v for k, v in _LAYOUT_BASE.items() if k != "margin"}
    fig.update_layout(
        **bar_layout,
        title=dict(text="Final Best Fitness — All Scenarios", font=dict(size=15)),
        xaxis=dict(title="Best fitness achieved", range=[0, 1.15], **_AXIS_STYLE),
        yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)", zerolinecolor="rgba(0,0,0,0)"),
        showlegend=False,
        margin=dict(l=160, r=60, t=60, b=50),
    )
    return fig
