"""Core calculations for the Kelly criterion binary-betting simulator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


STRATEGY_NAMES = ("No Kelly", "Half Kelly", "Full Kelly")


@dataclass(frozen=True)
class StrategyResult:
    """Simulation output for one betting strategy."""

    name: str
    fraction: float
    quantiles: np.ndarray
    sample_paths: np.ndarray
    terminal_bankrolls: np.ndarray


def _validate_probability(win_probability: float) -> None:
    if not 0.0 <= win_probability <= 1.0:
        raise ValueError("win_probability must be between 0 and 1")


def _validate_payout_multiple(payout_multiple: float) -> None:
    if payout_multiple <= 0.0:
        raise ValueError("payout_multiple must be positive")


def break_even_probability(decimal_odds: float) -> float:
    """Return the win probability required to break even at decimal odds."""

    if decimal_odds <= 1.0:
        raise ValueError("decimal_odds must be greater than 1")
    return 1.0 / float(decimal_odds)


def expected_value_per_dollar(win_probability: float, payout_multiple: float = 1.0) -> float:
    """Return expected profit per dollar staked on a binary wager."""

    _validate_probability(win_probability)
    _validate_payout_multiple(payout_multiple)
    lose_probability = 1.0 - win_probability
    return float(win_probability * payout_multiple - lose_probability)


def kelly_fraction(win_probability: float, payout_multiple: float = 1.0) -> float:
    """Return the non-negative Kelly fraction for a binary wager.

    ``payout_multiple`` is the net profit paid for each dollar wagered when
    the bet wins. For decimal odds ``O``, use ``O - 1``. When the calculated
    Kelly fraction is negative, the best positive stake is zero: there is no
    edge worth betting.
    """

    _validate_probability(win_probability)
    _validate_payout_multiple(payout_multiple)

    lose_probability = 1.0 - win_probability
    raw_fraction = win_probability - lose_probability / payout_multiple
    return max(0.0, float(raw_fraction))


def strategy_fractions(win_probability: float, payout_multiple: float = 1.0) -> dict[str, float]:
    """Return the stake fraction used by each strategy."""

    full_kelly = kelly_fraction(win_probability, payout_multiple)
    return {
        "No Kelly": 0.0,
        "Half Kelly": full_kelly / 2.0,
        "Full Kelly": full_kelly,
    }


def simulate_binary_bets(
    initial_bankroll: float,
    win_probability: float,
    decimal_odds: float,
    number_of_bets: int,
    simulations: int = 3_000,
    seed: int = 7,
    sample_count: int = 60,
) -> dict[str, StrategyResult]:
    """Simulate shared binary-bet outcomes for three betting strategies.

    Outcomes are generated using ``win_probability``. Decimal odds determine
    the profit paid on a win, so the outcome generator and the offered price
    are independent inputs. Each strategy sees the same outcomes in each
    trial, making the comparison about stake sizing rather than different
    random luck.
    """

    if initial_bankroll <= 0.0:
        raise ValueError("initial_bankroll must be positive")
    if number_of_bets < 1:
        raise ValueError("number_of_bets must be at least 1")
    if simulations < 1:
        raise ValueError("simulations must be at least 1")
    if sample_count < 1:
        raise ValueError("sample_count must be at least 1")

    _validate_probability(win_probability)
    if decimal_odds <= 1.0:
        raise ValueError("decimal_odds must be greater than 1")

    payout_multiple = decimal_odds - 1.0
    fractions = strategy_fractions(win_probability, payout_multiple)
    sample_size = min(sample_count, simulations)
    steps = number_of_bets + 1
    results: dict[str, StrategyResult] = {}
    bankrolls = {
        name: np.full(simulations, float(initial_bankroll), dtype=float)
        for name in STRATEGY_NAMES
    }
    quantiles = {
        name: np.empty((steps, 3), dtype=float) for name in STRATEGY_NAMES
    }
    sample_paths = {
        name: np.empty((steps, sample_size), dtype=float) for name in STRATEGY_NAMES
    }

    for name in STRATEGY_NAMES:
        quantiles[name][0] = initial_bankroll
        sample_paths[name][0] = initial_bankroll

    rng = np.random.default_rng(seed)
    for step in range(1, steps):
        wins = rng.random(simulations) < win_probability
        for name in STRATEGY_NAMES:
            fraction = fractions[name]
            current = bankrolls[name]
            bankrolls[name] = np.where(
                wins,
                current * (1.0 + fraction * payout_multiple),
                current * (1.0 - fraction),
            )
            quantiles[name][step] = np.percentile(bankrolls[name], [10, 50, 90])
            sample_paths[name][step] = bankrolls[name][:sample_size]

    for name in STRATEGY_NAMES:
        results[name] = StrategyResult(
            name=name,
            fraction=fractions[name],
            quantiles=quantiles[name],
            sample_paths=sample_paths[name],
            terminal_bankrolls=bankrolls[name],
        )
    return results
