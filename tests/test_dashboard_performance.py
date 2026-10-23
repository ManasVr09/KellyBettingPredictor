from pathlib import Path

import numpy as np
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_cached_report_matches_the_original_engine_and_seed_changes(monkeypatch):
    monkeypatch.syspath_prepend(str(APP.parent))
    from simulator import simulate_binary_bets, STRATEGY_NAMES
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    expected = simulate_binary_bets(1000.0, .55, 1.91, 250, 3000, 7)
    for name in STRATEGY_NAMES:
        np.testing.assert_array_equal(app.session_state["simulation_results"][name].terminal_bankrolls,
                                      expected[name].terminal_bankrolls)
        np.testing.assert_array_equal(app.session_state["simulation_results"][name].quantiles,
                                      expected[name].quantiles)
    before = app.dataframe[0].value.copy()
    app.run()
    assert not app.exception and app.dataframe[0].value.equals(before)
    next(widget for widget in app.number_input if widget.label == "Random seed").set_value(8)
    app.button[0].click().run()
    assert not app.exception
    assert not np.array_equal(app.session_state["simulation_results"][STRATEGY_NAMES[1]].terminal_bankrolls,
                              expected[STRATEGY_NAMES[1]].terminal_bankrolls)
    assert len(app.dataframe) == 2  # Comparison and probability ladder both remain visible.
