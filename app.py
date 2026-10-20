"""Interview-ready equity analytics dashboard. Run: streamlit run app.py."""
from datetime import timedelta
import json

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import daily_returns, drawdowns, insight_bullets, monthly_returns, summary_metrics
from src.data import ROOT, clean_prices, close_matrix, download_prices, load_snapshot
from src.modeling import walk_forward
from src.reporting import findings_markdown
from src.sql_analysis import monthly_sql_summary

st.set_page_config(page_title="Equity Lens | Market analytics", page_icon="📊", layout="wide")
COLORS = ["#168b80", "#4566c7", "#d28a2e", "#975cbd", "#db6472", "#34495e"]
px.defaults.color_discrete_sequence = COLORS
px.defaults.template = "plotly_white"


@st.cache_data
def snapshot():
    return load_snapshot()


@st.cache_data(ttl=3600, show_spinner="Downloading and validating market data…")
def live_prices(tickers, start, end):
    return clean_prices(download_prices(tickers, str(start), str(end + timedelta(days=1))))


@st.cache_data
def evaluate(close):
    return walk_forward(close)


def chart(fig, height=390):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="", hovermode="x unified", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch")


def csv_bytes(frame):
    return frame.to_csv(index=True).encode("utf-8")


try:
    base, base_audit = snapshot()
except (ValueError, OSError) as exc:
    st.error(str(exc))
    st.stop()

with st.sidebar:
    st.markdown("### EQUITY LENS")
    st.caption("A reproducible market analytics study")
    with st.form("analysis_controls"):
        source = st.radio("Data source", ["Offline snapshot", "Yahoo Finance"])
        selected = st.multiselect("Equities", ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"], default=["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"])
        st.caption("SPY is included as the benchmark in every comparison.")
        start = st.date_input("Start date", base.Date.min().date())
        end = st.date_input("End date (inclusive)", base.Date.max().date())
        risk_free_pct = st.number_input("Annual risk-free assumption (%)", 0.0, 15.0, 0.0, 0.25)
        st.form_submit_button("Update analysis", type="primary", width="stretch")
    st.divider()
    st.caption("Adjusted daily USD prices. Analytics use common observed sessions without filling missing prices.")
    st.caption("Educational research · No trading performance claimed")

if not selected or start >= end:
    st.info("Choose at least one equity and an end date after the start date.")
    st.stop()
symbols = selected + ["SPY"]
try:
    prices, audit = (base, base_audit) if source == "Offline snapshot" else live_prices(symbols, start, end)
    filtered = prices.loc[prices.Ticker.isin(symbols) & prices.Date.between(pd.Timestamp(start), pd.Timestamp(end))]
    close, dropped = close_matrix(filtered, symbols)
except Exception as exc:
    st.error(f"Could not prepare this analysis: {exc}")
    st.caption("Use the bundled offline snapshot if the live provider is unavailable.")
    st.stop()

metrics = summary_metrics(close, "SPY", risk_free_pct / 100)
returns = daily_returns(close)
st.caption("RESEARCH / EQUITIES / HISTORICAL ANALYSIS")
st.title("Performance tells half the story.")
st.markdown("Explore the returns, risks and predictability of five technology stocks against the S&P 500 ETF benchmark.")
st.caption(f"{source}  ·  {close.index.min():%d %b %Y} — {close.index.max():%d %b %Y}  ·  {len(close):,} common sessions  ·  USD")
if source == "Offline snapshot" and (start < base.Date.min().date() or end > base.Date.max().date()):
    st.info("The offline snapshot covers only the actual dates shown above. Use Yahoo Finance to request a different period.")

leader = metrics.loc[selected, "Total return"].idxmax()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Highest equity return", leader, f"{metrics.loc[leader, 'Total return']:.1%}", delta_color="off")
c2.metric("Benchmark total return", f"{metrics.loc['SPY', 'Total return']:.1%}")
c3.metric("Largest equity drawdown", f"{metrics.loc[selected, 'Max drawdown'].min():.1%}")
c4.metric("Validated selected rows", f"{len(filtered):,}")

overview, risk, experiment, quality = st.tabs(["Performance & findings", "Risk & relationships", "Model evaluation", "Data quality & SQL"])

with overview:
    st.subheader("Growth of $100")
    st.caption("Each series begins at $100 on the first common session; provider-adjusted close prices.")
    normalized = close.div(close.iloc[0]).mul(100)
    fig = px.line(normalized, labels={"value": "Value (USD)", "Date": ""})
    fig.update_traces(line_width=2.4)
    chart(fig, 430)
    for bullet in insight_bullets(close):
        st.markdown(f"- {bullet}")
    st.subheader("Performance scorecard")
    st.dataframe(metrics[["Total return", "CAGR", "Annual volatility", "Max drawdown", "Sharpe ratio"]].style.format({"Total return": "{:.1%}", "CAGR": "{:.1%}", "Annual volatility": "{:.1%}", "Max drawdown": "{:.1%}", "Sharpe ratio": "{:.2f}"}), width="stretch")
    st.caption(f"CAGR uses elapsed calendar time. Volatility uses 252 sessions/year. Sharpe assumes a constant {risk_free_pct:.2f}% annual risk-free rate.")
    monthly_ticker = st.selectbox("Monthly return detail", selected, key="monthly_ticker")
    monthly = monthly_returns(close)[monthly_ticker]
    heat = monthly.to_frame("Return").assign(Year=monthly.index.year, Month=monthly.index.month).pivot(index="Year", columns="Month", values="Return").reindex(columns=range(1, 13))
    heat.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    chart(px.imshow(heat, color_continuous_scale="RdBu", color_continuous_midpoint=0, text_auto=".1%", aspect="auto", labels={"color": "Return"}), 320)
    st.caption("Compounded observed daily returns. Boundary months can be partial; blank cells have no observations.")
    st.download_button("Download performance metrics", csv_bytes(metrics), "performance_metrics.csv", "text/csv")

with risk:
    st.subheader("What happened between the peaks?")
    chart(px.line(drawdowns(close).mul(100), labels={"value": "Drawdown (%)", "Date": ""}), 360)
    left, right = st.columns(2)
    with left:
        st.markdown("#### Daily-return correlation")
        chart(px.imshow(returns.corr(), zmin=-1, zmax=1, text_auto=".2f", color_continuous_scale="RdBu", aspect="auto"), 370)
    with right:
        st.markdown("#### Historical return versus risk")
        scatter = metrics.reset_index()
        scatter["Volatility (%)"] = scatter["Annual volatility"] * 100
        scatter["CAGR (%)"] = scatter["CAGR"] * 100
        chart(px.scatter(scatter, x="Volatility (%)", y="CAGR (%)", text="Ticker", color="Ticker", size_max=18), 370)
    st.markdown("#### 63-session rolling annualized volatility")
    chart(px.line(returns.rolling(63).std().mul(np.sqrt(252) * 100), labels={"value": "Annual volatility (%)", "Date": ""}), 300)
    st.dataframe(metrics[["Beta vs benchmark", "Correlation vs benchmark", "Daily VaR 95% (loss)", "Daily ES 95% (loss)", "Positive days"]].style.format({"Beta vs benchmark": "{:.2f}", "Correlation vs benchmark": "{:.2f}", "Daily VaR 95% (loss)": "{:.2%}", "Daily ES 95% (loss)": "{:.2%}", "Positive days": "{:.1%}"}), width="stretch")
    st.caption("VaR is the negative fifth percentile of historical daily returns; expected shortfall is the mean loss at or beyond that threshold. Both describe this sample. Correlations use daily returns, not price levels.")

with experiment:
    st.subheader("Can a model beat yesterday’s closing price?")
    model_ticker = st.selectbox("Evaluate a stock", selected, key="model_ticker")
    st.caption("One-session-ahead predictions · Four expanding training windows · 20 return lags · Fixed Ridge alpha = 10")
    try:
        scores, predictions, folds = evaluate(close[model_ticker])
    except ValueError as exc:
        st.info(str(exc))
    else:
        improvement = scores.loc["Ridge regression", "MAE improvement vs naive"]
        message = f"Ridge {'reduced' if improvement > 0 else 'increased'} price MAE by {abs(improvement):.2%} versus the previous-close baseline on these held-out sessions."
        st.info(message)
        st.dataframe(scores.style.format({"MAE (USD)": "{:.4f}", "RMSE (USD)": "{:.4f}", "Return MAE (bps)": "{:.2f}", "Direction accuracy": "{:.1%}", "MAE improvement vs naive": "{:+.2%}", "Observations": "{:.0f}"}, na_rep="N/A"), width="stretch")
        st.caption("Positive MAE improvement means lower error. Direction accuracy excludes flat predictions; it is N/A for the previous-close baseline. One basis point (bp) = 0.01 percentage point.")
        actual = predictions.drop_duplicates("Date").set_index("Date")["Actual close"]
        plotted = predictions.pivot(index="Date", columns="Model", values="Predicted close").assign(Actual=actual)
        chart(px.line(plotted, labels={"value": "Adjusted close (USD)", "Date": ""}), 380)
        st.caption("Prices can look close while next-day return errors remain large. This is not a multi-day forecast or a trading backtest.")
        st.markdown("#### Is performance consistent across periods?")
        chart(px.bar(folds, x="Fold", y="Return MAE (bps)", color="Model", barmode="group"), 310)
        with st.expander("Validation design and fold boundaries"):
            st.write("Training begins with the first 60% of complete feature rows, then expands across four test blocks. Each fold fits its scaler and model on earlier rows only. Test features use observed data through the preceding session. No test returns are used as training labels within that fold.")
            st.write("There is no hyperparameter search. Further tuning against these results would require a fresh test period. The legacy LSTM and saved model are excluded because their training provenance is unavailable.")
            st.dataframe(folds, width="stretch", hide_index=True)
        col1, col2 = st.columns(2)
        col1.download_button("Download held-out predictions", predictions.to_csv(index=False).encode(), "held_out_predictions.csv", "text/csv")
        report = findings_markdown(close, scores, model_ticker, "SPY", source, risk_free_pct / 100)
        col2.download_button("Download research findings", report.encode(), "research_findings.md", "text/markdown")

with quality:
    st.subheader("Trace every result back to its inputs")
    st.caption("Quality audit covers the source load before date/symbol filtering. Rules can overlap; unique invalid rows are counted separately.")
    left, right = st.columns([1, 2])
    with left:
        st.dataframe(audit, hide_index=True, width="stretch")
    with right:
        coverage = filtered.groupby("Ticker").agg(First=("Date", "min"), Last=("Date", "max"), Rows=("Date", "size"))
        st.dataframe(coverage, width="stretch")
        st.write(f"{dropped:,} dates excluded from cross-stock analysis because at least one selected symbol was missing. No price imputation is applied.")
        st.caption("A common missing date across every symbol is not detectable from this table. Exchange-calendar completeness is not independently verified.")
    if source == "Offline snapshot":
        manifest_path = ROOT / "data" / "market_snapshot.json"
        if manifest_path.exists():
            with st.expander("Snapshot source, retrieval time and integrity hash"):
                st.json(json.loads(manifest_path.read_text(encoding="utf-8")))
    st.markdown("#### SQL: monthly daily-return summaries")
    st.caption("This query runs against the validated selected records in SQLite. AVG(daily_return) is an arithmetic daily mean, not a monthly compounded return. Date filters precede LAG, so the first session has no return.")
    sql = (ROOT / "sql" / "analysis.sql").read_text(encoding="utf-8")
    with st.expander("View the SQL query"):
        st.code(sql, language="sql")
    sql_summary = monthly_sql_summary(filtered)
    st.dataframe(sql_summary, hide_index=True, width="stretch")
    st.download_button("Download SQL results", sql_summary.to_csv(index=False).encode(), "sql_monthly_summary.csv", "text/csv")
    st.download_button("Download validated selected data", filtered.to_csv(index=False).encode(), "validated_prices.csv", "text/csv")
    with st.expander("Inspect validated source records"):
        st.dataframe(filtered, hide_index=True, width="stretch")

st.divider()
st.caption("METHOD NOTES  ·  Hand-picked surviving US large caps  ·  Historical adjusted prices  ·  No causal or investment conclusions  ·  See README for formulas and reproducibility")
