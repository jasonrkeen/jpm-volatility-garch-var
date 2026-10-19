"""Past-only one-day VaR backtests; importing this module never downloads data."""
import math
import os
import hashlib
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from arch import arch_model


def validate_returns(returns, window):
    if not isinstance(window, int) or isinstance(window, bool) or window < 2:
        raise ValueError("window must be an integer of at least 2")
    if not isinstance(returns, pd.Series) or len(returns) <= window:
        raise ValueError("A return Series longer than the training window is required")
    if not returns.index.is_unique or not returns.index.is_monotonic_increasing:
        raise ValueError("Returns must have a unique, increasing index")
    if not np.isfinite(returns.to_numpy(dtype=float)).all():
        raise ValueError("Returns must be finite; resolve missing data before backtesting")
    return returns.astype(float) * 100


def kupiec_lr(num_breaches, num_obs, probability=0.05):
    """Unconditional coverage LR, including the finite boundary likelihoods."""
    if num_obs <= 0 or not 0 <= num_breaches <= num_obs or not 0 < probability < 1:
        raise ValueError("Invalid breach counts or probability")
    x, n = num_breaches, num_obs
    pi_hat = x / n
    null = (n - x) * math.log1p(-probability) + x * math.log(probability)
    alternative = 0.0
    if x:
        alternative += x * math.log(pi_hat)
    if n - x:
        alternative += (n - x) * math.log1p(-pi_hat)
    return max(0.0, -2 * (null - alternative))


def evaluate(returns_pct, thresholds, label):
    actual = returns_pct.loc[thresholds.index]
    if thresholds.empty or not np.isfinite(thresholds.to_numpy()).all():
        raise ValueError("No complete, finite forecasts to evaluate")
    breaches = actual < thresholds
    rate = 100 * float(breaches.mean())
    lr = kupiec_lr(int(breaches.sum()), len(breaches))
    decision = "Reject" if lr > 3.841458820694124 else "Fail to reject"
    print(f"\n--- {label} ---")
    print(f"Out-of-sample observations: {len(actual)}")
    print(f"Breach rate: {rate:.2f}% | Kupiec LR: {lr:.4f}")
    print(f"{decision} nominal 5% unconditional coverage at the 5% level.")
    print("Non-rejection does not establish model validity or breach independence.")
    return thresholds, actual, breaches, rate, lr


def run_garch_var(returns, label, window=250):
    """Refit on the prior window for each target; forecast its return quantile."""
    returns_pct = validate_returns(returns, window)
    target_index = returns_pct.index[window:]
    volatilities, thresholds = [], []
    for target in range(window, len(returns_pct)):
        training = returns_pct.iloc[target - window:target]
        if training.var() <= 0:
            raise ValueError("GARCH requires a nonconstant training window")
        model = arch_model(training, mean="Constant", vol="Garch", p=1, q=1,
                           dist="normal", rescale=False)
        fitted = model.fit(disp="off")
        if fitted.convergence_flag != 0:
            raise RuntimeError(f"GARCH fit did not converge for {returns_pct.index[target]}")
        forecast = fitted.forecast(horizon=1, reindex=False)
        mean = float(forecast.mean.iloc[-1, 0])
        variance = float(forecast.variance.iloc[-1, 0])
        if not math.isfinite(mean) or not math.isfinite(variance) or variance <= 0:
            raise RuntimeError("GARCH returned an invalid forecast")
        sigma = math.sqrt(variance)
        volatilities.append(sigma)
        thresholds.append(mean + NormalDist().inv_cdf(0.05) * sigma)
    volatility = pd.Series(volatilities, index=target_index, name="forecast_volatility_pct")
    threshold = pd.Series(thresholds, index=target_index, name="garch_threshold_pct")
    return (volatility, *evaluate(returns_pct, threshold, label))


def run_historical_var(returns, label, window=250):
    """The target observation never contributes to its own threshold."""
    returns_pct = validate_returns(returns, window)
    threshold = returns_pct.rolling(window=window).quantile(0.05).shift(1).iloc[window:]
    return evaluate(returns_pct, threshold, label)


def main():
    # -----------------------------
    # 1. Download historical data
    # -----------------------------
    ticker = "JPM"
    start_date = "2020-01-01"
    end_date = "2025-01-01"

    data = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        progress=False
    )

    prices_close = data["Close"].squeeze()

    if "Adj Close" in data.columns:
        prices_adj = data["Adj Close"].squeeze()
    else:
        raise ValueError("Adjusted Close is unavailable; refusing a mislabeled comparison.")

    os.makedirs("outputs", exist_ok=True)
    snapshot = Path("outputs/price_snapshot.csv")
    pd.DataFrame({"Close": prices_close, "Adj Close": prices_adj}).to_csv(snapshot, index_label="date")
    manifest = {
        "status": "started",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "ticker": ticker, "start": start_date, "end_exclusive": end_date,
        "training_window": 250, "python": platform.python_version(),
        "packages": {name: version(name) for name in ["numpy", "pandas", "arch", "yfinance", "matplotlib"]},
        "price_snapshot_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "data_boundary": "Current download; not an authenticated historical point-in-time vintage",
    }
    Path("outputs/run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


    # -----------------------------
    # 2. Compute log returns
    # -----------------------------
    returns_close = np.log(prices_close / prices_close.shift(1)).dropna()
    returns_adj = np.log(prices_adj / prices_adj.shift(1)).dropna()


    # -----------------------------
    # 3. Run both models
    # -----------------------------
    garch_close, var_close, ret_close, br_close, rate_close, kupiec_close = run_garch_var(
        returns_close, "Log Returns Using Close"
    )

    garch_adj, var_adj, ret_adj, br_adj, rate_adj, kupiec_adj = run_garch_var(
        returns_adj, "Log Returns Using Adjusted Close"
    )

    hist_var_close, hist_ret_close, hist_br_close, hist_rate_close, hist_kupiec_close = run_historical_var(
        returns_close, "Historical Simulation VaR Using Close", window=250
    )

    hist_var_adj, hist_ret_adj, hist_br_adj, hist_rate_adj, hist_kupiec_adj = run_historical_var(
        returns_adj, "Historical Simulation VaR Using Adjusted Close", window=250
    )

    # -----------------------------
    # 4. Plot comparison
    # -----------------------------
    plt.figure(figsize=(12, 10))

    # -----------------------------
    # Close-based comparison
    # -----------------------------
    plt.subplot(2, 1, 1)

    plt.plot(var_close, label="95% GARCH VaR (Close)", color="blue")
    plt.plot(hist_var_close, label="95% Historical VaR (Close)", color="green", linestyle="--")
    plt.plot(ret_close, label="Returns", alpha=0.4, color="orange")

    breach_points_garch_close = ret_close[br_close]
    plt.scatter(
        breach_points_garch_close.index,
        breach_points_garch_close.values,
        color="red",
        s=35,
        edgecolor="black",
        linewidth=0.5,
        label="GARCH Breaches"
    )

    breach_points_hist_close = hist_ret_close[hist_br_close]
    plt.scatter(
        breach_points_hist_close.index,
        breach_points_hist_close.values,
        color="purple",
        s=30,
        edgecolor="black",
        linewidth=0.5,
        label="Historical Breaches"
    )

    plt.title(
        f"Close Prices | GARCH Breach Rate: {rate_close:.2f}% | Hist Breach Rate: {hist_rate_close:.2f}%"
    )
    plt.ylabel("Return / VaR")
    plt.legend(loc="upper right")
    plt.grid(alpha=0.3)

    # -----------------------------
    # Adjusted-close-based comparison
    # -----------------------------
    plt.subplot(2, 1, 2)

    plt.plot(var_adj, label="95% GARCH VaR (Adjusted Close)", color="blue")
    plt.plot(hist_var_adj, label="95% Historical VaR (Adjusted Close)", color="green", linestyle="--")
    plt.plot(ret_adj, label="Returns", alpha=0.4, color="orange")

    breach_points_garch_adj = ret_adj[br_adj]
    plt.scatter(
        breach_points_garch_adj.index,
        breach_points_garch_adj.values,
        color="red",
        s=35,
        edgecolor="black",
        linewidth=0.5,
        label="GARCH Breaches"
    )

    breach_points_hist_adj = hist_ret_adj[hist_br_adj]
    plt.scatter(
        breach_points_hist_adj.index,
        breach_points_hist_adj.values,
        color="purple",
        s=30,
        edgecolor="black",
        linewidth=0.5,
        label="Historical Breaches"
    )

    plt.title(
        f"Adjusted Close Prices | GARCH Breach Rate: {rate_adj:.2f}% | Hist Breach Rate: {hist_rate_adj:.2f}%"
    )
    plt.ylabel("Return / VaR")
    plt.xlabel("Date")
    plt.legend(loc="upper right")
    plt.grid(alpha=0.3)

    plt.tight_layout()
    os.makedirs("outputs", exist_ok=True)
    plt.savefig("outputs/garch_vs_historical_var.png", dpi=300, bbox_inches="tight")
    for name, actual, garch, historical in [
        ("close", ret_close, var_close, hist_var_close),
        ("adjusted_close", ret_adj, var_adj, hist_var_adj),
    ]:
        pd.DataFrame({"return_pct": actual, "garch_threshold_pct": garch,
                      "historical_threshold_pct": historical}).to_csv(
            f"outputs/{name}_backtest.csv", index_label="date")
    manifest["status"] = "complete"
    manifest["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["output_sha256"] = {
        name: hashlib.sha256(Path("outputs", name).read_bytes()).hexdigest()
        for name in ["close_backtest.csv", "adjusted_close_backtest.csv", "garch_vs_historical_var.png"]
    }
    Path("outputs/run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if "agg" != plt.get_backend().lower():
        plt.show()

if __name__ == "__main__":
    main()
