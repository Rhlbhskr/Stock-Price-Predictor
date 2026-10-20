import hashlib
import json

from src.data import SNAPSHOT, close_matrix, load_snapshot


def test_bundled_snapshot_matches_provenance_and_quality_contract():
    manifest = json.loads(SNAPSHOT.with_suffix(".json").read_text(encoding="utf-8"))
    assert hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest() == manifest["sha256"]
    prices, audit = load_snapshot()
    assert len(prices) == manifest["rows"]
    assert not prices.duplicated(["Date", "Ticker"]).any()
    assert set(prices.Ticker) == set(manifest["tickers"])
    assert audit.set_index("Check").loc["Invalid rows removed (unique)", "Rows"] == 0
    close, _ = close_matrix(prices, manifest["tickers"])
    assert len(close) > 1000
