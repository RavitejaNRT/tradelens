# TradeLens — Project Documentation

## 1. Project Overview

TradeLens is a Python-based systematic investing research and signal engine focused initially on Indian equities listed on the NSE.

The current implementation is deliberately narrow and simple:

**Classic 12–1 Momentum — Nifty 500 Top 30**

The project is designed to research whether a systematic momentum strategy can produce a repeatable historical edge and whether that edge remains robust after accounting for transaction costs and different portfolio sizes.

TradeLens is a research and decision-support system. It is not designed to guarantee profits or predict future stock prices with certainty.

---

# 2. Current Strategy

The current strategy is:

| Component      | Current implementation       |
| -------------- | ---------------------------- |
| Universe       | Latest Nifty 500             |
| Signal         | Classic 12–1 momentum        |
| Formula        | Price[t-1] / Price[t-12] − 1 |
| Ranking        | Cross-sectional              |
| Portfolio      | Top 30                       |
| Weighting      | Equal weight                 |
| Rebalance      | Monthly                      |
| Holding period | 1 month                      |
| Stop loss      | None                         |
| Target         | None                         |
| Optimization   | None                         |
| Hard filters   | None                         |

The strategy is intentionally frozen while it is being validated.

---

# 3. Classic 12–1 Momentum

Classic 12–1 momentum measures the stock's return over approximately the previous 12 months while excluding the most recent month.

The formula is:

```text
Momentum = Price[t-1] / Price[t-12] - 1
```

For a signal generated at month `t`:

* The latest incomplete month is excluded.
* The most recent completed month is excluded from the momentum calculation.
* The calculation uses the completed month preceding it.
* Stocks are ranked against one another.
* The highest-ranking stocks are selected.

This prevents the current incomplete month from influencing the signal.

---

# 4. Universe Management

The strategy uses the **latest Nifty 500 universe**.

Before `main.py` imports the stock list:

```python
refresh_nifty500_universe()
```

is executed.

The refreshed universe is then loaded from:

```text
universe.py
```

The important architectural principle is:

> `universe.py` represents the current universe. The market-data cache does not define the universe.

This distinction is important because Nifty 500 membership changes over time.

---

# 5. Market-Data Cache

Market data is stored locally in:

```text
tradelens_market_cache_12_1.pkl
```

The cache is a **historical price-data cache**, not a stock-universe definition.

Every run performs the following process:

```text
Refresh Nifty 500
       ↓
Load current universe
       ↓
Load existing market-data cache
       ↓
Compare current universe with cached symbols
       ↓
Identify new/missing constituents
       ↓
Download missing historical data
       ↓
Save updated cache
       ↓
Restrict calculation to current Nifty 500
       ↓
Calculate Top 30
```

## 5.1 New Constituents

If a stock has entered the Nifty 500 and is not present in the cache:

* It is identified as missing.
* Historical data is downloaded.
* The data is added to the cache.

## 5.2 Removed Constituents

If a stock exists in the cache but is no longer in the current Nifty 500:

* Its historical data may remain physically stored in the cache.
* It is excluded from the active current-universe calculation.

This avoids unnecessarily deleting useful historical price data while ensuring that former constituents cannot enter the current Top 30 selection.

## 5.3 Operational Requirement

No manual cache deletion is required.

The normal command is simply:

```powershell
python main.py
```

The application is responsible for reconciling the cache with the latest universe.

---

# 6. Historical Market Data

The current implementation uses:

**Yahoo Finance through `yfinance`**

The system downloads historical prices beginning from:

```text
2018-01-01
```

Adjusted prices are used through:

```python
auto_adjust=True
```

The system handles common `yfinance` MultiIndex responses and skips symbols for which usable data cannot be obtained.

---

# 7. Monthly Data Construction

Daily closing-price data is converted into monthly observations.

The month-end observation is used:

```python
series.resample("ME").last()
```

Only stocks with sufficient historical observations are considered usable.

The resulting structure is conceptually:

```text
              STOCK_A   STOCK_B   STOCK_C
2018-01-31       ...       ...       ...
2018-02-28       ...       ...       ...
2018-03-31       ...       ...       ...
...
```

---

# 8. Current Top 30 Portfolio

After calculating 12–1 momentum:

1. Stocks are ranked from highest to lowest momentum.
2. The top 30 are selected.
3. Each stock receives equal weight.

Therefore:

```text
Weight = 1 / 30
       ≈ 3.33%
```

The portfolio is intended to be held for the month following the signal month.

---

# 9. Current Signal Output

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

This file represents the current portfolio generated by the frozen strategy.

---

# 10. No Stop Loss or Target

The current Classic 12–1 portfolio strategy does not use individual stock:

* Stop losses
* Profit targets
* ATR exits
* Technical exits

The strategy's exit mechanism is the monthly rebalance.

A stock remains in the portfolio only while it remains among the selected stocks at the relevant monthly rebalance.

---

# 11. Backtesting Engine

`backtest.py` is the validation engine for the strategy.

It tests multiple portfolio sizes:

```text
Top 10
Top 20
Top 30
Top 50
```

This is not intended to optimize the strategy.

The purpose is to understand whether the strategy's behavior is reasonably robust across different portfolio concentrations.

---

# 12. Transaction-Cost Testing

The backtest evaluates:

```text
0.00%
0.10%
0.20%
```

transaction-cost assumptions.

The backtest calculates portfolio turnover and applies the assumed transaction cost proportionally to turnover.

Performance is reported separately as:

* Gross return
* Net return

This helps determine whether the observed historical edge survives reasonable trading costs.

---

# 13. Backtest Metrics

The validation engine reports:

* Number of months
* CAGR
* Annualized volatility
* Maximum drawdown
* Percentage of positive months
* Best month
* Worst month
* Average turnover

Yearly output additionally includes:

* Gross return
* Net return
* Average turnover
* Number of months

---

# 14. Out-of-Sample Validation

The current validation separates:

```text
Training/reference period:
2018–2021

Out-of-sample period:
2022 onward
```

The strategy has no parameters selected from the training period.

Therefore, the separation is primarily chronological rather than a parameter-optimization process.

The purpose is to examine whether the strategy continues to behave reasonably outside the earlier historical period.

---

# 15. Survivorship-Bias Limitation

This is one of the most important limitations of the current backtest.

The current `universe.py` represents the current Nifty 500 membership.

Historical Nifty 500 membership is not reconstructed for every historical rebalance date.

Therefore, the current backtest does **not** constitute a fully point-in-time, survivorship-bias-free Nifty 500 backtest.

The current test should be interpreted as:

> A robustness and validation test using the current Nifty 500 universe.

It should **not** be interpreted as a completely unbiased reconstruction of what the strategy would have owned historically.

A true point-in-time implementation requires historical Nifty 500 constituent membership for every rebalance date.

---

# 16. Look-Ahead Bias

The strategy is designed so that the current incomplete month does not influence the signal.

The signal uses completed monthly observations.

The momentum calculation excludes the latest completed month and uses the preceding completed month as the latest price in the 12–1 calculation.

This is intended to prevent future information from entering the signal calculation.

---

# 17. Overfitting Philosophy

TradeLens deliberately avoids optimizing parameters merely to improve historical returns.

The current strategy contains:

* No RSI optimization
* No ATR optimization
* No volume multiplier optimization
* No moving-average optimization
* No stop-loss optimization
* No target optimization
* No feature-weight optimization

The purpose is to test a simple established momentum concept first.

A strategy that performs exceptionally well only after extensive parameter tuning should be treated with suspicion.

The project therefore prioritizes:

**Robustness over backtest perfection.**

---

# 18. Validation Framework

The intended validation sequence is:

```text
Strategy definition
        ↓
Historical backtest
        ↓
Transaction-cost testing
        ↓
Portfolio-size sensitivity
        ↓
Out-of-sample testing
        ↓
Market-regime analysis
        ↓
Paper trading
        ↓
Real-world evaluation
```

Additional validation should be performed before real-money deployment.

---

# 19. Paper Trading

Backtest success is not sufficient evidence for immediate real-money deployment.

The intended progression is:

1. Freeze strategy.
2. Validate historical performance.
3. Test robustness.
4. Run paper portfolio.
5. Compare live paper results with expected historical behavior.
6. Evaluate execution and data issues.
7. Consider small real-money deployment only after sufficient evidence.

---

# 20. Development Roadmap

## Phase 1 — Environment

Completed:

* Python installation
* VS Code setup
* Virtual environment
* Git
* GitHub repository
* `.gitignore`
* README
* Project documentation

## Phase 2 — Initial Python Implementation

Completed:

* Market-data retrieval
* Nifty 500 universe refresh
* Market-data caching
* Monthly price construction
* 12–1 momentum calculation
* Cross-sectional ranking
* Top 30 selection
* Equal-weight portfolio
* CSV signal output

## Phase 3 — Validation

Current focus:

* Historical backtesting
* Transaction-cost analysis
* Portfolio-size comparison
* Yearly performance
* Drawdown analysis
* Turnover analysis
* Out-of-sample testing

## Phase 4 — Robustness

Planned:

* Point-in-time Nifty 500 membership
* Slippage modelling
* Better transaction-cost modelling
* Benchmark comparison
* Market-regime analysis
* Sector analysis
* Sensitivity analysis

## Phase 5 — Paper Trading

Planned:

* Automated monthly signals
* Portfolio tracking
* Expected vs actual performance
* Execution tracking
* Drawdown monitoring

## Phase 6 — Real-World Evaluation

Only after sufficient evidence should real-money deployment be considered.

---

# 21. Project Structure

```text
TradeLens/
│
├── main.py
├── backtest.py
├── trade_data.py
├── universe.py
├── trade_calculator.py
├── README.md
├── .gitignore
│
├── docs/
│   └── PROJECT_DOCUMENTATION.md
│
├── tradelens_market_cache_12_1.pkl
├── current_12_1_top30.csv
│
├── 12_1_validation_results.csv
├── 12_1_validation_yearly.csv
└── 12_1_validation_trades.csv
```

Generated files may not necessarily be committed to Git, depending on `.gitignore` configuration.

---

# 22. Core Design Principles

TradeLens follows these principles:

### Evidence > intuition

Strategy decisions should be supported by measurable evidence.

### Risk-adjusted returns > raw returns

High returns accompanied by excessive drawdown are not automatically desirable.

### Robustness > backtest perfection

A strategy that works reasonably across different conditions is preferable to one that produces spectacular results only under one configuration.

### No trade > bad trade

The system should never manufacture a signal merely to produce activity.

### Simplicity > unnecessary complexity

Additional indicators and filters should have a research justification.

### Understanding > blindly generated code

The implementation should remain understandable to the developer.

---

# 23. Current Status

The project has moved beyond the initial environment-setup stage.

The current working system consists of:

**`main.py`**

Generates the current Nifty 500 Top 30 portfolio using Classic 12–1 momentum.

**`backtest.py`**

Validates the strategy across different portfolio sizes and transaction-cost assumptions.

**`trade_data.py`**

Refreshes the Nifty 500 universe.

**`universe.py`**

Contains the refreshed current Nifty 500 symbols.

The current priority is **strategy validation**, not adding more indicators or filters.

---

# 24. Known Limitations

Current limitations include:

1. Historical Nifty 500 membership is not point-in-time.
2. Survivorship bias therefore remains.
3. Yahoo Finance data is a free-data source with limitations.
4. Slippage is not fully modelled.
5. Transaction costs are simplified assumptions.
6. Corporate actions and historical data quality may affect results.
7. The backtest does not prove future profitability.
8. The current strategy has not yet been validated through live paper trading.

These limitations must be considered before interpreting performance results.

---

# 25. Future Strategy Development

The current strategy should not be modified simply because another indicator appears attractive.

Potential additions such as:

* RSI
* ATR
* Volume
* Relative strength
* Sector strength
* Market regime
* Breakout confirmation

should only be introduced after a clear hypothesis is established and tested independently.

Every additional parameter creates another opportunity for overfitting.

---

# 26. Success Criteria

TradeLens should ultimately be evaluated using a sufficiently large sample rather than individual trades.

Important measures include:

* CAGR
* Maximum drawdown
* Volatility
* Positive-month percentage
* Profit factor
* Expectancy
* Turnover
* Transaction costs
* Stability across years
* Stability across market regimes
* Out-of-sample performance

No single metric should determine whether a strategy is accepted.

---

# 27. Guiding Principle

The fundamental objective of TradeLens is:

**Evidence > intuition**

**Robustness > optimization**

**Risk-adjusted returns > raw returns**

**Simple rules > unnecessary complexity**

**No trade > bad trade**

**Understanding > blindly generated code**

---

# 28. Disclaimer

TradeLens is an educational and research project.

It may contain software bugs, incomplete data, inaccurate data, modelling assumptions and statistical limitations.

Historical backtest performance does not guarantee future performance.

TradeLens outputs should not be treated as a guarantee of profit or as personalized financial advice.
