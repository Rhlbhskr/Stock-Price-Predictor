from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from src.data import load_snapshot

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture(autouse=True)
def provider(monkeypatch):
    """Keep dashboard checks independent of the network and each other's cache."""
    st.cache_data.clear()
    download = Mock(side_effect=ValueError("Provider temporarily unavailable"))
    monkeypatch.setattr("src.data.download_prices", download)
    yield download
    st.cache_data.clear()


def recent_prices():
    prices, _ = load_snapshot()
    latest = pd.Timestamp(datetime.now(timezone.utc).date() - timedelta(days=1))
    prices["Date"] += latest - prices.Date.max()
    return prices


def test_dashboard_falls_back_offline_and_model_selection_updates():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    assert len(app.metric) == 4
    assert len(app.tabs) == 4
    assert any("Could not refresh" in item.value for item in app.warning)
    assert any("Offline snapshot  ·" in item.value for item in app.caption)
    app.selectbox(key="model_ticker").select("NVDA").run()
    assert not app.exception
    assert "Ridge" in app.info[0].value


def test_short_range_has_descriptive_analytics_and_model_guard():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.date_input[1].set_value(date(2021, 6, 1))
    app.button[0].click().run()
    assert not app.exception
    assert any("141" in item.value for item in app.info)


def test_opening_downloads_through_today_and_reuses_recent_data(provider):
    provider.side_effect = None
    provider.return_value = recent_prices()
    today = datetime.now(timezone.utc).date()
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    assert not app.warning
    assert app.radio[0].value == "Yahoo Finance"
    assert app.date_input[1].value == today
    symbols, start, end = provider.call_args.args
    assert set(symbols) == {"AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "SPY"}
    assert start == "2021-01-04"
    assert end == str(today + timedelta(days=1))  # Yahoo's end date is exclusive.
    latest = provider.return_value.Date.max().strftime("%d %b %Y")
    assert any("Yahoo Finance  ·" in item.value and latest in item.value for item in app.caption)
    app.selectbox(key="model_ticker").select("NVDA").run()
    assert not app.exception
    assert provider.call_count == 1


def test_explicit_offline_mode_does_not_download(provider):
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    provider.reset_mock()
    app.radio[0].set_value("Offline snapshot")
    app.button[0].click().run()
    assert not app.exception
    assert not app.warning
    provider.assert_not_called()


def test_failed_download_can_recover_on_next_open(provider):
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert app.warning
    provider.side_effect = None
    provider.return_value = recent_prices()
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    assert not app.warning
    assert any("Yahoo Finance  ·" in item.value for item in app.caption)
