# TradeLens — Project Documentation

## 1. Project Overview

TradeLens is a Python-based systematic investing and strategy-validation project for Indian equities.

The current implementation focuses on a simple, rules-based **Classic 12–1 Momentum** strategy applied to the Nifty 500 universe.

TradeLens currently has two primary functions:

1. Generate the current monthly **Top 30 momentum portfolio**
2. Validate the 12–1 momentum strategy through historical backtesting and robustness analysis

The project is designed to prioritize:

* Objective rules
* Reproducibility
* Avoidance of look-ahead bias
* Minimal discretionary decision-making
* Robustness rather than backtest optimization
* Clear documentation of data and methodology limitations

TradeLens is a research and decision-support system. It does not guarantee investment returns.

---

# 2. Current Strategy

The current strategy is **Classic 12–1 Momentum**.

For every eligible stock, momentum is calculated as:

```text
Momentum = Price[t-1] / Price[t-12] - 1
```

Where:

* `t-1` = latest completed month
* `t-12` = the month 12 months before the latest completed month

The most recent incomplete month is excluded from the signal.

Stocks are ranked cross-sectionally according to their momentum.

The live portfolio selects the **Top 30 stocks** and assigns equal weights.

---

# 3. Current Strategy Specification

| Component              | Current implementation         |
| ---------------------- | ------------------------------ |
| Market                 | Indian equities                |
| Universe               | Nifty 500                      |
| Momentum               | Classic 12–1                   |
| Momentum formula       | `Price[t-1] / Price[t-12] - 1` |
| Ranking                | Cross-sectional                |
| Live selection         | Top 30                         |
| Weighting              | Equal weight                   |
| Weight per stock       | 3.33%                          |
| Rebalance              | Monthly                        |
| Holding period         | 1 month                        |
| Stop loss              | None                           |
| Target                 | None                           |
| RSI                    | None                           |
| ATR                    | None                           |
| Volume filter          | None                           |
| 52-week-high filter    | None                           |
| Fundamental filters    | None                           |
| Hard filters           | None                           |
| Feature weighting      | None                           |
| Discretionary ranking  | None                           |
| Parameter optimization | None                           |

The strategy is intentionally simple.

---

# 4. Why Classic 12–1 Momentum

The project originally considered a short-term positional trading system using entries, stop losses, targets, technical indicators and risk/reward calculations.

The current direction is different.

TradeLens has been simplified to first test whether a well-defined, widely studied momentum concept can demonstrate robustness without adding numerous additional conditions.

The current research question is:

> Does a simple Classic 12–1 momentum strategy applied to the Nifty 500 produce sufficiently robust results across different portfolio sizes, transaction costs and historical periods?

The purpose is not to discover a combination of parameters that produces the highest historical return.

---

# 5. Live Signal Engine — `main.py`

`main.py` is the current portfolio-generation engine.

Its purpose is to generate the current **Top 30 Classic 12–1 Momentum portfolio**.

The process is:

```text
Refresh Nifty 500 universe
        ↓
Load current universe
        ↓
Download historical market data
        ↓
Cache market data
        ↓
Build monthly price matrix
        ↓
Exclude incomplete current month
        ↓
Calculate 12–1 momentum
        ↓
Rank stocks
        ↓
Select Top 30
        ↓
Assign equal weights
        ↓
Generate CSV
```

---

# 6. Nifty 500 Universe

Before calculating the portfolio, `main.py` calls:

```python
refresh_nifty500_universe()
```

from `trade_data.py`.

The resulting symbols are then loaded from:

```text
universe.py
```

The current implementation therefore uses the current Nifty 500 universe for live portfolio generation.

---

# 7. Market Data

Market data is retrieved using:

```text
yfinance
```

Historical data begins from:

```text
2018-01-01
```

The system uses adjusted price data through:

```python
auto_adjust=True
```

Daily observations are converted into month-end prices before calculating momentum.

---

# 8. Data Validation

Individual securities are skipped if usable historical data cannot be obtained.

The live engine requires a minimum amount of historical data before accepting a security.

The current implementation requires at least:

```text
260 daily observations
```

before a stock is considered usable in the download stage.

After conversion to monthly observations, a minimum of:

```text
13 monthly observations
```

is required.

---

# 9. Market Data Cache

`main.py` stores downloaded market data locally:

```text
tradelens_market_cache_12_1.pkl
```

On subsequent executions, the program attempts to load this cache before downloading the data again.

The cache reduces unnecessary repeated downloads.

If the cache cannot be loaded or does not contain sufficient usable data, the system downloads the market data again.

---

# 10. Monthly Price Matrix

Daily adjusted closing prices are converted to month-end prices using monthly resampling.

Conceptually:

```text
Daily prices
     ↓
Month-end prices
     ↓
Stock × Month matrix
```

Only securities with sufficient monthly history are retained.

---

# 11. Completed-Month Rule

The live strategy must not use the current incomplete month when generating the signal.

The system therefore identifies the latest completed monthly observation and excludes the current incomplete month.

This is important because using the current month's unfinished price could introduce information that would not have been available at the intended monthly decision point.

---

# 12. Momentum Calculation

The current implementation uses Classic 12–1 momentum.

The calculation is:

```text
Momentum = Price[t-1] / Price[t-12] - 1
```

The latest completed month is deliberately excluded from the numerator.

Conceptually:

```text
12 months ago          Latest completed month
     │                         │
     ▼                         ▼
Price[t-12]  ──────────────>  Price[t-1]
                  │
                  └── Momentum measurement
```

Stocks are then ranked from highest to lowest momentum.

---

# 13. Portfolio Selection

The live portfolio selects:

```text
Top 30 stocks
```

after ranking all eligible stocks by 12–1 momentum.

Each stock receives an equal allocation:

```text
1 / 30 = 3.33%
```

The portfolio is therefore not weighted according to:

* Momentum magnitude
* Market capitalization
* Volatility
* Fundamental quality
* Technical indicators

Every selected stock receives the same weight.

---

# 14. Monthly Implementation

The signal generated from the latest completed month is intended for the following holding month.

For example, conceptually:

```text
Completed signal month
        ↓
Calculate momentum
        ↓
Select Top 30
        ↓
Hold during following month
        ↓
Next monthly rebalance
```

The holding period is therefore approximately one month.

There is currently no individual stock stop loss or target.

---

# 15. Live Output

`main.py` generates:

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
* Strategy

Example structure:

| Rank | Symbol | Momentum | Weight | Weight % |
| ---: | ------ | -------: | -----: | -------: |
|    1 | XYZ    |    45.2% | 0.0333 |    3.33% |
|    2 | ABC    |    41.7% | 0.0333 |    3.33% |

The actual values depend on the latest market data.

---

# 16. Backtesting Engine — `backtest.py`

`backtest.py` is the historical validation engine.

It does not generate the live portfolio.

Its purpose is to test the robustness of the underlying Classic 12–1 momentum strategy.

The backtest evaluates:

```text
Top 10
Top 20
Top 30
Top 50
```

portfolio configurations.

This allows the project to determine whether results are highly dependent on a particular portfolio size.

---

# 17. Backtest Strategy

The backtest uses the same basic 12–1 momentum concept:

```text
Momentum = Price[t-1] / Price[t-12] - 1
```

At each monthly rebalance:

1. Use information available through the previous month
2. Calculate momentum
3. Rank stocks cross-sectionally
4. Select the Top N stocks
5. Equal-weight the selected stocks
6. Hold for the following month
7. Rebalance again

No stop loss or price target is used.

---

# 18. Portfolio Sizes Tested

The validation engine tests:

```text
Top 10
Top 20
Top 30
Top 50
```

The live strategy remains:

```text
Top 30
```

The alternative portfolio sizes are used for robustness testing rather than as competing live strategies.

---

# 19. Transaction-Cost Testing

The backtest tests three transaction-cost assumptions:

```text
0.00%
0.10%
0.20%
```

The purpose is to determine how sensitive performance is to trading costs.

The backtest calculates portfolio turnover based on the proportion of holdings that enter or leave the portfolio.

Transaction cost is then applied according to the estimated turnover.

The 0.20% case is used as the conservative reference case in the final summary.

These values are research assumptions and should not be interpreted as exact real-world brokerage, tax or slippage costs.

---

# 20. Gross vs Net Returns

The backtest maintains separate:

```text
Gross return
Net return
```

Gross return represents portfolio performance before the modeled transaction cost.

Net return subtracts the estimated transaction cost.

This distinction allows the effect of trading costs to be evaluated explicitly.

---

# 21. Portfolio Turnover

Turnover is estimated from the overlap between the previous and current portfolios.

If the portfolio contains 30 stocks and 6 stocks are replaced, the simplified turnover estimate is:

```text
6 / 30 = 20%
```

For the first portfolio, turnover is treated as:

```text
100%
```

because there is no previous portfolio against which to measure overlap.

This is an intentionally simplified turnover model.

It does not attempt to model exact order-level execution.

---

# 22. Performance Metrics

The backtest calculates:

### CAGR

Annualized compounded return based on the monthly net-return series.

### Volatility

Annualized volatility calculated from monthly returns.

### Maximum Drawdown

The largest decline from a previous portfolio equity peak.

### Positive Months

Percentage of months with positive net returns.

### Best Month

Highest monthly net return.

### Worst Month

Lowest monthly net return.

### Average Turnover

Average estimated portfolio turnover.

---

# 23. Yearly Results

The backtest also calculates yearly performance.

For each year it records:

* Portfolio size
* Transaction-cost assumption
* Gross return
* Net return
* Average turnover
* Number of months

Output:

```text
12_1_validation_yearly.csv
```

This allows performance to be examined year by year rather than relying only on a single total CAGR.

---

# 24. Trade-Level / Portfolio-Level Records

The validation engine records the portfolio selected at each rebalance date.

Output:

```text
12_1_validation_trades.csv
```

The records include:

* Date
* Portfolio size
* Transaction-cost assumption
* Gross return
* Net return
* Turnover
* Transaction cost
* Selected symbols

This provides a historical record of the portfolios generated by the backtest.

---

# 25. Out-of-Sample Validation

The current implementation separates the historical period chronologically.

The intended separation is:

```text
Training period : 2018–2021
OOS period      : 2022 onward
```

The OOS results are calculated from:

```text
2022-01-31
```

onward.

An important clarification is required:

The strategy has no parameters selected through a training process.

Therefore, this is not a conventional machine-learning-style training/validation workflow.

The training period is primarily used as a chronological separation before the OOS period.

---

# 26. Survivorship-Bias Limitation

The current backtest is **not fully survivorship-bias-free**.

This is one of the most important limitations of the current system.

`universe.py` represents the current Nifty 500 universe.

The backtest does not reconstruct the actual Nifty 500 membership for every historical rebalance date.

Therefore, the system cannot fully reproduce the historical investable universe that would have existed at each point in time.

For example, a stock that entered the Nifty 500 recently may be included in the historical test even though it was not actually a member of the index during earlier periods.

Conversely, stocks that left the index may be absent from the current universe.

Therefore:

> The current backtest should not be described as a completely point-in-time, survivorship-bias-free Nifty 500 backtest.

A true point-in-time implementation would require historical Nifty 500 constituent membership for every rebalance date.

---

# 27. Look-Ahead Bias

The strategy is designed to avoid using future price information when generating a monthly signal.

At signal month `t`, momentum uses:

```text
Price[t-1] / Price[t-12] - 1
```

The subsequent monthly return is then measured using the following month's price movement.

The current incomplete month is excluded from the live signal calculation.

This separation is intended to prevent future prices from influencing the historical signal.

However, avoiding look-ahead bias does not eliminate other sources of backtest bias, including the current-universe survivorship limitation.

---

# 28. No Parameter Optimization

The validation engine deliberately does not search for the combination that produces the highest historical return.

The tested portfolio sizes are predefined:

```text
10 / 20 / 30 / 50
```

The tested transaction costs are predefined:

```text
0.00% / 0.10% / 0.20%
```

No RSI, ATR, volume, moving-average or fundamental parameters are optimized.

The purpose is robustness testing rather than curve fitting.

---

# 29. Robustness Philosophy

A strategy should not be considered reliable simply because one historical configuration produced an attractive CAGR.

TradeLens therefore examines:

* Different portfolio sizes
* Different transaction costs
* Yearly returns
* Maximum drawdown
* Volatility
* Positive-month percentage
* Portfolio turnover
* Out-of-sample performance

The preferred outcome is a strategy that remains reasonably effective when assumptions change.

---

# 30. Strategy Freeze

The current live strategy is considered **frozen**.

Current configuration:

```text
Universe       : Nifty 500
Momentum       : Classic 12–1
Selection      : Top 30
Weight         : Equal weight
Rebalance      : Monthly
Holding        : 1 month
Stop loss      : None
Target         : None
Optimization   : None
```

The backtest may evaluate alternative portfolio sizes for robustness, but this does not automatically change the live strategy.

Any future modification should be treated as a new strategy version and validated independently.

---

# 31. Project Files

Current core files:

```text
TradeLens/
│
├── main.py
├── backtest.py
├── trade_data.py
├── universe.py
├── README.md
├── PROJECT_DOCUMENTATION.md
└── .gitignore
```

Generated files may include:

```text
tradelens_market_cache_12_1.pkl
current_12_1_top30.csv
12_1_validation_results.csv
12_1_validation_yearly.csv
12_1_validation_trades.csv
```

Generated files are produced by executing the corresponding scripts and may not exist in a fresh clone.

---

# 32. Role of Each Core Python File

## `main.py`

Live/current portfolio signal generation.

Responsible for:

* Loading the universe
* Downloading market data
* Caching market data
* Building monthly prices
* Calculating momentum
* Selecting Top 30
* Generating the current portfolio CSV

---

## `backtest.py`

Historical strategy validation.

Responsible for:

* Downloading historical data
* Building monthly data
* Calculating historical momentum
* Testing Top 10/20/30/50
* Applying transaction-cost assumptions
* Calculating performance metrics
* Producing yearly results
* Producing OOS results
* Recording historical portfolio selections

---

## `trade_data.py`

Responsible for refreshing the Nifty 500 stock universe used by the project.

---

## `universe.py`

Contains the stock symbols used by the strategy.

---

# 33. Data Cost Constraint

TradeLens initially uses freely accessible market-data sources.

The current implementation uses:

```text
yfinance
```

No paid market-data subscription is required for the current development implementation.

However, free data should not automatically be assumed to be:

* Complete
* Error-free
* Point-in-time
* Suitable for institutional research
* Suitable for guaranteed live execution

Data limitations must be considered when interpreting results.

---

# 34. Current Data Limitations

The current implementation has several important data limitations:

1. The historical universe is not point-in-time.
2. Historical Nifty 500 membership is not reconstructed.
3. Exact execution prices are not modeled.
4. Slippage is not explicitly modeled.
5. Taxes are not modeled.
6. Brokerage and exchange charges are not modeled individually.
7. Corporate-event effects depend on the underlying data provided by `yfinance`.
8. The cache is local and should not be treated as a permanent authoritative market-data store.

These limitations should be addressed before relying on the results for high-confidence investment conclusions.

---

# 35. Running the Current Portfolio Generator

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Run:

```powershell
python main.py
```

The program generates:

```text
current_12_1_top30.csv
```

The resulting portfolio represents the current Top 30 stocks according to the frozen Classic 12–1 momentum methodology.

---

# 36. Running the Backtest

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Run:

```powershell
python backtest.py
```

The program evaluates:

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

The main outputs are:

```text
12_1_validation_results.csv
12_1_validation_yearly.csv
12_1_validation_trades.csv
```

---

# 37. Development Philosophy

TradeLens follows these principles:

### Evidence over intuition

Strategy decisions should be supported by measurable evidence.

### Simplicity over unnecessary complexity

A simple strategy should be tested before adding additional indicators and filters.

### Robustness over backtest perfection

A slightly less impressive but stable strategy is preferable to an extremely optimized historical result.

### No optimization for a desired outcome

The strategy should not be repeatedly modified simply because the backtest result is disappointing.

### No forced trade

For the current monthly portfolio strategy, the system follows the predefined Top 30 selection rather than inventing discretionary signals.

### Understanding over blind code generation

Every important component should be understood by the developer before it becomes part of the permanent system.

---

# 38. Development Roadmap

## Phase 1 — Environment and Repository

Completed:

* Python environment
* VS Code setup
* Virtual environment
* Git repository
* GitHub repository
* `.gitignore`
* README
* Project documentation

---

## Phase 2 — Core Python Development

Completed/currently developed:

* Python modules
* Functions
* Exception handling
* File handling
* Pandas
* NumPy
* Time-series processing
* External data retrieval
* CSV generation

---

## Phase 3 — Nifty 500 Universe

Completed/current:

* Nifty 500 universe retrieval
* Symbol storage
* Universe loading
* Universe integration with the signal engine

---

## Phase 4 — Classic 12–1 Momentum

Completed:

* Monthly price construction
* Completed-month handling
* 12–1 momentum calculation
* Cross-sectional ranking
* Top 30 selection
* Equal weighting
* Monthly portfolio generation

---

## Phase 5 — Backtesting

Completed/current:

* Historical market-data download
* Monthly price matrix
* Portfolio simulation
* Multiple portfolio sizes
* Transaction-cost testing
* Turnover estimation
* Performance metrics
* Yearly results
* OOS results
* Historical portfolio records

---

## Phase 6 — Validation Improvements

Future work may include:

* Historical point-in-time Nifty 500 membership
* More accurate transaction-cost modeling
* Explicit slippage modeling
* Corporate-action validation
* More rigorous walk-forward methodology
* Benchmark comparison
* Sector exposure analysis
* Concentration analysis
* Liquidity analysis
* Additional robustness tests

---

## Phase 7 — Paper Portfolio Validation

After the strategy and data methodology are sufficiently validated:

* Generate monthly portfolios
* Track actual portfolio performance
* Record turnover
* Record deviations from theoretical returns
* Compare live/paper results with backtest expectations

---

## Phase 8 — Real-World Evaluation

Only after sufficient historical and paper-trading evidence should real-money deployment be considered.

Any live deployment should begin cautiously and should not assume that historical backtest performance will continue.

---

# 39. What the Current Project Does NOT Do

The current implementation does **not**:

* Predict individual stock prices
* Generate intraday signals
* Generate stop-loss levels
* Generate price targets
* Calculate 1:2 risk/reward trade setups
* Use RSI
* Use ATR
* Use volume confirmation
* Use technical breakout filters
* Use fundamental filters
* Use sector-strength filters
* Optimize parameters
* Automatically place broker orders
* Guarantee returns

These may be considered future research areas, but they are not part of the current frozen strategy.

---

# 40. Current Project Status

**Current phase: Classic 12–1 Momentum implementation and validation**

Completed:

* Python development environment
* Git/GitHub project
* Nifty 500 universe integration
* Historical market-data retrieval
* Market-data caching
* Monthly price construction
* Classic 12–1 momentum calculation
* Top 30 portfolio generation
* Equal weighting
* Monthly rebalance methodology
* Historical backtesting
* Top 10/20/30/50 robustness testing
* Transaction-cost testing
* Yearly performance analysis
* OOS performance analysis

Current focus:

**Validate whether Classic 12–1 Momentum demonstrates sufficient robustness before adding unnecessary strategy complexity.**

---

# 41. Validation Standard

A favorable backtest alone is not sufficient evidence to declare the strategy successful.

Before considering the strategy robust, TradeLens should eventually establish that:

* Results are not dependent on one portfolio size
* Results remain reasonable after transaction costs
* Results are not concentrated in one exceptional period
* Drawdowns are acceptable
* OOS performance remains meaningful
* The strategy survives reasonable methodology changes
* Data limitations are understood
* Survivorship bias is addressed as far as practical
* Paper-trading performance is consistent with expectations

---

# 42. Future Strategy Changes

If the strategy is changed substantially, the new version should be treated as a separate strategy.

Examples:

```text
Classic 12–1 Momentum v1
Classic 12–1 Momentum v2
```

A version change should document:

* What changed
* Why it changed
* What evidence motivated the change
* Whether the change was specified before testing
* Backtest results
* OOS results
* Robustness results

This is intended to prevent silent strategy drift.

---

# 43. Guiding Principles

TradeLens follows these principles:

**Evidence > intuition**

**Risk-adjusted robustness > maximum historical return**

**Simple rules > unnecessary complexity**

**Out-of-sample evidence > in-sample performance**

**Robustness > backtest perfection**

**Understanding > blindly generated code**

**A known limitation > a misleading claim of accuracy**

---

# 44. Disclaimer

TradeLens is an educational and research project.

Historical backtest results do not guarantee future performance.

The current backtest has a known survivorship-bias limitation because historical Nifty 500 membership is not reconstructed for every historical rebalance date.

Market data may contain errors, omissions or adjustments that affect results.

The backtest does not fully model all real-world trading costs, taxes, slippage, liquidity constraints or execution differences.

TradeLens outputs should therefore be treated as research information and not as a guarantee of profit or personalized financial advice.
