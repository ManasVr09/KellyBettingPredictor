import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from simulator import (  # noqa: E402
    break_even_probability,
    expected_value_per_dollar,
    kelly_fraction,
    simulate_binary_bets,
    strategy_fractions,
)


class SimulatorTests(unittest.TestCase):
    def test_decimal_odds_define_break_even_probability(self):
        self.assertAlmostEqual(break_even_probability(2.00), 0.50)
        self.assertAlmostEqual(break_even_probability(2.50), 0.40)

    def test_below_50_percent_can_still_have_a_positive_edge(self):
        payout_multiple = 2.50 - 1.0

        self.assertAlmostEqual(expected_value_per_dollar(0.45, payout_multiple), 0.125)
        self.assertAlmostEqual(kelly_fraction(0.45, payout_multiple), 1 / 12)

    def test_even_money_kelly_fraction_matches_2p_minus_1(self):
        self.assertAlmostEqual(kelly_fraction(0.55), 0.10)
        self.assertAlmostEqual(kelly_fraction(0.50), 0.0)
        self.assertAlmostEqual(kelly_fraction(0.45), 0.0)

    def test_strategy_fractions_scale_full_kelly(self):
        fractions = strategy_fractions(0.45, payout_multiple=1.5)

        self.assertAlmostEqual(fractions["No Kelly"], 0.0)
        self.assertAlmostEqual(fractions["Half Kelly"], 1 / 24)
        self.assertAlmostEqual(fractions["Full Kelly"], 1 / 12)

    def test_simulation_is_reproducible_and_uses_no_kelly_as_cash(self):
        first = simulate_binary_bets(
            100.0,
            0.45,
            2.50,
            20,
            simulations=100,
            seed=11,
            sample_count=5,
        )
        second = simulate_binary_bets(
            100.0,
            0.45,
            2.50,
            20,
            simulations=100,
            seed=11,
            sample_count=5,
        )

        for name in first:
            np.testing.assert_array_equal(first[name].quantiles, second[name].quantiles)
            np.testing.assert_array_equal(first[name].terminal_bankrolls, second[name].terminal_bankrolls)

        np.testing.assert_allclose(first["No Kelly"].terminal_bankrolls, 100.0)
        self.assertGreater(first["Full Kelly"].fraction, first["Half Kelly"].fraction)

    def test_invalid_inputs_raise(self):
        invalid_cases = (
            {"initial_bankroll": 0.0},
            {"win_probability": -0.1},
            {"win_probability": 1.1},
            {"decimal_odds": 1.0},
            {"number_of_bets": 0},
            {"simulations": 0},
        )
        for invalid_case in invalid_cases:
            defaults = {
                "initial_bankroll": 100.0,
                "win_probability": 0.45,
                "decimal_odds": 2.50,
                "number_of_bets": 10,
                "simulations": 10,
            }
            defaults.update(invalid_case)

            with self.subTest(invalid_case=invalid_case), self.assertRaises(ValueError):
                simulate_binary_bets(**defaults)


if __name__ == "__main__":
    unittest.main()
