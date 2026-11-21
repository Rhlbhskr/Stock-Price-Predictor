Equity Lens — Equity Performance & Risk Analytics
A reproducible financial analytics project combining Python, SQL, interactive dashboards, and leakage-aware model evaluation.

Live dashboard · [**Research findings**](reports/findings.md) · [**Executed notebook**](notebooks/equity_analysis.ipynb) · Source code

Tech stack: Python · Pandas · NumPy · SQLite · Plotly · Streamlit · scikit-learn · pytest

Overview
Equity Lens investigates a deceptively simple question: does an impressive historical return still look attractive after accounting for risk—and can a predictive model beat a straightforward baseline?

The project compares five technology stocks (AAPL, MSFT, NVDA, AMZN, GOOGL) against SPY over a fixed 2021–2025 historical sample. It brings the full workflow together: data validation, SQL analysis, risk metrics, visualization, time-ordered machine-learning evaluation, and reproducible reporting.

It is designed as an analytics and model-evaluation tool, not a trading signal generator.
Key findings
The versioned dataset contains 7,530 validated daily records across six symbols, covering 1,255 common observed sessions from January 4, 2021, through December 31, 2025.
Finding	Result	Interpretation
NVIDIA total return	1,326.2%	Strong historical growth in this selected period
SPY total return	98.1%	Broad-market reference, not a sector-matched benchmark
NVIDIA annualized volatility	52.2%	Substantial variation in daily returns
NVIDIA maximum drawdown	−66.3%	Severe peak-to-trough decline despite high total return


Prediction experiment: simpler baselines won
A separate Apple (AAPL) experiment evaluates next-session predictions across four chronological held-out test blocks:
Approach	Held-out price MAE
Ridge regression (alpha=10)	$2.5405
Previous-close baseline (zero predicted return)	$2.4834
Training-mean-return baseline	$2.4722


Ridge produced 2.30% higher price MAE than simply predicting the previous close. This result is intentionally reported as a negative finding: a more complex model did not improve out-of-sample prediction in this experiment.

The experiment does not establish that these methods will perform the same way for other stocks or time periods. Full outputs and evaluation scope are documented in the [findings report](reports/findings.md) and [research notebook](notebooks/equity_analysis.ipynb).
What the dashboard offers
View	What you can investigate
Performance & findings	Growth of $100, total return, CAGR, compounded monthly returns, and computed observations
Risk & relationships	Volatility, drawdowns, correlations of daily returns, beta, historical 95% VaR, and expected shortfall
Model evaluation	Four chronological folds, Ridge vs. two baselines, error metrics, fold-level results, and prediction exports
Data quality & SQL	Validation audit, aligned-session coverage, data provenance, an executable SQLite query, and data exports


Choose the assets, analysis dates, and risk-free-rate assumption, then select Update analysis.
Live data vs. reproducible snapshot
- Yahoo Finance (default): Requests daily historical data through the current UTC date, with downloads cached for one hour. The latest session available from the provider is shown. This is not a real-time market feed.
- Offline snapshot: Uses the fixed, versioned 2021–2025 dataset. It requires no network access once dependencies are installed and is also used if the live provider is unavailable, with a visible warning.
Live data refreshes do not overwrite the snapshot or silently change the published research reports.
Engineering and analytical approach
1. Validate before analyzing
Historical adjusted OHLC data is retrieved with yfinance using auto_adjust=True. The pipeline:
1. Checks required fields and parses symbols, dates, and numeric values.
2. Rejects invalid keys, non-finite data, nonpositive prices, negative volume, and inconsistent OHLC bars.
3. Resolves duplicate date/symbol records using the final valid source occurrence.
4. Sorts records and records validation counts in a data-quality audit.
5. Aligns cross-stock comparisons to common observed sessions, without forward-filling missing prices.
The [data provenance manifest](data/market_snapshot.json) records the retrieval timestamp, date range, library version, adjustment policy, row count, SHA-256 hash, and source-load audit. Coverage checks do not independently prove exchange-calendar completeness.
2. Analyze with both Python and SQL
Pandas and NumPy calculate performance and risk measures; Plotly renders interactive charts. An executable SQLite workflow uses LAG, PARTITION BY, and monthly aggregations, and its output is checked against Pandas calculations.

Selected metric definitions:
Metric	Calculation / interpretation
Daily return	close[t] / close[t-1] - 1
Total return	last close / first close - 1
CAGR	(last / first) ** (365.25 / elapsed calendar days) - 1
Annualized volatility	Sample standard deviation of daily returns × sqrt(252)
Maximum drawdown	Lowest value of close / running peak - 1 in the selected window
Sharpe ratio	Annualized mean excess daily return divided by annualized volatility
Beta	Return covariance with the benchmark divided by benchmark return variance
Historical 95% VaR	Negative fifth percentile of daily returns
Historical 95% expected shortfall	Negative mean return at or below the fifth percentile


Correlations use returns, not price levels. The SQL monthly query reports an arithmetic average daily return, which is different from the dashboard's compounded monthly return.
3. Evaluate predictions without using future data to fit the model
The experiment predicts the next-session return, then converts that return to a predicted price using the observed previous close.
- Features: 20 lagged returns; lagged 5- and 20-session return means; lagged 20-session volatility.
- Split: The first 60% of complete feature rows form the initial training set; the remainder is evaluated in four consecutive chronological test blocks.
- Model: StandardScaler and Ridge(alpha=10) are refitted using only data available before each test block.
- Baselines: Previous-close/zero-return prediction and the mean return of the preceding training data, recalculated at each fold boundary.
- Evaluation: Price MAE/RMSE, return MAE, direction accuracy where defined, fold-level scores, and exported held-out predictions.
The fitted model remains fixed within each test block while the lag features use previously observed session returns. This is a one-step-ahead, historical evaluation, not a recursively generated multi-day forecast. Hyperparameters were fixed ahead of this evaluation; further tuning would require a fresh final test period.
Run locally
Tested Python version: 3.11. The bundled snapshot requires no API key, TensorFlow, or live data connection after installing dependencies.
Windows (PowerShell)
git clone https://github.com/Rhlbhskr/Stock-Price-Predictor.git
cd Stock-Price-Predictor
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
On macOS/Linux, use .venv/bin/python in place of .\.venv\Scripts\python.exe.

The legacy launch paths Stocks.py and Stockprice.py forward to the supported app.py entry point.
Reproduce results and run tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.build_report
The report command regenerates the analysis outputs in reports/: findings, the performance figure, risk/performance metrics, data-quality audit, SQL outputs, model results, held-out predictions, and fold boundaries.

The test suite checks hand-calculated metrics, validation rules, SQL–Pandas agreement, snapshot integrity, date alignment, future-data perturbation, and dashboard behavior. GitHub Actions runs the tests and report generation on pushes and pull requests.

To explore the notebook, optionally install and launch JupyterLab:
.\.venv\Scripts\python.exe -m pip install jupyterlab
.\.venv\Scripts\python.exe -m jupyterlab
Open [`notebooks/equity_analysis.ipynb`](notebooks/equity_analysis.ipynb).
Refresh data explicitly
The versioned snapshot is not updated automatically. To download another dataset without replacing it:
.\.venv\Scripts\python.exe -m scripts.refresh_data --start 2021-01-01 --end 2026-01-01 --output data/local/research.csv
The requested end date is exclusive. Omit --output only when intentionally replacing the bundled snapshot; if you do, regenerate reports and review any affected README or résumé claims, since historical adjusted prices can be revised by the provider.
Repository layout
app.py                           Streamlit dashboard
src/
  data.py                        Validation, live loading, snapshot handling
  analytics.py                   Risk/performance metrics and findings
  modeling.py                    Chronological model evaluation
  sql_analysis.py                SQLite analyses
  reporting.py                   Shared findings generation
sql/analysis.sql                 Window functions and monthly queries
scripts/
  refresh_data.py                Explicit refresh with provenance
  build_report.py                Offline result and figure generation
data/
  market_snapshot.csv            Fixed historical dataset
  market_snapshot.json           Provenance, hash, and quality audit
notebooks/equity_analysis.ipynb  Executed analysis and interpretation
reports/                        Figures, tables, predictions, findings
tests/                          Data, metric, model, and UI checks
docs/cv_and_interview.md         Project explanation and interview guide
legacy/                          Archived original LSTM prototype
Limitations and responsible interpretation
- Selection bias: The six symbols are a selected set of surviving assets, not a representative or unbiased stock universe.
- Benchmark limitations: SPY is a broad-market comparator, not a technology-sector-matched benchmark.
- Historical data limitations: Adjusted prices may be revised. Alignment to common observed dates does not validate every expected exchange session.
- Model limitations: One stock, one period, and four held-out blocks cannot establish general predictive performance; no live trading strategy was tested.
- Risk interpretation: Correlation is descriptive, and sample-based VaR/expected shortfall are not guarantees of future losses.
- Trading assumptions: No transaction costs, slippage, taxes, portfolio allocation, or executed trades are modeled.
The earlier LSTM prototype is preserved under [`legacy/`](legacy/README.md) for transparency. Its original saved model is not used in the current dashboard because its training provenance is unknown; earlier preprocessing could also leak future information. The current application does not advertise an unsupported 60-day forecast.

Potential next steps: Predeclare a broader stock universe, add sector-specific benchmarks and exchange-calendar checks, and reserve a fresh future period for any new model-selection decisions.
Equity Lens is an educational financial analytics and model-evaluation project, not investment advice.

Open the dashboard · [View the findings](reports/findings.md) · Explore the code
