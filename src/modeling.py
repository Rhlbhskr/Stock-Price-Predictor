"""Expanding-window, next-session return evaluation with two simple baselines."""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def feature_table(close: pd.Series, lags: int = 20) -> pd.DataFrame:
    """Each row predicts that row's return using observations strictly before it."""
    returns = close.pct_change(fill_method=None)
    features = pd.DataFrame({f"lag_{lag}": returns.shift(lag) for lag in range(1, lags + 1)})
    features["mean_5"] = returns.rolling(5).mean().shift(1)
    features["mean_20"] = returns.rolling(20).mean().shift(1)
    features["vol_20"] = returns.rolling(20).std().shift(1)
    features["previous_close"] = close.shift(1)
    features["actual_return"] = returns
    features["actual_close"] = close
    return features.dropna()


def score_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, group in predictions.groupby("Model", sort=False):
        price_error = group["Predicted close"] - group["Actual close"]
        return_error = group["Predicted return"] - group["Actual return"]
        moving = (group["Predicted return"] != 0) & (group["Actual return"] != 0)
        hit_rate = (np.sign(group.loc[moving, "Predicted return"]) == np.sign(group.loc[moving, "Actual return"])).mean() if moving.any() else np.nan
        rows.append({"Model": name, "MAE (USD)": price_error.abs().mean(), "RMSE (USD)": np.sqrt((price_error ** 2).mean()),
                     "Return MAE (bps)": return_error.abs().mean() * 10000, "Direction accuracy": hit_rate, "Observations": len(group)})
    return pd.DataFrame(rows).set_index("Model")


def walk_forward(close: pd.Series, folds: int = 4) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data = feature_table(close)
    if len(data) < 120:
        raise ValueError("Model evaluation needs at least 141 common price observations.")
    initial = int(len(data) * 0.6)
    boundaries = np.linspace(initial, len(data), folds + 1, dtype=int)
    columns = [col for col in data if col not in {"previous_close", "actual_return", "actual_close"}]
    results, fold_rows = [], []
    for fold, (start, end) in enumerate(zip(boundaries[:-1], boundaries[1:]), 1):
        train, test = data.iloc[:start], data.iloc[start:end]
        model = make_pipeline(StandardScaler(), Ridge(alpha=10.0))
        model.fit(train[columns], train["actual_return"])
        predicted = {
            "Previous close": np.zeros(len(test)),
            "Historical mean": np.repeat(train["actual_return"].mean(), len(test)),
            "Ridge regression": model.predict(test[columns]),
        }
        pieces = []
        for name, values in predicted.items():
            piece = pd.DataFrame({"Date": test.index, "Fold": fold, "Model": name,
                                  "Actual close": test["actual_close"].to_numpy(), "Predicted close": test["previous_close"].to_numpy() * (1 + values),
                                  "Actual return": test["actual_return"].to_numpy(), "Predicted return": values})
            pieces.append(piece)
        fold_predictions = pd.concat(pieces, ignore_index=True)
        results.append(fold_predictions)
        for name, row in score_predictions(fold_predictions).iterrows():
            fold_rows.append({"Fold": fold, "Model": name, "Train start": train.index.min(), "Train end": train.index.max(),
                              "Test start": test.index.min(), "Test end": test.index.max(), "Train rows": len(train), "Test rows": len(test), **row.to_dict()})
    predictions = pd.concat(results, ignore_index=True)
    scores = score_predictions(predictions)
    scores["MAE improvement vs naive"] = 1 - scores["MAE (USD)"] / scores.loc["Previous close", "MAE (USD)"] if scores.loc["Previous close", "MAE (USD)"] else np.nan
    return scores, predictions, pd.DataFrame(fold_rows)
