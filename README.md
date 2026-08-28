# TradeLens

**Classic 12–1 Momentum — Systematic Nifty 500 Portfolio**

TradeLens is a Python-based systematic investing project built around a simple, rules-based **Classic 12–1 Momentum** strategy.

The project has two primary functions:

1. **Generate the current monthly Top 30 momentum portfolio**
2. **Validate the strategy through historical backtesting and robustness testing**

The strategy deliberately avoids discretionary stock selection, technical indicators, stop losses, price targets, and parameter optimization.

---

## Strategy

TradeLens implements the classic **12–1 momentum** concept.

### Momentum Formula

For each stock:

```text
Momentum = Price[t-1] / Price[t-12] - 1
```

Where:

* `t-1` = latest completed month
* `t-12` = price 12 months before the latest completed month
* The most recent incomplete month is excluded

This means the strategy measures approximately **12 months of historical momentum while excluding the most recent month**.

### Portfolio Rules

| Rule                   | Implementation        |
| ---------------------- | --------------------- |
| Universe               | Nifty 500             |
| Signal                 | Classic 12–1 momentum |
| Ranking                | Cross-sectional       |
| Selection              | Top 30                |
| Weighting              | Equal weight          |
| Rebalance              | Monthly               |
| Holding period         | 1 month               |
| Stop loss              | None                  |
| Target                 | None                  |
| RSI                    | None                  |
| ATR                    | None                  |
| Volume filter          | None                  |
| 52-week-high filter    | None                  |
| Fundamental filters    | None                  |
| Parameter optimization | None                  |
| Discretionary ranking  | None                  |

Each selected stock receives an equal portfolio weight:

```text
1 / 30 = 3.33%
```

---

# Project Components

## `main.py`

`main.py` is the **live portfolio signal engine**.

It:

1. Refreshes the current Nifty 500 universe
2. Loads the current stock universe
3. Downloads historical adjusted price data using `yfinance`
4. Caches the downloaded data locally
5. Converts daily prices into month-end prices
6. Uses only the latest completed month
7. Calculates 12–1 momentum for every eligible stock
8. Ranks stocks by momentum
9. Selects the Top 30
10. Assigns equal weights
11. Saves the current portfolio to CSV

### Output

```text
current_12_1_top30.csv
```

The output contains:

* Rank
* Symbol
* Momentum
* Weight
* Weight percentage
* Signal month
* Holding month
* Strategy name

---

# `backtest.py`

`backtest.py` is the **strategy validation and robustness engine**.

It is intentionally separate from the live signal generator.

The backtest tests:

* Top 10 portfolio
* Top 20 portfolio
* Top 30 portfolio
* Top 50 portfolio

It also tests multiple transaction-cost assumptions:

```text
0.00%
0.10%
0.20%
```

The purpose is not to find the combination with the highest historical return.

The purpose is to determine whether the basic 12–1 momentum idea remains reasonably robust when:

* Portfolio size changes
* Transaction costs are introduced
* Performance is examined year by year
* Out-of-sample performance is examined
* Drawdowns and volatility are considered
* Portfolio turnover is measured

---

## Backtest Methodology

### Monthly Rebalancing

At each rebalance date, the strategy:

1. Looks only at information available through the previous completed month
2. Calculates 12–1 momentum
3. Ranks the available stocks
4. Selects the Top N
5. Holds the portfolio for the following month

No future prices are used to generate the signal.

---

## Portfolio Sizes Tested

The validation engine tests:

```text
Top 10
Top 20
Top 30
Top 50
```

This helps determine whether the strategy's performance depends heavily on selecting a particular number of stocks.

---

## Transaction Costs

The backtest tests:

```text
0.00%
0.10%
0.20%
```

Transaction costs are applied according to estimated portfolio turnover.

The 0.20% case is used as the conservative reference case in the final summary.

These are assumptions for validation rather than a claim about the exact trading cost that will occur in live trading.

---

# Performance Metrics

The backtest reports:

### CAGR

Compound annual growth rate of the portfolio.

### Volatility

Annualized volatility calculated from monthly returns.

### Maximum Drawdown

The largest decline from a previous portfolio equity peak.

### Positive Months

Percentage of months producing a positive net return.

### Best Month

Highest monthly net return.

### Worst Month

Lowest monthly net return.

### Turnover

Estimated proportion of the portfolio that changes during each rebalance.

### Transaction Cost

Estimated cost associated with portfolio turnover.

---

# Yearly Analysis

The backtest also generates year-by-year results.

For each year it records:

* Gross return
* Net return
* Average turnover
* Number of months tested

Output:

```text
12_1_validation_yearly.csv
```

This makes it possible to examine whether the strategy's performance was concentrated in only a small number of years.

---

# Out-of-Sample Validation

The validation engine separates the test chronologically.

The current implementation uses:

```text
Training period : 2018–2021
OOS period      : 2022 onward
```

Importantly, **no strategy parameters are selected from the training period**.

The separation is therefore primarily chronological rather than a conventional parameter-training exercise.

The reported OOS results are intended to provide a more conservative assessment than simply reporting the entire historical period.

---

# Important Survivorship-Bias Limitation

The current implementation does **not** provide a completely survivorship-bias-free backtest.

`universe.py` represents the **current Nifty 500 universe**.

Historical Nifty 500 membership is not reconstructed for every historical rebalance date.

Therefore, the backtest cannot fully answer:

> "What would this strategy have achieved using only the stocks that were actually members of the Nifty 500 at each historical point in time?"

Instead, the current test uses the available current universe consistently across the historical period.

This is an important limitation.

A true point-in-time Nifty 500 backtest would require historical index membership for every rebalance date.

Therefore:

> **The backtest should not be described as completely survivorship-bias-free.**

---

# Why the Strategy Is Intentionally Simple

TradeLens does not currently attempt to combine momentum with numerous additional filters.

There are deliberately:

* No RSI filters
* No ATR filters
* No volume filters
* No moving-average filters
* No fundamental filters
* No stop losses
* No profit targets
* No discretionary ranking
* No feature weighting
* No parameter optimization

The objective is to test whether the basic **12–1 momentum signal itself** has sufficient robustness.

Adding many filters can improve historical results while simultaneously increasing the risk of overfitting.

---

# Data

Market data is obtained using:

```text
yfinance
```

The system downloads historical adjusted price data beginning from:

```text
2018-01-01
```

Daily prices are converted into month-end observations for the momentum calculation.

---

# Data Cache

`main.py` stores downloaded market data locally:

```text
tradelens_market_cache_12_1.pkl
```

This allows subsequent executions to reuse the cached data rather than downloading it again, provided the cache is usable.

---

# Universe

The stock universe is maintained through:

```text
universe.py
```

The current implementation refreshes the Nifty 500 universe through:

```text
trade_data.py
```

before loading the symbols.

The exact historical membership of the Nifty 500 is **not currently reconstructed by the backtest**.

---

# Project Structure

```text
TradeLens/
│
├── main.py
├── backtest.py
├── trade_data.py
├── universe.py
├── README.md
├── PROJECT_DOCUMENTATION.md
├── .gitignore
│
├── tradelens_market_cache_12_1.pkl
├── current_12_1_top30.csv
│
├── 12_1_validation_results.csv
├── 12_1_validation_yearly.csv
└── 12_1_validation_trades.csv
```

Generated data files may not exist until the corresponding scripts have been executed.

---

# Running TradeLens

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

## Generate Current Top 30 Portfolio

Run:

```powershell
python main.py
```

The program calculates the latest completed month's momentum and generates:

```text
current_12_1_top30.csv
```

The portfolio is intended for the month following the signal month.

---

# Run the Backtest

Run:

```powershell
python backtest.py
```

The program tests:

```text
Top 10
Top 20
Top 30
Top 50
```

under:

```text
0.00%
0.10%
0.20%
```

transaction-cost assumptions.

It generates:

```text
12_1_validation_results.csv
12_1_validation_yearly.csv
12_1_validation_trades.csv
```

---

# Validation Philosophy

TradeLens follows a deliberately conservative validation philosophy.

The system should answer:

> **Does a simple, predefined 12–1 momentum strategy remain reasonably robust across portfolio sizes, transaction costs, time periods and out-of-sample data?**

It should **not** answer:

> "Which parameters produce the highest historical CAGR?"

No parameters are optimized by the validation engine.

The objective is to reduce the temptation to repeatedly modify the strategy until the historical backtest looks attractive.

---

# Current Strategy Status

The strategy is currently **frozen**.

Current live configuration:

```text
Universe       : Nifty 500
Strategy       : Classic 12–1 Momentum
Portfolio      : Top 30
Weight         : Equal weight
Rebalance      : Monthly
Holding        : 1 month
Stop loss      : None
Target         : None
Optimization   : None
```

The backtest deliberately tests alternative portfolio sizes to evaluate robustness, but the live implementation remains **Top 30**.

---

# Important Disclaimer

TradeLens is a research and portfolio-analysis project.

Historical backtest performance does not guarantee future returns.

The current backtest has a known survivorship-bias limitation because historical Nifty 500 membership is not reconstructed.

Transaction costs, taxes, slippage, liquidity constraints and execution differences may cause live results to differ from backtest results.

The output should therefore be treated as systematic research information rather than a guarantee of investment performance.
