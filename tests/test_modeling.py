import numpy as np
import pandas as pd

from src.modeling import feature_table, walk_forward


def series():
    rng = np.random.default_rng(42)
    return pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.015, 400))), index=pd.bdate_range("2022-01-03", periods=400))


def test_features_cannot_see_the_current_target():
    original = series()
    changed = original.copy()
    changed.iloc[250:] *= 5
    columns = [c for c in feature_table(original).columns if c not in {"actual_close", "actual_return"}]
    pd.testing.assert_frame_equal(feature_table(original).loc[:original.index[250], columns], feature_table(changed).loc[:original.index[250], columns])


def test_walk_forward_strict_dates_baselines_and_prediction_coverage():
    scores, predictions, folds = walk_forward(series())
    assert (folds["Train end"] < folds["Test start"]).all()
    assert folds.groupby("Fold")["Train rows"].first().is_monotonic_increasing
    assert not predictions.duplicated(["Date", "Model"]).any()
    assert predictions.groupby("Model").size().nunique() == 1
    naive = predictions[predictions.Model == "Previous close"]
    assert (naive["Predicted return"] == 0).all()
    np.testing.assert_allclose(naive["Predicted close"], series().shift(1).loc[naive.Date])
    assert np.isnan(scores.loc["Previous close", "Direction accuracy"])


def test_future_data_cannot_change_earlier_predictions():
    original = series()
    changed = original.copy()
    changed.iloc[-20:] *= 4
    _, first, _ = walk_forward(original)
    _, second, _ = walk_forward(changed)
    before = first.Date < original.index[-20]
    pd.testing.assert_frame_equal(first.loc[before], second.loc[before])
