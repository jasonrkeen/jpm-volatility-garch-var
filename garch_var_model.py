import math
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
    auto_adjust=False
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
    returns_close, "Log Returns using Close"
)

garch_adj, var_adj, ret_adj, br_adj, rate_adj, kupiec_adj = run_garch_var(
    returns_adj, "Log Returns using Adjusted Close"
)


# -----------------------------
# 4. Plot comparison
# -----------------------------
plt.figure(figsize=(12, 10))

plt.subplot(2, 1, 1)
plt.plot(var_close, label="95% VaR (Close)")
plt.plot(ret_close, label="Returns", alpha=0.4)
breach_points_close = ret_close[br_close]
plt.scatter(
    breach_points_close.index,
    breach_points_close.values,
    color="red",
    s=35,
    edgecolor="black",
    linewidth=0.5,
    label="VaR Breaches"
)
plt.title(f"Log Returns Using Close | Breach Rate: {rate_close:.2f}% | Kupiec: {kupiec_close:.2f}")
plt.ylabel("Return / VaR")
plt.legend()

plt.subplot(2, 1, 2)
plt.plot(var_adj, label="95% VaR (Adjusted Close)")
plt.plot(ret_adj, label="Returns", alpha=0.4)
breach_points_adj = ret_adj[br_adj]
plt.scatter(
    breach_points_adj.index,
    breach_points_adj.values,
    color="red",
    s=35,
    edgecolor="black",
    linewidth=0.5,
    label="VaR Breaches"
)
plt.title(f"Log Returns Using Adjusted Close | Breach Rate: {rate_adj:.2f}% | Kupiec: {kupiec_adj:.2f}")
plt.ylabel("Return / VaR")
plt.xlabel("Date")
plt.legend()

plt.tight_layout()
plt.savefig("images/close_vs_adjclose_comparison.png", dpi=300, bbox_inches="tight")
plt.show()