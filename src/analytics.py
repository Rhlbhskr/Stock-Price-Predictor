"""Descriptive market analytics. Returns are fractions, prices are adjusted USD."""
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def daily_returns(close: pd.DataFrame) -> pd.DataFrame:
    return close.pct_change(fill_method=None).iloc[1:]


def drawdowns(close: pd.DataFrame) -> pd.DataFrame:
    return close / close.cummax() - 1


def summary_metrics(close: pd.DataFrame, benchmark: str = "SPY", risk_free: float = 0.0) -> pd.DataFrame:
    returns = daily_returns(close)
    years = (close.index[-1] - close.index[0]).days / 365.25
    if years <= 0 or benchmark not in close:
        raise ValueError("A valid date range and benchmark are required.")
    total = close.iloc[-1] / close.iloc[0] - 1
    vol = returns.std(ddof=1) * np.sqrt(TRADING_DAYS)
    daily_rf = (1 + risk_free) ** (1 / TRADING_DAYS) - 1
    benchmark_variance = returns[benchmark].var(ddof=1)
    q = returns.quantile(0.05)
    out = pd.DataFrame({
        "Total return": total,
        "CAGR": (1 + total) ** (1 / years) - 1,
        "Annual volatility": vol,
        "Max drawdown": drawdowns(close).min(),
        "Sharpe ratio": (returns.mean() - daily_rf) * TRADING_DAYS / vol.replace(0, np.nan),
        "Beta vs benchmark": returns.apply(lambda x: x.cov(returns[benchmark]) / benchmark_variance if benchmark_variance > 0 else np.nan),
        "Correlation vs benchmark": returns.corr()[benchmark],
        "Daily VaR 95% (loss)": -q,
        "Daily ES 95% (loss)": returns.apply(lambda x: -x[x <= q[x.name]].mean()),
        "Positive days": (returns > 0).mean(),
    })
    out.index.name = "Ticker"
    return out


def monthly_returns(close: pd.DataFrame) -> pd.DataFrame:
    """Compound observed daily returns; first/last months can be partial."""
    return daily_returns(close).add(1).resample("ME").prod(min_count=1).sub(1)


def insight_bullets(close: pd.DataFrame, benchmark: str = "SPY") -> list[str]:
    metrics = summary_metrics(close, benchmark)
    stocks = metrics.drop(index=benchmark)
    if stocks.empty:
        return [f"{benchmark} returned {metrics.loc[benchmark, 'Total return']:.1%} over the selected observations."]
    leader = stocks["Total return"].idxmax()
    risky = stocks["Annual volatility"].idxmax()
    return [
        f"{leader} had the highest selected-stock return ({stocks.loc[leader, 'Total return']:.1%}); {benchmark} returned {metrics.loc[benchmark, 'Total return']:.1%} over the same sessions.",
        f"{risky} had the highest selected-stock annualized volatility ({stocks.loc[risky, 'Annual volatility']:.1%}) and a maximum drawdown of {stocks.loc[risky, 'Max drawdown']:.1%}.",
        "These are historical comparisons of a hand-picked group of surviving large-cap companies; they do not establish future performance or causation.",
    ]
