# JPM Volatility Modeling with GARCH and VaR

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Status](https://img.shields.io/badge/Status-Complete-success)
![Focus](https://img.shields.io/badge/Focus-Quantitative%20Finance-orange)

## Overview

This project analyzes JPMorgan (JPM) stock returns using a **GARCH(1,1)** model to estimate time-varying volatility and compute a **95% one-day Value at Risk (VaR)**.

It demonstrates how volatility clustering impacts downside risk and validates the model using statistical backtesting.

---

## Project Objective

The goal is to model **dynamic market risk** in equity returns and evaluate whether a volatility-based VaR model is properly calibrated.

---

## Methodology

### Data

* Historical price data retrieved using `yfinance`
* Daily log returns computed from adjusted close prices

### Modeling

* GARCH(1,1) model fitted using the `arch` library
* Conditional volatility estimated over time
* VaR calculated as:

[
VaR_{95%} = -1.65 \cdot \sigma_t
]

### Backtesting

* VaR breaches identified where actual returns fall below VaR
* Kupiec Proportion of Failures test applied to evaluate model accuracy

---

## Key Insights

* Volatility spikes significantly during stressed periods (e.g., 2020 market shock)
* Volatility clustering is clearly visible over time
* VaR becomes more negative during high-volatility regimes, indicating increased downside risk

---

## Model Validation

* Observed VaR breach rate: **4.14%**
* Expected breach rate: **5.00%**
* Kupiec LR statistic: **2.09**
* Critical value (95%, df=1): **3.84**

**Result:** Fail to reject the null hypothesis → the VaR model is **well-calibrated**

---

## Results

The chart below shows:

* GARCH conditional volatility
* 95% VaR estimate
* Actual returns
* VaR breach points (highlighted)

![VaR Backtest](images/var_backtest.png)

---

## Project Structure

```
jpm-volatility-garch-var/
│
├── garch_var_model.py      # Main modeling and analysis script
├── requirements.txt       # Dependencies
├── README.md              # Project documentation
└── images/
    └── var_backtest.png   # Output visualization
```

---

## Tools & Libraries

* Python
* pandas
* numpy
* matplotlib
* yfinance
* arch

---

## How to Run

1. Clone the repository:

```bash
git clone https://github.com/jasonrkeen/jpm-volatility-garch-var.git
cd jpm-volatility-garch-var
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the model:

```bash
python garch_var_model.py
```

---

## Future Improvements

* Add rolling-window VaR estimation
* Compare with Historical Simulation VaR
* Implement Conditional Coverage (Christoffersen) test
* Extend to portfolio-level risk modeling

---

## Author

Jason Keen