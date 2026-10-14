# JPM Volatility Modeling with GARCH and VaR

A Python comparison of one-day GARCH(1,1) and historical-simulation return
thresholds for JPMorgan equity. The research question is whether their
out-of-sample breach frequencies are consistent with nominal 95% coverage.

## Methodology correction

The previous implementation fitted GARCH on the full evaluation sample and
included the tested return in the historical quantile window. Its reported
breach rates and calibration claims do not validate this corrected backtest.
The original documentation is retained in [the historical record](docs/legacy_readme.md),
and the existing `images/` files remain historical illustrations. They have
not been regenerated as corrected results.

## Past-only evaluation

- Download Close and Adjusted Close separately for 2020-01-01 through
  2025-01-01 (exclusive end date) using `yfinance`.
- Compute daily log returns and express modeled returns in percentage points.
- For each target date, refit a constant-mean, normal-error GARCH(1,1) using
  only the preceding 250 observations. Forecast the next observation's mean
  and variance, then calculate `mean + normal_quantile(0.05) * sigma`.
- Historical simulation uses the fifth percentile of the same preceding
  250 returns. Its rolling quantile is shifted by one observation.
- Evaluate both methods on identical target dates, excluding the initial
  250-return training period. Early-2020 behavior is training data,
  not part of the reported out-of-sample evaluation.
- Stop on invalid data or failed GARCH convergence instead of silently
  dropping difficult forecasts or substituting another model.

The code stores lower-tail **return thresholds**, generally negative. A
positive loss VaR would use the opposite sign. VaR is a quantile, not a
maximum possible loss or an expected tail loss. Nominal coverage is a model
target, not a guarantee of future losses.

## Evaluation and limitations

The script reports breach rates and the Kupiec unconditional-coverage
likelihood-ratio statistic. Failure to reject 5% coverage does not establish
model validity, independent breaches, or good performance in extreme events.
The asymptotic test can be unreliable in small samples. Breach-independence
testing and alternative innovation distributions remain future work.

Price data downloaded today may contain subsequent revisions and corporate
action adjustments. Past-only return windows remove the identified code-level
look-ahead issues, but do not establish a historical point-in-time data vintage.
This is a single-equity research demonstration, not investment advice or a
validated production risk system. Corrected market performance must be assessed
from a recorded run; legacy numbers must not be reused.

## Run

Use Python 3.10 or newer in an isolated environment:

```console
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python garch_var_model.py
```

The model downloads prices and refits GARCH for every target date, so a full
run takes longer than a single fit. It writes `outputs/close_backtest.csv`,
`outputs/adjusted_close_backtest.csv`, and
`outputs/garch_vs_historical_var.png`. Existing files at those output paths
are replaced on a new run; preserve a completed run elsewhere before rerunning
if it needs to be retained. Historical files in `images/` are untouched.

Each run also saves `outputs/price_snapshot.csv` and `outputs/run_manifest.json`
with retrieval time, source/input/output hashes, Python/package versions, and
completion status. A `started` manifest must not be treated as a completed run.

Tests use synthetic returns and require no market-data downloads. They check
forecast timing, target/future perturbation invariance, equal evaluation
dates, coverage-test boundary cases, and fit-failure handling.

## Author

Jason Keen
