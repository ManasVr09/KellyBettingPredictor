"""Streamlit interface for exploring Kelly betting with binary outcomes."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator import (  # noqa: E402
    STRATEGY_NAMES,
    break_even_probability,
    expected_value_per_dollar,
    kelly_fraction,
    simulate_binary_bets,
)


st.set_page_config(
    page_title="Kelly Betting Lab",
    page_icon=":material/casino:",
    layout="wide",
)


DEFAULT_INPUTS = {
    "initial_bankroll": 1_000.0,
    "win_probability": 0.55,
    "decimal_odds": 1.91,
    "number_of_bets": 250,
    "simulations": 3_000,
    "seed": 7,
    "log_scale": True,
}


def money(value: float) -> str:
    """Format a bankroll value compactly for tables and metrics."""

    return f"${value:,.2f}"


def make_bankroll_figure(
    results: dict[str, object],
    number_of_bets: int,
    initial_bankroll: float,
    log_scale: bool,
) -> go.Figure:
    """Create a median bankroll chart with a 10th–90th percentile ribbon."""

    colors = {
        "No Kelly": ("#94a3b8", "rgba(148, 163, 184, 0.12)"),
        "Half Kelly": ("#2f80ed", "rgba(47, 128, 237, 0.12)"),
        "Full Kelly": ("#f2994a", "rgba(242, 153, 74, 0.12)"),
    }
    x = np.arange(number_of_bets + 1)
    figure = go.Figure()

    for name in STRATEGY_NAMES:
        result = results[name]
        low = result.quantiles[:, 0]
        median = result.quantiles[:, 1]
        high = result.quantiles[:, 2]
        color, fillcolor = colors[name]

        figure.add_trace(
            go.Scatter(
                x=np.concatenate([x, x[::-1]]),
                y=np.concatenate([high, low[::-1]]),
                fill="toself",
                fillcolor=fillcolor,
                line={"color": "rgba(0,0,0,0)"},
                hoverinfo="skip",
                showlegend=False,
                name=f"{name} range",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=x,
                y=median,
                mode="lines",
                name=name,
                line={"color": color, "width": 3 if name != "No Kelly" else 2},
                customdata=np.column_stack([low, high]),
                hovertemplate=(
                    f"{name}<br>Bet: %{{x:,}}<br>Median: $%{{y:,.2f}}"
                    "<br>10th–90th percentile: $%{customdata[0]:,.2f} – "
                    "$%{customdata[1]:,.2f}<extra></extra>"
                ),
            )
        )

    figure.add_hline(
        y=initial_bankroll,
        line_dash="dot",
        line_width=1,
        line_color="#64748b",
        annotation_text="Starting bankroll",
        annotation_position="top left",
    )
    figure.update_layout(
        title="Bankroll over repeated bets",
        xaxis_title="Bet number",
        yaxis_title="Bankroll ($)",
        yaxis_type="log" if log_scale else "linear",
        hovermode="x unified",
        height=540,
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    return figure


def build_summary_table(results: dict[str, object], initial_bankroll: float) -> pd.DataFrame:
    """Create the user-facing strategy comparison table."""

    rows = []
    for name in STRATEGY_NAMES:
        result = results[name]
        terminal = result.terminal_bankrolls
        rows.append(
            {
                "Strategy": name,
                "Bet fraction": f"{result.fraction:.1%}",
                "Bet on next wager": money(initial_bankroll * result.fraction),
                "10th percentile": money(float(np.percentile(terminal, 10))),
                "Median final bankroll": money(float(np.median(terminal))),
                "90th percentile": money(float(np.percentile(terminal, 90))),
                "Finish above start": f"{np.mean(terminal > initial_bankroll):.1%}",
            }
        )
    return pd.DataFrame(rows)


def build_probability_ladder(
    decimal_odds: float,
    initial_bankroll: float,
    current_probability: float,
) -> pd.DataFrame:
    """Show how the edge and stake change at probabilities below and above 50%."""

    payout_multiple = decimal_odds - 1.0
    levels = sorted(
        {
            0.25,
            0.35,
            0.40,
            0.45,
            0.50,
            0.55,
            0.60,
            0.65,
            0.70,
            round(current_probability, 2),
        }
    )
    break_even = break_even_probability(decimal_odds)
    return pd.DataFrame(
        [
            {
                "Win probability": f"{probability:.0%}",
                "Edge vs break-even": f"{probability - break_even:+.1%}",
                "Expected value per $1": f"{expected_value_per_dollar(probability, payout_multiple):+.3f}",
                "Full Kelly": f"{kelly_fraction(probability, payout_multiple):.1%}",
                "Full Kelly stake": money(initial_bankroll * kelly_fraction(probability, payout_multiple)),
            }
            for probability in levels
        ]
    )


@st.cache_data(show_spinner=False, max_entries=8)
def run_simulation(
    initial_bankroll: float,
    win_probability: float,
    decimal_odds: float,
    number_of_bets: int,
    simulations: int,
    seed: int,
    implementation_key: tuple = (),
):
    """Cache simulation output while the user explores the controls."""

    return simulate_binary_bets(
        initial_bankroll=initial_bankroll,
        win_probability=win_probability,
        decimal_odds=decimal_odds,
        number_of_bets=number_of_bets,
        simulations=simulations,
        seed=seed,
    )


def implementation_signature() -> tuple:
    return tuple((path.name, path.stat().st_mtime_ns, path.stat().st_size)
                 for path in (ROOT / "app.py", ROOT / "simulator.py"))


@st.cache_data(max_entries=8, show_spinner=False)
def render_bankroll_chart(simulation_key: tuple, number_of_bets: int, initial_bankroll: float,
                          log_scale: bool, _results) -> None:
    st.plotly_chart(make_bankroll_figure(_results, number_of_bets, initial_bankroll, log_scale))


@st.cache_data(max_entries=8, show_spinner=False)
def render_summary(simulation_key: tuple, initial_bankroll: float, _results) -> None:
    st.subheader("Strategy comparison")
    st.dataframe(build_summary_table(_results, initial_bankroll), hide_index=True)


@st.cache_data(max_entries=16, show_spinner=False)
def render_probability_ladder(implementation_key: tuple, decimal_odds: float, initial_bankroll: float, win_probability: float) -> None:
    st.subheader("Probability ladder at these odds")
    st.dataframe(build_probability_ladder(decimal_odds, initial_bankroll, win_probability), hide_index=True)


st.session_state.setdefault("simulation_inputs", DEFAULT_INPUTS.copy())

st.title("Kelly betting lab")
st.caption("How much should you bet when your probability differs from the price?")

with st.sidebar:
    st.header("Experiment controls")
    with st.form("betting_inputs"):
        initial_bankroll_input = st.number_input(
            "Starting bankroll",
            min_value=10.0,
            max_value=1_000_000.0,
            value=float(DEFAULT_INPUTS["initial_bankroll"]),
            step=100.0,
            help="The amount available before the first wager.",
        )
        win_probability_pct_input = st.slider(
            "Your estimated chance of winning",
            min_value=1.0,
            max_value=99.0,
            value=float(DEFAULT_INPUTS["win_probability"] * 100.0),
            step=1.0,
            format="%.0f%%",
            help="This can be below 50%. Favorable odds can still create a positive edge.",
        )
        decimal_odds_input = st.number_input(
            "Decimal odds",
            min_value=1.01,
            max_value=100.0,
            value=float(DEFAULT_INPUTS["decimal_odds"]),
            step=0.01,
            format="%.2f",
            help="Odds include the returned stake. 2.00 means a $1 win returns $2 total; 1.91 is roughly -110.",
        )
        number_of_bets_input = st.slider(
            "Number of bets",
            min_value=10,
            max_value=1_000,
            value=int(DEFAULT_INPUTS["number_of_bets"]),
            step=10,
        )
        simulations_input = st.slider(
            "Monte Carlo trials",
            min_value=500,
            max_value=10_000,
            value=int(DEFAULT_INPUTS["simulations"]),
            step=500,
            help="Independent bankroll histories used to estimate the outcome range.",
        )
        seed_input = st.number_input(
            "Random seed",
            min_value=0,
            max_value=999_999,
            value=int(DEFAULT_INPUTS["seed"]),
            step=1,
        )
        log_scale_input = st.checkbox(
            "Use a log bankroll axis",
            value=bool(DEFAULT_INPUTS["log_scale"]),
            help="Useful when compounding makes strategies spread far apart.",
        )
        submitted = st.form_submit_button("Run simulation", type="primary")

    if submitted:
        st.session_state.simulation_inputs = {
            "initial_bankroll": float(initial_bankroll_input),
            "win_probability": float(win_probability_pct_input) / 100.0,
            "decimal_odds": float(decimal_odds_input),
            "number_of_bets": int(number_of_bets_input),
            "simulations": int(simulations_input),
            "seed": int(seed_input),
            "log_scale": bool(log_scale_input),
        }

inputs = st.session_state.simulation_inputs
initial_bankroll = inputs["initial_bankroll"]
win_probability = inputs["win_probability"]
decimal_odds = inputs["decimal_odds"]
number_of_bets = inputs["number_of_bets"]
simulations = inputs["simulations"]
seed = inputs["seed"]
log_scale = inputs["log_scale"]

payout_multiple = decimal_odds - 1.0
break_even = break_even_probability(decimal_odds)
edge_vs_break_even = win_probability - break_even
expected_value = expected_value_per_dollar(win_probability, payout_multiple)
full_kelly = kelly_fraction(win_probability, payout_multiple)
half_kelly = full_kelly / 2.0

st.info(
    f"At {decimal_odds:.2f} decimal odds, the break-even win probability is "
    f"{break_even:.1%}. A probability below 50% can still be profitable when "
    f"it is above that threshold."
)

if edge_vs_break_even > 0.0:
    st.success(
        f"Positive edge: your {win_probability:.1%} estimate is {edge_vs_break_even:+.1%} "
        f"versus the {break_even:.1%} break-even probability."
    )
else:
    st.warning(
        f"No positive edge at these odds: your {win_probability:.1%} estimate is at or below "
        f"the {break_even:.1%} break-even probability. Kelly says bet $0; no stake size turns "
        "a negative-expected-value wager into a profitable one."
    )

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Your win probability", f"{win_probability:.1%}")
metric_2.metric("Break-even probability", f"{break_even:.1%}")
metric_3.metric("Expected value per $1", f"{expected_value:+.3f}")
metric_4.metric("Full Kelly stake", money(initial_bankroll * full_kelly))

code_signature = implementation_signature()
arguments = (initial_bankroll, win_probability, decimal_odds, number_of_bets, simulations, seed)
simulation_key = (*arguments, code_signature)
if st.session_state.get("report_key") != simulation_key:
    st.session_state["simulation_results"] = run_simulation(*arguments, implementation_key=code_signature)
    st.session_state["report_key"] = simulation_key
results = st.session_state["simulation_results"]
render_bankroll_chart(simulation_key, number_of_bets, initial_bankroll, log_scale, results)
st.caption(
    "Lines show median bankroll. Shaded bands show the 10th–90th percentile across trials; "
    "all strategies see the same outcomes."
)

render_summary(simulation_key, initial_bankroll, results)

render_probability_ladder(code_signature, decimal_odds, initial_bankroll, win_probability)

st.subheader("The sizing rule")
st.latex(r"f^* = \frac{bp-q}{b}, \qquad b = O-1, \qquad q=1-p")
st.markdown(
    "Here **p** is your estimated win probability, **O** is decimal odds, and **b** is the net profit "
    "on a $1 stake. Half Kelly uses half of **f·**; No Kelly uses 0%. Kelly is floored at zero when "
    "your estimate does not clear the break-even probability."
)

details = st.expander("Assumptions and caveats", on_change="rerun", key="simulation_assumptions")
if details.open:
    with details:
        st.markdown(
            """
            - Every wager is independent and has the same modeled win probability.
            - Decimal odds stay constant across the simulation; the model does not include changing lines.
            - The break-even probability is `1 / decimal odds`. Sportsbook margin, fees, taxes, limits, and slippage are not modeled separately.
            - The probability estimate is treated as known. In real betting, estimation error is often the biggest risk.
            - Kelly maximizes long-run growth of log wealth; it does not maximize the chance of being ahead after a short run.
            """
        )
st.warning("Illustrative simulation only — never risk money you cannot afford to lose.")
