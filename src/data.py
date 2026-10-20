"""Market-data contract, quality audit and explicit live-data loading."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "market_snapshot.csv"
REQUIRED = ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]


def clean_prices(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reject invalid bars; never fill prices or silently invent observations.

    Quality counts overlap: an invalid row can fail more than one rule.
    Duplicate date/ticker rows keep the final source occurrence.
    """
    missing = set(REQUIRED) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    df = raw[REQUIRED].copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", utc=True).dt.tz_convert(None).dt.normalize()
    df["Ticker"] = df["Ticker"].astype("string").str.strip().str.upper()
    numeric = REQUIRED[2:]
    df[numeric] = df[numeric].apply(pd.to_numeric, errors="coerce")
    bad_key = df["Date"].isna() | df["Ticker"].isna() | df["Ticker"].eq("")
    bad_numeric = ~np.isfinite(df[numeric]).all(axis=1)
    bad_value = (df[["Open", "High", "Low", "Close"]] <= 0).any(axis=1) | (df["Volume"] < 0)
    bad_bar = (df["High"] < df[["Open", "Low", "Close"]].max(axis=1)) | (df["Low"] > df[["Open", "High", "Close"]].min(axis=1))
    invalid = bad_key | bad_numeric | bad_value | bad_bar
    valid = df.loc[~invalid]
    duplicate_count = int(valid.duplicated(["Date", "Ticker"], keep="last").sum())
    cleaned = valid.drop_duplicates(["Date", "Ticker"], keep="last").sort_values(["Ticker", "Date"]).reset_index(drop=True)
    audit = pd.DataFrame({"Check": ["Input rows", "Invalid date / ticker", "Missing / non-finite numeric fields", "Nonpositive price / negative volume", "Inconsistent OHLC bar", "Invalid rows removed (unique)", "Duplicate keys removed", "Output rows"],
                          "Rows": [len(raw), int(bad_key.sum()), int(bad_numeric.sum()), int(bad_value.sum()), int(bad_bar.sum()), int(invalid.sum()), duplicate_count, len(cleaned)]})
    if cleaned.empty:
        raise ValueError("No valid price observations remain after validation.")
    return cleaned, audit


def load_snapshot() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not SNAPSHOT.exists():
        raise ValueError("Snapshot missing. Run python -m scripts.refresh_data or restore data/market_snapshot.csv.")
    return clean_prices(pd.read_csv(SNAPSHOT))


def download_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Yahoo end date is exclusive. All OHLC fields use auto_adjust=True."""
    import yfinance as yf

    frames = []
    for ticker in dict.fromkeys(tickers):
        prices = yf.download(ticker, start=start, end=end, auto_adjust=True,
                             multi_level_index=False, progress=False, threads=False)
        if prices is None or prices.empty:
            raise ValueError(f"No data received for {ticker}. Check the ticker, dates or provider availability.")
        prices = prices.reset_index()
        prices["Ticker"] = ticker
        frames.append(prices[REQUIRED])
    if not frames:
        raise ValueError("Choose at least one ticker.")
    return pd.concat(frames, ignore_index=True)


def close_matrix(prices: pd.DataFrame, tickers: list[str]) -> tuple[pd.DataFrame, int]:
    """Use the intersection of sessions; do not forward-fill suspensions/gaps."""
    wide = prices.loc[prices["Ticker"].isin(tickers)].pivot(index="Date", columns="Ticker", values="Close")
    missing = set(tickers) - set(wide.columns)
    if missing:
        raise ValueError(f"Missing symbols: {', '.join(sorted(missing))}")
    aligned = wide[tickers].dropna()
    if len(aligned) < 60:
        raise ValueError("Choose a range with at least 60 common trading observations.")
    return aligned, len(wide) - len(aligned)
