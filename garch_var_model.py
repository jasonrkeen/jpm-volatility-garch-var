import math
import os
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from arch import arch_model


def run_garch_var(returns, label):
    returns_pct = returns * 100

    model = arch_model(returns_pct, vol="Garch", p=1, q=1)
    results = model.fit(disp="off")

    garch_vol = results.conditional_volatility
    var_95 = -1.65 * garch_vol

    returns_aligned, var_aligned = returns_pct.align(var_95, join="inner", axis=0)

    breaches = returns_aligned < var_aligned
    num_breaches = int(breaches.sum())
    num_obs = len(returns_aligned)
    breach_rate = (num_breaches / num_obs) * 100

    x = num_breaches
    n = num_obs
    p = 0.05

    if x == 0 or x == n:
        kupiec_lr = float("inf")
        kupiec_result = "Reject model adequacy (edge-case breach count)."
    else:
        pi_hat = x / n
        log_l_null = (n - x) * math.log(1 - p) + x * math.log(p)
        log_l_alt = (n - x) * math.log(1 - pi_hat) + x * math.log(pi_hat)
        kupiec_lr = -2 * (log_l_null - log_l_alt)

        if kupiec_lr > 3.841:
            kupiec_result = "Reject the VaR model at the 5% level."
        else:
            kupiec_result = "Fail to reject the VaR model at the 5% level."

    print(f"\n--- {label} ---")
    print(f"Total observations: {num_obs}")
    print(f"Number of breaches: {num_breaches}")
    print(f"Breach rate: {breach_rate:.2f}%")
    print(f"Kupiec LR statistic: {kupiec_lr:.4f}")
    print(kupiec_result)

    return garch_vol, var_aligned, returns_aligned, breaches, breach_rate, kupiec_lr

def run_historical_var(returns, label, window=250):
    returns_pct = returns * 100

    hist_var_95 = returns_pct.rolling(window=window).quantile(0.05)
    returns_aligned, var_aligned = returns_pct.align(hist_var_95, join="inner", axis=0)
    valid = var_aligned.notna()

    returns_aligned = returns_aligned[valid]
    var_aligned = var_aligned[valid]

    breaches = returns_aligned < var_aligned
    num_breaches = int(breaches.sum())
    num_obs = len(returns_aligned)
    breach_rate = (num_breaches / num_obs) * 100

    x = num_breaches
    n = num_obs
    p = 0.05

    if x == 0 or x == n:
        kupiec_lr = float("inf")
        kupiec_result = "Reject model adequacy (edge-case breach count)."
    else:
        pi_hat = x / n
        log_l_null = (n - x) * math.log(1 - p) + x * math.log(p)
        log_l_alt = (n - x) * math.log(1 - pi_hat) + x * math.log(pi_hat)
        kupiec_lr = -2 * (log_l_null - log_l_alt)

        if kupiec_lr > 3.841:
            kupiec_result = "Reject the VaR model at the 5% level."
        else:
            kupiec_result = "Fail to reject the VaR model at the 5% level."

    print(f"\n--- {label} ---")
    print(f"Rolling window: {window} days")
    print(f"Total observations: {num_obs}")
    print(f"Number of breaches: {num_breaches}")
    print(f"Breach rate: {breach_rate:.2f}%")
    print(f"Kupiec LR statistic: {kupiec_lr:.4f}")
    print(kupiec_result)

    return var_aligned, returns_aligned, breaches, breach_rate, kupiec_lr

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
    prices_adj = prices_close.copy()
    print("Adj Close not found; using Close instead.")


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
os.makedirs("images", exist_ok=True)
plt.savefig("images/garch_vs_historical_var.png", dpi=300, bbox_inches="tight")
plt.show()