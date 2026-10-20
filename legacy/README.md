# Original LSTM prototype (archived)

These are the two original scripts, preserved for reference. They require the original TensorFlow/Keras environment, which is not part of the new analytics app.

The root `stock_model.h5` is retained but **never loaded** by the new dashboard. Its training ticker, dates, scaling parameters and validation evidence are unknown.

Known prototype limitations:

- The scaler was fit on the full series before the chronological split.
- `Stocks.py` could load the same saved model for different selected tickers.
- There was no naive forecast baseline or chronological validation across periods.
- Recursive 60-step forecasts lacked evaluated uncertainty; their dates included calendar days and the final observed date.
- Duplicated app code, fixed date ranges and missing setup instructions hindered reproduction.

The supported entry point is now `streamlit run app.py`. Old root entry points forward to it.
