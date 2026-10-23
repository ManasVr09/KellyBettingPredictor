# Kelly Betting Lab

An interactive Streamlit simulator for the question:

> How much should you bet when your probability differs from the price?

This is a binary-betting model rather than a fair-coin model. You provide:

- Your estimated probability of winning.
- The decimal odds being offered.
- Your starting bankroll and number of repeated wagers.

The simulator compares three bankroll policies:

- **No Kelly:** bet 0% of bankroll.
- **Half Kelly:** bet half of the full Kelly fraction.
- **Full Kelly:** bet the full Kelly fraction.

## Break-even probability

For decimal odds `O`, the probability required to break even is:

```text
p_break_even = 1 / O
```

This means a probability below 50% can still be profitable when the odds are
long enough. At 2.50 decimal odds, the break-even probability is 40%. If your
estimated win probability is 45%, the wager has positive expected value and
Full Kelly bets 8.33% of bankroll:

```text
b = O - 1
f* = (b × p - (1 - p)) / b
   = (1.5 × 0.45 - 0.55) / 1.5
   = 8.33%
```

If your estimate is below the break-even probability, Kelly floors the stake
at 0%. No stake size turns a negative-expected-value wager into a positive one.

## Run the app

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

## Run the tests

```bash
python3 -m unittest discover -s tests -v
```

The simulation uses shared random outcomes for all three policies so the
comparison isolates stake sizing. It is illustrative only and does not model
changing odds, bookmaker margin, fees, taxes, betting limits, estimation error,
or dependence between outcomes.

## Performance

See the [performance notes](PERFORMANCE.md) for caching and result-preservation checks.
