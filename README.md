# TradeLens

**Classic 12–1 Momentum — Nifty 500 Top 30**

TradeLens is a Python-based systematic investing research and signal engine.

The current implementation is intentionally simple and frozen:

* **Universe:** Latest Nifty 500
* **Strategy:** Classic 12–1 momentum
* **Selection:** Top 30 stocks
* **Weighting:** Equal weight
* **Rebalance:** Monthly
* **Holding period:** 1 month
* **Stop loss:** None
* **Target:** None
* **Optimization:** None

The project currently focuses on building a clean, reproducible momentum strategy and validating it before introducing additional complexity.

---

## ⚠️ Important — How to Run

The latest Nifty 500 universe is refreshed automatically every time `main.py` runs.

The market-data cache is **not treated as the stock universe**.

When `main.py` runs, TradeLens:

1. Refreshes the latest Nifty 500 membership.
2. Loads the existing market-data cache, if available.
3. Compares the cache with the current Nifty 500 universe.
4. Downloads historical data for newly added/missing constituents.
5. Keeps existing cached data where available.
6. Excludes stocks that are no longer in the current Nifty 500.
7. Saves the reconciled market-data cache.
8. Calculates the current Top 30 portfolio using only current Nifty 500 constituents.

### Normal run

```powershell
python main.py
```

**You do NOT need to manually delete `tradelens_market_cache_12_1.pkl` before each run.**

The cache is a price-data cache, not a permanent list of Nifty 500 stocks.

---

## Strategy

TradeLens currently implements the **Classic 12–1 Momentum** strategy.

### Momentum formula

```text
Momentum = Price[t-1] / Price[t-12] - 1
```

Where:

* `t-1` = latest completed month used for the signal
* `t-12` = price 12 months before that
* The latest incomplete/current month is excluded

This is the traditional 12–1 momentum concept: the most recent month is skipped to reduce the influence of short-term reversal effects.

### Portfolio construction

* Rank eligible Nifty 500 stocks by 12–1 momentum.
* Select the top 30.
* Allocate equal weight to each stock.
* Rebalance monthly.
* Hold the portfolio for the following month.

Each selected stock therefore receives:

```text
1 / 30 = 3.33%
```

---

## Current Output

`main.py` produces:

```text
current_12_1_top30.csv
```

The file contains:

* Rank
* Symbol
* Momentum
* Weight
* Weight percentage
* Signal month
* Holding month
* Strategy

The output represents the **current Top 30 portfolio signal**.

---

## Market Data

TradeLens currently uses:

**Yahoo Finance / `yfinance`**

Historical adjusted closing prices are downloaded from Yahoo Finance.

The project currently uses free market data and therefore does not require a paid market-data subscription.

### Data limitations

Free data may contain:

* Missing observations
* Delisted-stock limitations
* Corporate-action complexities
* Historical data inconsistencies
* Temporary download failures
* Availability limitations

Therefore, data quality must be considered when interpreting backtest results.

---

## Market-Data Cache

TradeLens stores downloaded price data locally in:

```text
tradelens_market_cache_12_1.pkl
```

The cache exists to avoid unnecessarily downloading the complete historical dataset every time.

Importantly, the cache is **not the Nifty 500 universe**.

The current universe comes from the refreshed `universe.py`.

If the Nifty 500 changes:

```text
Latest Nifty 500
       ↓
Compare with cache
       ↓
New constituent?
       ↓
Download missing data
       ↓
Remove/exclude former constituents from active calculation
       ↓
Calculate Top 30
```

This means manual cache deletion is not required during normal operation.

---

## Backtesting

`backtest.py` is the validation engine for the Classic 12–1 momentum strategy.

It tests:

* Top 10
* Top 20
* Top 30
* Top 50

and evaluates multiple transaction-cost assumptions:

* 0 bps
* 10 bps
* 20 bps

The backtest reports:

* CAGR
* Volatility
* Maximum drawdown
* Positive-month percentage
* Best month
* Worst month
* Average turnover
* Yearly returns
* Gross returns
* Net returns
* Transaction costs

It also produces out-of-sample results from 2022 onward.

### Important limitation

The current `universe.py` represents the **current Nifty 500 universe**.

Therefore, `backtest.py` cannot reconstruct the actual historical Nifty 500 membership for every historical rebalance date.

As a result, the backtest is **not completely survivorship-bias-free**.

It is therefore a robustness/validation test using the current universe rather than a true point-in-time historical Nifty 500 backtest.

A true point-in-time test requires historical Nifty 500 constituent membership for every rebalance date.

---

## Validation Philosophy

TradeLens is deliberately avoiding strategy optimization.

The current Classic 12–1 strategy does not use:

* RSI
* ATR
* Volume filters
* 52-week-high filters
* Stop losses
* Price targets
* Discretionary ranking
* Optimized feature weights

The objective is to determine whether a simple, well-known momentum effect demonstrates a sufficiently robust historical edge before adding complexity.

The project values:

**Evidence > intuition**

**Robustness > backtest perfection**

**Risk-adjusted returns > raw returns**

**Simple rules > unnecessary complexity**

---

## Project Structure

```text
TradeLens/
│
├── main.py
├── backtest.py
├── trade_data.py
├── trade_calculator.py
├── universe.py
├── README.md
├── .gitignore
│
├── docs/
│   └── PROJECT_DOCUMENTATION.md
│
└── output files
    ├── current_12_1_top30.csv
    ├── 12_1_validation_results.csv
    ├── 12_1_validation_yearly.csv
    └── 12_1_validation_trades.csv
```

`universe.py` is refreshed from the latest Nifty 500 membership before `main.py` performs its calculation.

---

## Running the Current Signal Engine

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Run:

```powershell
python main.py
```

The program will refresh the universe, reconcile the cache, download required data, calculate momentum and generate the current Top 30 portfolio.

---

## Running the Backtest

Run:

```powershell
python backtest.py
```

The backtest downloads the required historical data and produces:

```text
12_1_validation_results.csv
12_1_validation_yearly.csv
12_1_validation_trades.csv
```

These files contain the detailed validation results.

---

## Development Philosophy

TradeLens is being developed progressively.

The intended process is:

```text
Understand
    ↓
Implement
    ↓
Test
    ↓
Backtest
    ↓
Validate
    ↓
Paper trade
    ↓
Evaluate
    ↓
Only then consider real money
```

The system should never be made more complicated simply because a more complicated strategy produces a better historical backtest.

---

## Future Development

Potential future work includes:

* True point-in-time Nifty 500 membership
* Better historical data handling
* Slippage modelling
* More accurate transaction-cost modelling
* Walk-forward validation
* Market-regime analysis
* Sector analysis
* Benchmark comparison
* Portfolio turnover analysis
* Paper-trading infrastructure
* Automated signal generation
* Additional strategies only after the current strategy is properly validated

Additional technical indicators and filters should only be introduced when there is a clear research reason for doing so.

---

## Disclaimer

TradeLens is an educational and research project.

It does not guarantee profits or future performance.

Historical backtests are subject to data limitations, modelling assumptions, survivorship bias and other statistical limitations.

TradeLens outputs should not be considered personalized financial advice.
