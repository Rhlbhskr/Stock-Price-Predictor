# Presenting this project on your CV

## Project title

**Equity Performance & Risk Analytics | Python, SQL, Pandas, Plotly, Streamlit**

## CV bullets

- Built an interactive equity analytics dashboard using 7,530 historical daily observations across five technology stocks and an S&P 500 ETF benchmark, covering 2021–2025.
- Implemented a validated data pipeline and SQLite window-function analysis to compare cumulative returns, CAGR, volatility, drawdowns and daily-return correlations.
- Evaluated next-session predictions with four expanding chronological folds and two baselines; found Ridge regression increased Apple price MAE by 2.30% versus the previous-close baseline.

Use these after you have run the project and can explain the implementation. Do not claim real trading profits, production deployment, professional experience or an LSTM accuracy improvement from this work.
If you change the snapshot, regenerate the report and update these numbers.

## 60-second interview introduction

“I started with a stock prediction prototype and developed it into a reproducible analytics study. I wanted to answer two questions: which stocks performed strongly relative to SPY, and what risk came with those returns? I used adjusted daily prices, validated the OHLC records, and compared performance on common sessions without filling gaps. I added SQL summaries, interactive risk charts and a chronological model experiment. NVIDIA led historical returns but also had a maximum drawdown of about 66%. On Apple, Ridge did not beat a simple previous-close baseline. My main conclusion was that strong historical performance and visually convincing predictions do not establish reliable next-day predictability.”

## Five-minute demonstration

1. Open the offline dashboard and identify the data source, period, universe and benchmark.
2. Show the normalized growth chart and explain why raw share prices cannot compare company performance.
3. Pair the leading return with its drawdown and annualized volatility.
4. Show daily-return correlations and explain why price-level correlation can mislead.
5. Open the SQL and explain `LAG`, `PARTITION BY`, aggregation and the distinction between arithmetic mean return and compounded return.
6. Show model baselines, fold boundaries and the negative result. Explain the original scaler leakage and how the new pipeline prevents it.
7. Download findings or open the notebook to demonstrate reproducibility.

## Questions you should be able to answer

- **Why SPY?** It is a broad US large-cap ETF benchmark, useful for contextualizing this selected US equity group. It is not a perfect sector-matched benchmark.
- **Why adjusted prices?** The provider adjusts for splits and dividends so these events do not appear as mechanical raw-price discontinuities. This is provider-revised historical data, not a complete point-in-time data system.
- **Why compare on common dates?** It keeps observed comparison sessions consistent. The app reports exclusions and avoids filling unavailable prices.
- **How is CAGR different from average daily return?** CAGR is the constant annual growth rate linking the initial and final price; daily mean is an arithmetic statistic of single-session returns.
- **What does a 66% drawdown mean?** A historical decline of about 66% from the running peak within this analysis window; a new investor's realized outcome depends on entry and exit.
- **What is leakage?** Using information unavailable at prediction time, such as fitting a scaler on the future test period. The new scaler is fit within each training fold only.
- **What happens within a test block?** The model stays fixed until the next fold, while each prediction uses newly observed previous-session returns. This evaluates a sequence of one-step predictions.
- **Why drop the LSTM from the main app?** Its saved model has no training provenance, and the original evaluation lacked a naive baseline. A transparent tested experiment is stronger evidence than an unsupported complex model.
- **Did Ridge help?** On the bundled Apple experiment it increased price MAE by 2.30%. That is an experimental finding, not a reason to hide the baseline.
- **What would you do next?** Evaluate a predeclared broader universe and an untouched later period; introduce sector benchmarks and exchange-calendar completeness checks. Any trading claim would also need realistic costs and a separate strategy backtest.

## Before sharing

Read `reports/findings.md`, run the tests, and practice the demonstration. Add the [GitHub repository](https://github.com/Rhlbhskr/Stock-Price-Predictor) to your CV and review the Analytics checks workflow in the repository's Actions tab.
