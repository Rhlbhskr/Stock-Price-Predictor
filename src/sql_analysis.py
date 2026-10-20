"""Execute the portfolio SQL against the same validated records as the app."""
import sqlite3

import pandas as pd

from src.data import ROOT


def monthly_sql_summary(prices: pd.DataFrame) -> pd.DataFrame:
    with sqlite3.connect(":memory:") as connection:
        frame = prices.copy()
        frame["Date"] = frame["Date"].dt.strftime("%Y-%m-%d")
        frame.to_sql("prices", connection, index=False, if_exists="replace")
        return pd.read_sql_query((ROOT / "sql" / "analysis.sql").read_text(encoding="utf-8"), connection)
