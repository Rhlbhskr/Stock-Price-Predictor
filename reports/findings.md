# Equity analytics: evidence and findings

Source: Bundled Yahoo Finance snapshot. Adjusted USD OHLC prices; observed sessions only.
Period: 2021-01-04 to 2025-12-31.
Universe: AAPL, MSFT, NVDA, AMZN, GOOGL, SPY. Common price observations: 1,255.
Benchmark: SPY. Risk-free assumption for Sharpe: 0.00% annually.

## Questions

1. Which selected equities delivered the strongest historical return, and what risk accompanied it?
2. How did they compare with the benchmark on the same sessions?
3. Does a lagged-return model outperform a simple next-session baseline?

## Descriptive findings

- NVDA had the highest selected-stock return (1326.2%); SPY returned 98.1% over the same sessions.
- NVDA had the highest selected-stock annualized volatility (52.2%) and a maximum drawdown of -66.3%.
- These are historical comparisons of a hand-picked group of surviving large-cap companies; they do not establish future performance or causation.

| Ticker | Total return | CAGR | Annual volatility | Max drawdown |
| --- | ---: | ---: | ---: | ---: |
| AAPL | 115.81% | 16.67% | 27.86% | -33.36% |
| MSFT | 131.53% | 18.33% | 25.71% | -37.15% |
| NVDA | 1326.20% | 70.36% | 52.22% | -66.34% |
| AMZN | 44.87% | 7.71% | 35.11% | -56.15% |
| GOOGL | 265.40% | 29.66% | 31.15% | -44.32% |
| SPY | 98.08% | 14.69% | 17.11% | -24.50% |

## Model experiment: AAPL

Ridge increased price MAE by 2.30% versus the previous-close baseline. This is an out-of-sample comparison, not evidence of a profitable strategy.

| Model | Price MAE (USD) | Price RMSE (USD) | Return MAE (bps) |
| --- | ---: | ---: | ---: |
| Previous close | 2.4834 | 3.6664 | 116.08 |
| Historical mean | 2.4722 | 3.6648 | 115.56 |
| Ridge regression | 2.5405 | 3.7158 | 118.88 |

Four expanding chronological folds begin after the first 60% of usable feature rows.
Each fold fits a fresh StandardScaler and Ridge(alpha=10) on earlier observations only.
Features are 20 lagged returns plus lagged rolling means and volatility. Each test prediction uses actual history through the previous session.
The training-mean baseline is refit at each fold boundary. The previous-close baseline predicts zero return.
These are rolling one-step predictions; no multi-day forecast or trading backtest is claimed.
Hyperparameters are fixed in advance; these test results must not be reused for tuning and still called an untouched final test.

## Interpretation and next decision

Use return and drawdown together when describing performance. A high price-level fit can coexist with poor next-day predictability.
If Ridge fails to beat the naive baseline, report that finding directly. If it wins slightly, validate on new periods and a broader universe before making stronger claims.

## Assumptions and limits

- CAGR uses elapsed calendar days / 365.25; volatility uses sample daily standard deviation times sqrt(252).
- Drawdown is measured from the running peak within this selected window. Earlier peaks are not included.
- The fixed universe has selection and survivorship bias. Correlation does not establish causation.
- Adjusted prices reflect the provider's split/dividend adjustments and can be revised later; this is not point-in-time fundamental data.
- Historical 95% VaR and expected shortfall summarize the observed daily loss distribution; they are not guarantees or forecast intervals.
- Missing sessions are never forward-filled. Cross-stock comparisons use the intersection of available dates.
- USD only; no transaction costs, slippage, taxes, trading strategy or realized trading performance is modeled.
- This is an educational analytics study, not investment advice.
