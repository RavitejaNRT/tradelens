# TradeLens

**Rule-based momentum investing system built around classic, evidence-backed strategies.**

TradeLens is a Python-based research and portfolio-selection project designed to test established quantitative investing strategies without relying on discretionary stock picking, parameter optimization, or overfitting.

The first strategy implemented and validated is **Classic 12–1 Price Momentum — Top 30**.

---

## Current Strategy

### Classic 12–1 Price Momentum — Top 30

The strategy ranks stocks based on their **12-month price momentum while excluding the most recent month**.

### Momentum Formula

```text
Momentum = Price[t-1] / Price[t-12] - 1
```

Where:

* `t-1` = latest completed month
* `t-12` = price 12 months before the latest completed month
* The most recent month is deliberately excluded from the momentum calculation.

### Portfolio Rules

| Rule                     | Implementation                         |
| ------------------------ | -------------------------------------- |
| Universe                 | Nifty 500                              |
| Momentum                 | 12-month return excluding latest month |
| Ranking                  | Cross-sectional                        |
| Selection                | Top 30 stocks                          |
| Weighting                | Equal weight                           |
| Weight per stock         | 3.33%                                  |
| Rebalance                | Monthly                                |
| Holding period           | 1 month                                |
| Stop loss                | None                                   |
| Target                   | None                                   |
| RSI                      | None                                   |
| ATR                      | None                                   |
| Volume filter            | None                                   |
| 52-week-high filter      | None                                   |
| Fundamental filters      | None                                   |
| Parameter optimization   | None                                   |
| Feature weights          | None                                   |
| Hard-filter optimization | None                                   |

TradeLens intentionally keeps the strategy close to the classic momentum concept rather than fine-tuning parameters to historical results.

---

## How the Monthly Signal Works

The strategy always uses the **latest completed month**.

For example:

### July Portfolio

Run the strategy after the **last trading day of June**.

```text
June = latest completed month
June = excluded from momentum
May = latest month used in the momentum calculation
```

The resulting Top 30 portfolio is held during July.

If the signal is missed on the month-end, it can be run on the **first trading day of the new month**, provided the previous month is complete.

The current incomplete month is never used.

---

## Backtesting & Validation

TradeLens tested the strategy through multiple stages:

1. Classic historical backtest
2. Walk-forward / unseen out-of-sample testing
3. Portfolio-size comparison
4. Transaction-cost validation
5. Drawdown and volatility analysis
6. Current portfolio signal generation

### Walk-Forward OOS Result

The fixed strategy was tested using Top 10, Top 20 and Top 30 portfolios.

The aggregate unseen OOS results were:

| Portfolio  | OOS Trades |   Win Rate | Profit Factor |  Expectancy |
| ---------- | ---------: | ---------: | ------------: | ----------: |
| Top 10     |        560 |     53.57% |          1.55 |     0.0248R |
| Top 20     |      1,120 |     53.93% |          1.50 |     0.0208R |
| **Top 30** |  **1,680** | **54.82%** |      **1.55** | **0.0216R** |

The Top 30 portfolio produced positive expectancy in **100% of the tested walk-forward folds**.

---

## Transaction-Cost Validation

The Top 30 portfolio was tested at different transaction-cost assumptions.

| Transaction Cost |       CAGR | Max Drawdown | Positive Months | Avg. Turnover |
| ---------------: | ---------: | -----------: | --------------: | ------------: |
|            0.00% |     23.37% |      -27.84% |          64.29% |        29.35% |
|            0.10% |     22.94% |      -27.96% |          64.29% |        29.35% |
|        **0.20%** | **22.52%** |  **-28.07%** |      **64.29%** |    **29.35%** |

The **0.20% transaction-cost scenario** is used as the more conservative reference.

### Interpretation

The historical test suggests that the strategy had a meaningful positive edge even after allowing for transaction costs.

However, these results are **historical simulations, not guaranteed future returns**.

---

## What to Expect

This is a **momentum strategy**, so it should not be expected to make money every month or every year.

Expect:

* Periods of strong outperformance
* Periods of weak performance
* Negative months
* Significant drawdowns
* Portfolio turnover every month
* Large changes in the selected stocks
* Occasional concentration in particular sectors or themes
* Momentum reversals where recent winners fall sharply

The strategy is designed to capture **persistent relative strength over time**, not to predict which stock will rise tomorrow.

The objective is therefore to evaluate performance over **multiple years**, rather than judge the strategy from one month or one calendar year.

---

## Important Caveats

### 1. Survivorship Bias

The current implementation uses the **current Nifty 500 universe** rather than historical point-in-time Nifty 500 membership.

Therefore, the backtest is **not fully survivorship-bias-free**.

A future improvement would be to maintain historical Nifty 500 constituent membership for every rebalance date.

### 2. Historical Results Are Not Guarantees

The reported CAGR, drawdown and other statistics describe the tested historical period only.

Future market regimes can behave differently.

### 3. No Guaranteed Monthly Profit

A positive long-term CAGR does not mean every month or every year will be profitable.

### 4. Execution Differences

Backtest prices may differ from actual execution because of:

* Slippage
* Bid/ask spreads
* Liquidity
* Market impact
* Brokerage and taxes
* Order timing

### 5. Strategy Is Intentionally Not Optimized

TradeLens does not currently attempt to maximize historical CAGR by continuously changing:

* Momentum periods
* Portfolio size
* Filters
* Stop losses
* Targets
* Technical indicators
* Parameter combinations

This is intentional.

The goal is to reduce the risk of **overfitting the strategy to historical data**.

---

## Project Philosophy

TradeLens follows a simple principle:

> **Start with a known strategy → implement it transparently → backtest it → test unseen periods → test costs and robustness → only then consider live implementation.**

The project is designed to avoid turning historical data into a parameter-mining exercise.

A strategy that looks spectacular only after extensive optimization is less interesting than a simple strategy that continues to work when tested on unseen data.

---

## Current Live Workflow

At the end of each month:

```text
1. Download/update market data
2. Identify the latest completed month
3. Calculate 12–1 momentum
4. Rank the Nifty 500 universe
5. Select the Top 30
6. Allocate 3.33% to each stock
7. Hold for the next month
8. Repeat at the next month-end
```

The current portfolio is generated by:

```text
main.py
```

and saved as:

```text
current_12_1_top30.csv
```

---

## Repository Structure

```text
TradeLens/
│
├── main.py
├── backtest.py
├── universe.py
├── README.md
│
├── docs/
│   └── PROJECT_DOCUMENTATION.md
│
├── current_12_1_top30.csv
│
└── .gitignore
```

Additional backtest output files may be generated during research and validation.

---

## Roadmap

### Completed

* [x] Project setup
* [x] Nifty 500 universe
* [x] Market-data pipeline
* [x] Classic 12–1 momentum calculation
* [x] Monthly portfolio construction
* [x] Top 10 / 20 / 30 / 50 comparison
* [x] Walk-forward OOS testing
* [x] Transaction-cost validation
* [x] Current Top 30 signal generation

### Next

* [ ] Production-quality monthly signal workflow
* [ ] Portfolio tracking
* [ ] Trade/holding history
* [ ] Performance monitoring
* [ ] Risk monitoring
* [ ] Historical point-in-time universe
* [ ] Research and validation of additional classic quantitative strategies

---

## Disclaimer

TradeLens is a **research and educational software project**.

Backtested performance does not guarantee future results. The project is not investment advice, and actual investment decisions should consider risk tolerance, taxes, transaction costs, liquidity and changing market conditions.

---

## Strategy Status

**Current production strategy:**

### Classic 12–1 Momentum — Top 30

**Status: Validated for further live monitoring.**

The strategy is intentionally kept simple, transparent and rules-based.

**No optimization.
No prediction model.
No discretionary stock selection.
No stop loss.
No target.
Monthly rebalance.**
