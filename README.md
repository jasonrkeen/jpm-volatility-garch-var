# JPM Volatility and Value at Risk Modeling

This project analyzes JPMorgan (JPM) stock returns using a GARCH(1,1) model to estimate conditional volatility and 95% one-day Value at Risk (VaR).

## Project Objective
The goal of this project is to model time-varying market risk in JPMorgan equity returns and demonstrate how volatility clustering affects downside risk estimates.

## Methods Used
- Historical price retrieval with `yfinance`
- Daily return calculation
- GARCH(1,1) volatility modeling using the `arch` library
- 95% one-day Value at Risk estimation
- Data visualization with `matplotlib`

## Key Insights
- Volatility spikes sharply during stressed market periods, especially in 2020.
- Volatility demonstrates clustering, where high-volatility periods tend to persist.
- Value at Risk becomes significantly more negative during periods of elevated volatility, indicating higher expected downside risk.

## Model Validation

The model was evaluated using Value at Risk (VaR) backtesting and the Kupiec Proportion of Failures test.

- Observed VaR breach rate: 4.14%
- Expected breach rate (95% VaR): 5.00%
- Kupiec test statistic: 2.09
- Critical value (95%, df=1): 3.84

Result: Fail to reject the null hypothesis, indicating the VaR model is well-calibrated.

## Tools
- Python
- yfinance
- matplotlib
- pandas
- numpy
- arch

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt