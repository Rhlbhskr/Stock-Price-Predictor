from pathlib import Path
from datetime import date

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_dashboard_runs_offline_and_model_selection_updates():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    assert len(app.metric) == 4
    assert len(app.tabs) == 4
    app.selectbox(key="model_ticker").select("NVDA").run()
    assert not app.exception
    assert "Ridge" in app.info[0].value


def test_short_range_has_descriptive_analytics_and_model_guard():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.date_input[1].set_value(date(2021, 6, 1))
    app.button[0].click().run()
    assert not app.exception
    assert any("141" in item.value for item in app.info)
