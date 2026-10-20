"""Human-readable findings built from the exact same metrics as the dashboard."""
import pandas as pd

from src.analytics import insight_bullets, summary_metrics


def findings_markdown(close: pd.DataFrame, scores: pd.DataFrame, ticker: str, benchmark: str, source: str, risk_free: float = 0.0) -> str:
    metrics = summary_metrics(close, benchmark, risk_free)
    improvement = scores.loc["Ridge regression", "MAE improvement vs naive"]
    result = f"Ridge {'reduced' if improvement > 0 else 'increased'} price MAE by {abs(improvement):.2%} versus the previous-close baseline."
    bullets = "\n".join(f"- {item}" for item in insight_bullets(close, benchmark))
    rows = "\n".join(f"| {name} | {row['Total return']:.2%} | {row['CAGR']:.2%} | {row['Annual volatility']:.2%} | {row['Max drawdown']:.2%} |" for name, row in metrics.iterrows())
    model_rows = "\n".join(f"| {name} | {row['MAE (USD)']:.4f} | {row['RMSE (USD)']:.4f} | {row['Return MAE (bps)']:.2f} |" for name, row in scores.iterrows())
    return f"""# Equity analytics: evidence and findings

Source: {source}. Adjusted USD OHLC prices; observed sessions only.
Period: {close.index.min().date()} to {close.index.max().date()}.
Universe: {', '.join(close.columns)}. Common price observations: {len(close):,}.
Benchmark: {benchmark}. Risk-free assumption for Sharpe: {risk_free:.2%} annually.

## Questions

1. Which selected equities delivered the strongest historical return, and what risk accompanied it?
2. How did they compare with the benchmark on the same sessions?
3. Does a lagged-return model outperform a simple next-session baseline?

## Descriptive findings

{bullets}

| Ticker | Total return | CAGR | Annual volatility | Max drawdown |
| --- | ---: | ---: | ---: | ---: |
{rows}

## Model experiment: {ticker}

{result} This is an out-of-sample comparison, not evidence of a profitable strategy.

| Model | Price MAE (USD) | Price RMSE (USD) | Return MAE (bps) |
| --- | ---: | ---: | ---: |
{model_rows}

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
"""
