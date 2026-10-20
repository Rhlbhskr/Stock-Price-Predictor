"""Reproduce portfolio evidence from the bundled snapshot, without network calls."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analytics import drawdowns, summary_metrics
from src.data import ROOT, close_matrix, load_snapshot
from src.modeling import walk_forward
from src.reporting import findings_markdown
from src.sql_analysis import monthly_sql_summary


def main():
    prices, audit = load_snapshot()
    symbols = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "SPY"]
    close, excluded = close_matrix(prices, symbols)
    output = ROOT / "reports"
    output.mkdir(exist_ok=True)
    metrics = summary_metrics(close)
    scores, predictions, folds = walk_forward(close["AAPL"])
    metrics.to_csv(output / "performance_metrics.csv")
    scores.to_csv(output / "model_comparison.csv")
    predictions.to_csv(output / "held_out_predictions.csv", index=False)
    folds.to_csv(output / "validation_folds.csv", index=False)
    audit.to_csv(output / "quality_audit.csv", index=False)
    monthly_sql_summary(prices).to_csv(output / "sql_monthly_summary.csv", index=False)
    (output / "findings.md").write_text(findings_markdown(close, scores, "AAPL", "SPY", "Bundled Yahoo Finance snapshot"), encoding="utf-8")
    (output / "run_summary.json").write_text(json.dumps({"common_observations": len(close), "excluded_dates": excluded, "model_ticker": "AAPL", "ridge_mae_improvement": scores.loc["Ridge regression", "MAE improvement vs naive"]}, indent=2), encoding="utf-8")
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold", "figure.facecolor": "#f6f8fb", "axes.facecolor": "#f6f8fb", "axes.prop_cycle": plt.cycler(color=["#168b80", "#4566c7", "#d28a2e", "#975cbd", "#db6472", "#34495e"])})
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    close.div(close.iloc[0]).mul(100).plot(ax=axes[0], linewidth=1.7)
    axes[0].set(title="EQUITY LENS  |  Growth of $100", ylabel="Adjusted value (USD)")
    axes[0].legend(ncol=6, loc="upper left", frameon=False)
    drawdowns(close).mul(100).plot(ax=axes[1], legend=False, linewidth=1.2)
    axes[1].set(title="Historical drawdowns", ylabel="Below running peak (%)", xlabel="")
    for ax in axes:
        ax.grid(alpha=0.15)
    fig.text(0.08, 0.015, "Yahoo Finance adjusted daily prices | 2021–2025 | Selected survivors; historical comparison only", fontsize=9, color="#526477")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(output / "performance.png", dpi=150)
    plt.close(fig)
    print((output / "findings.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
