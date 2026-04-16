import math

import matplotlib.pyplot as plt
import yfinance as yf
from arch import arch_model


# -----------------------------
# 1. Download historical data
# -----------------------------
ticker = "JPM"
start_date = "2020-01-01"
end_date = "2025-01-01"

data = yf.download(ticker, start=start_date, end=end_date)

# Force Close prices into a Series
prices = data["Close"].squeeze()


# -----------------------------
# 2. Compute returns
# -----------------------------
returns = prices.pct_change().dropna()
returns_pct = returns * 100  # GARCH typically uses percentage returns


# -----------------------------
# 3. Fit GARCH(1,1) model
# -----------------------------
model = arch_model(returns_pct, vol="Garch", p=1, q=1)
results = model.fit(disp="off")

print("\nGARCH(1,1) Model Summary:\n")
print(results.summary())


# -----------------------------
# 4. Extract volatility + VaR
# -----------------------------
garch_vol = results.conditional_volatility
var_95 = -1.65 * garch_vol  # 95% one-day VaR under normality assumption


# -----------------------------
# 5. Align series for backtesting
# -----------------------------
returns_aligned, var_aligned = returns_pct.align(var_95, join="inner", axis=0)


# -----------------------------
# 6. VaR backtest
# -----------------------------
breaches = returns_aligned < var_aligned
num_breaches = int(breaches.sum())
num_obs = len(returns_aligned)
breach_rate = (num_breaches / num_obs) * 100
expected_breach_rate = 0.05

print("\nVaR Backtest Results:")
print(f"Total observations: {num_obs}")
print(f"Number of breaches: {num_breaches}")
print(f"Breach rate: {breach_rate:.2f}%")
print("Expected breach rate for 95% VaR: 5.00%")


# -----------------------------
# 7. Kupiec test
# -----------------------------
# Null hypothesis: observed breach frequency equals expected VaR breach probability
# LR_uc = -2 * ln( ((1-p)^(n-x) * p^x) / ((1-x/n)^(n-x) * (x/n)^x) )
# Approx. chi-square with 1 degree of freedom
#
# Critical value at 5% significance for chi-square(1): 3.841

x = num_breaches
n = num_obs
p = expected_breach_rate

# Handle edge cases safely
if x == 0 or x == n:
    kupiec_lr = float("inf")
    kupiec_result = "Reject model adequacy (edge-case breach count)."
else:
    pi_hat = x / n

    log_l_null = (n - x) * math.log(1 - p) + x * math.log(p)
    log_l_alt = (n - x) * math.log(1 - pi_hat) + x * math.log(pi_hat)

    kupiec_lr = -2 * (log_l_null - log_l_alt)

    critical_value_5pct = 3.841

    if kupiec_lr > critical_value_5pct:
        kupiec_result = "Reject the VaR model at the 5% level."
    else:
        kupiec_result = "Fail to reject the VaR model at the 5% level."

print("\nKupiec Test Results:")
print(f"Kupiec LR statistic: {kupiec_lr:.4f}")
print("Chi-square critical value (95%, df=1): 3.841")
print(kupiec_result)


# -----------------------------
# 8. Plot results
# -----------------------------
plt.figure(figsize=(10, 8))

plt.subplot(2, 1, 1)
plt.plot(garch_vol, label="Conditional Volatility")
plt.title(f"GARCH Volatility ({ticker})")
plt.ylabel("Volatility")
plt.legend()

plt.subplot(2, 1, 2)
plt.plot(var_aligned, label="95% VaR")
plt.plot(returns_aligned, label="Actual Returns", alpha=0.4)

# Add breach markers
breach_points = returns_aligned[breaches]
plt.scatter(
    breach_points.index,
    breach_points.values,
    color="red",
    s=35,
    edgecolor="black",
    linewidth=0.5,
    label="VaR Breaches"
)

plt.title(f"95% Value at Risk Backtest ({ticker})")
plt.ylabel("Return / VaR")
plt.xlabel("Date")
plt.legend()

plt.tight_layout()
plt.savefig("images/var_backtest.png", dpi=300, bbox_inches="tight")
plt.show()