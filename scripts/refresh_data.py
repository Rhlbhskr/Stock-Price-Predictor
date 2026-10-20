"""Explicitly download and freeze a dataset plus a provenance manifest."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yfinance

from src.data import ROOT, clean_prices, download_prices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="+", default=["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "SPY"])
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--end", default="2026-01-01", help="Exclusive end date")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "market_snapshot.csv")
    args = parser.parse_args()
    tickers = list(dict.fromkeys(t.strip().upper() for t in args.tickers))
    raw = download_prices(tickers, args.start, args.end)
    prices, audit = clean_prices(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    prices.to_csv(args.output, index=False, date_format="%Y-%m-%d", float_format="%.8f", lineterminator="\n")
    manifest = {"provider": "Yahoo Finance via yfinance", "source_url": "https://finance.yahoo.com/", "yfinance_version": yfinance.__version__,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "requested_start": args.start, "requested_end_exclusive": args.end,
                "auto_adjust": True, "currency": "USD", "volume": "Provider-reported share volume; not a dollar liquidity measure",
                "tickers": tickers, "rows": len(prices), "first_date": str(prices.Date.min().date()), "last_date": str(prices.Date.max().date()),
                "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(), "quality_audit": audit.to_dict("records")}
    args.output.with_suffix(".json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Saved {len(prices):,} validated rows to {args.output}")


if __name__ == "__main__":
    main()
