"""Kelly criterion binary-betting simulator."""

from .simulator import (
    STRATEGY_NAMES,
    StrategyResult,
    break_even_probability,
    expected_value_per_dollar,
    kelly_fraction,
    simulate_binary_bets,
    strategy_fractions,
)

__all__ = [
    "STRATEGY_NAMES",
    "StrategyResult",
    "break_even_probability",
    "expected_value_per_dollar",
    "kelly_fraction",
    "simulate_binary_bets",
    "strategy_fractions",
]
