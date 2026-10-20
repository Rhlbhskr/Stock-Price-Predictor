import numpy as np
import pandas as pd
import pytest

from src.analytics import daily_returns, drawdowns, monthly_returns, summary_metrics
from src.data import clean_prices, close_matrix
from src.sql_analysis import monthly_sql_summary


def bars():
    return pd.DataFrame({"Date": pd.bdate_range("2024-01-01", periods=4), "Ticker": "AAPL", "Open": [100, 110, 88, 99], "High": [100, 110, 88, 99], "Low": [100, 110, 88, 99], "Close": [100, 110, 88, 99], "Volume": 1000})


def test_returns_drawdown_and_monthly_compounding():
    close = bars().set_index("Date")[["Close"]].rename(columns={"Close": "SPY"})
    np.testing.assert_allclose(daily_returns(close)["SPY"], [0.1, -0.2, 0.125])
    np.testing.assert_allclose(drawdowns(close)["SPY"], [0, 0, -0.2, -0.1])
    assert monthly_returns(close)["SPY"].iloc[0] == pytest.approx(-0.01)
    metrics = summary_metrics(close)
    assert metrics.loc["SPY", "Total return"] == pytest.approx(-0.01)
    assert metrics.loc["SPY", "Max drawdown"] == pytest.approx(-0.2)
    assert metrics.loc["SPY", "Beta vs benchmark"] == pytest.approx(1)
    assert metrics.loc["SPY", "Annual volatility"] == pytest.approx(np.std([0.1, -0.2, 0.125], ddof=1) * np.sqrt(252))


def test_cleaning_audits_duplicate_and_invalid_rows_without_filling():
    frame = bars()
    duplicate = frame.iloc[[0]].copy()
    invalid = frame.iloc[[1]].copy()
    invalid["Close"] = -1
    nonfinite = frame.iloc[[2]].copy()
    nonfinite["Volume"] = np.inf
    cleaned, audit = clean_prices(pd.concat([frame, duplicate, invalid, nonfinite]))
    assert len(cleaned) == 4
    counts = audit.set_index("Check")["Rows"]
    assert counts["Duplicate keys removed"] == 1
    assert counts["Invalid rows removed (unique)"] == 2
    assert counts["Input rows"] - counts["Invalid rows removed (unique)"] - counts["Duplicate keys removed"] == counts["Output rows"]


def test_invalid_keys_and_bad_bars_are_removed():
    frame = bars()
    frame.loc[0, "Date"] = pd.NaT
    frame.loc[1, "Ticker"] = None
    frame.loc[2, "High"] = 1
    cleaned, _ = clean_prices(frame)
    assert len(cleaned) == 1
    with pytest.raises(ValueError, match="Missing required"):
        clean_prices(frame.drop(columns="Close"))


def test_intersection_drops_missing_session_without_forward_fill():
    dates = pd.bdate_range("2024-01-01", periods=80)
    left = pd.DataFrame({"Date": dates, "Ticker": "AAPL", "Close": np.arange(80) + 100.0})
    right = left.assign(Ticker="SPY").drop(index=15)
    close, excluded = close_matrix(pd.concat([left, right]), ["AAPL", "SPY"])
    assert len(close) == 79 and excluded == 1
    assert dates[15] not in close.index


def test_sql_lag_partitions_tickers_and_matches_pandas():
    a = bars()
    b = bars().assign(Ticker="SPY", Close=[50, 55, 44, 49.5])
    result = monthly_sql_summary(pd.concat([a, b]))
    for _, row in result.iterrows():
        series = a.Close if row.Ticker == "AAPL" else b.Close
        assert row.return_observations == 3
        assert row.mean_daily_return == pytest.approx(series.pct_change().mean())
