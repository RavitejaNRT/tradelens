# backtest.py
# TradeLens — Classic 12–1 Momentum
# POINT-IN-TIME / SURVIVORSHIP-BIAS-AWARE VALIDATION
#
# IMPORTANT:
# This version does NOT pretend that today's Nifty 500 membership
# was the historical universe.
#
# Because universe.py contains only the CURRENT universe, this script
# cannot reconstruct historical Nifty 500 membership by itself.
#
# Therefore it performs the next-best defensible test:
#
#   1. Uses the current universe consistently.
#   2. Does NOT optimize any parameters.
#   3. Uses only information available at each rebalance date.
#   4. Tests transaction costs.
#   5. Tests Top 10 / 20 / 30 / 50.
#   6. Reports yearly returns, drawdown, turnover and OOS results.
#   7. Separates gross and net performance.
#
# Strategy:
#   Momentum = Price[t-1] / Price[t-12] - 1
#   Ranking  = Cross-sectional
#   Rebalance = Monthly
#   Portfolio = Equal-weight top N
#   No RSI / ATR / volume / 52W high / stop / target
#
# This is a validation engine, NOT a strategy optimizer.


from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf


# ==============================================================
# CONFIGURATION
# ==============================================================

BASE_DIR = Path(__file__).resolve().parent

DOWNLOAD_START = "2018-01-01"

# Test several portfolio sizes.
PORTFOLIO_SIZES = [10, 20, 30, 50]

# Round-trip transaction-cost assumptions.
# 0.10% means 10 bps for a complete buy/sell cycle.
COST_LEVELS = [0.00, 0.0010, 0.0020]

# Minimum number of months required.
MIN_MONTHS = 13

OUTPUT_RESULTS = BASE_DIR / "12_1_validation_results.csv"
OUTPUT_YEARLY = BASE_DIR / "12_1_validation_yearly.csv"
OUTPUT_TRADES = BASE_DIR / "12_1_validation_trades.csv"


# ==============================================================
# UNIVERSE
# ==============================================================

def load_symbols():

    universe_file = BASE_DIR / "universe.py"

    if not universe_file.exists():
        raise FileNotFoundError(
            "universe.py not found."
        )

    namespace = {}

    exec(
        universe_file.read_text(
            encoding="utf-8"
        ),
        namespace
    )

    possible_names = [
        "symbols",
        "NIFTY500_SYMBOLS",
        "NIFTY_500_SYMBOLS",
        "SYMBOLS",
        "NIFTY500",
        "UNIVERSE",
    ]

    for name in possible_names:

        value = namespace.get(name)

        if isinstance(value, (list, tuple)) and value:

            symbols = []

            for symbol in value:

                symbol = str(symbol).strip().upper()

                if not symbol:
                    continue

                if not symbol.endswith(".NS"):
                    symbol += ".NS"

                symbols.append(symbol)

            symbols = list(
                dict.fromkeys(symbols)
            )

            print(
                f"Nifty 500 symbols loaded from universe.py "
                f"using '{name}': {len(symbols)}"
            )

            return symbols

    raise ValueError(
        "Could not find stock list in universe.py."
    )


# ==============================================================
# DOWNLOAD
# ==============================================================

def download_data(symbols):

    print()
    print("=" * 64)
    print("DOWNLOADING MARKET DATA")
    print("=" * 64)

    print(
        f"Required history : {DOWNLOAD_START}"
    )

    usable = {}

    for i, symbol in enumerate(symbols, 1):

        try:

            df = yf.download(
                symbol,
                start=DOWNLOAD_START,
                progress=False,
                auto_adjust=True,
                actions=False,
                threads=False,
            )

            if df is None or df.empty:
                continue

            if isinstance(
                df.columns,
                pd.MultiIndex
            ):

                if "Close" not in (
                    df.columns
                    .get_level_values(0)
                ):
                    continue

                close = df["Close"]

                if isinstance(
                    close,
                    pd.DataFrame
                ):

                    if close.shape[1] == 0:
                        continue

                    close = close.iloc[:, 0]

            else:

                if "Close" not in df.columns:
                    continue

                close = df["Close"]

            close = pd.to_numeric(
                close,
                errors="coerce"
            ).dropna()

            if len(close) < 270:
                continue

            close.index = pd.to_datetime(
                close.index
            )

            usable[symbol] = close

        except Exception:
            continue

        if i % 25 == 0 or i == len(symbols):

            print(
                f"Downloaded {i}/{len(symbols)} | "
                f"usable {len(usable)}"
            )

    print()
    print(
        f"Requested symbols : {len(symbols)}"
    )

    print(
        f"Usable symbols    : {len(usable)}"
    )

    if len(usable) < 100:

        raise RuntimeError(
            "Too few usable symbols."
        )

    return usable


# ==============================================================
# MONTHLY DATA
# ==============================================================

def build_monthly_matrix(data):

    monthly = {}

    for symbol, close in data.items():

        try:

            series = (
                close
                .sort_index()
                .resample("ME")
                .last()
                .dropna()
            )

            if len(series) >= MIN_MONTHS:

                monthly[symbol] = series

        except Exception:
            continue

    matrix = pd.DataFrame(monthly)

    return matrix.sort_index()


# ==============================================================
# PORTFOLIO RETURN
# ==============================================================

def portfolio_return(
    previous_prices,
    current_prices,
    symbols,
    cost_rate
):

    available = [
        s for s in symbols
        if (
            s in previous_prices.index
            and s in current_prices.index
            and pd.notna(previous_prices[s])
            and pd.notna(current_prices[s])
            and previous_prices[s] > 0
        )
    ]

    if not available:

        return np.nan, 0.0

    returns = (
        current_prices.loc[available]
        /
        previous_prices.loc[available]
        - 1.0
    )

    gross_return = returns.mean()

    # The cost here is applied to the portfolio's
    # initial deployment. This is deliberately simple
    # and conservative rather than pretending to know
    # exact execution prices.
    net_return = (
        gross_return - cost_rate
    )

    return (
        net_return,
        gross_return
    )


# ==============================================================
# BACKTEST ONE PORTFOLIO
# ==============================================================

def run_backtest(
    monthly,
    top_n,
    cost_rate
):

    dates = monthly.index

    # Need 12 months of history BEFORE the signal month.
    signal_dates = dates[12:]

    portfolio_returns = []
    records = []

    previous_portfolio = set()

    for signal_date in signal_dates:

        # ------------------------------------------------------
        # Signal uses information through the PREVIOUS month.
        #
        # At signal month t:
        #
        # momentum =
        # price[t-1] / price[t-12] - 1
        # ------------------------------------------------------

        signal_position = dates.get_loc(
            signal_date
        )

        if signal_position < 12:
            continue

        previous_date = dates[
            signal_position - 1
        ]

        twelve_months_ago = dates[
            signal_position - 12
        ]

        previous_prices = monthly.loc[
            previous_date
        ]

        old_prices = monthly.loc[
            twelve_months_ago
        ]

        momentum = (
            previous_prices
            /
            old_prices
            - 1.0
        )

        momentum = momentum.replace(
            [np.inf, -np.inf],
            np.nan
        ).dropna()

        if len(momentum) < top_n:
            continue

        # ------------------------------------------------------
        # Cross-sectional ranking
        # ------------------------------------------------------

        selected = list(
            momentum
            .sort_values(
                ascending=False
            )
            .head(top_n)
            .index
        )

        current_date = signal_date

        current_prices = monthly.loc[
            current_date
        ]

        # ------------------------------------------------------
        # Monthly return
        # ------------------------------------------------------

        gross_returns = []

        for symbol in selected:

            if (
                symbol not in previous_prices.index
                or symbol not in current_prices.index
            ):
                continue

            p0 = previous_prices[symbol]
            p1 = current_prices[symbol]

            if (
                pd.isna(p0)
                or pd.isna(p1)
                or p0 <= 0
            ):
                continue

            gross_returns.append(
                p1 / p0 - 1.0
            )

        if not gross_returns:
            continue

        gross_return = np.mean(
            gross_returns
        )

        # ------------------------------------------------------
        # Turnover
        #
        # A simple portfolio turnover estimate:
        # fraction of names entering/leaving.
        # ------------------------------------------------------

        current_set = set(selected)

        if not previous_portfolio:

            turnover = 1.0

        else:

            overlap = len(
                current_set
                &
                previous_portfolio
            )

            turnover = (
                1.0
                -
                overlap / top_n
            )

        # Cost proportional to turnover.
        transaction_cost = (
            turnover * cost_rate
        )

        net_return = (
            gross_return
            -
            transaction_cost
        )

        portfolio_returns.append(
            {
                "date": current_date,
                "gross_return": gross_return,
                "net_return": net_return,
                "turnover": turnover,
                "transaction_cost": transaction_cost,
                "stocks": len(selected),
            }
        )

        records.append(
            {
                "date": current_date,
                "portfolio_size": top_n,
                "cost_rate": cost_rate,
                "gross_return": gross_return,
                "net_return": net_return,
                "turnover": turnover,
                "transaction_cost": transaction_cost,
                "symbols": ",".join(selected),
            }
        )

        previous_portfolio = current_set

    returns = pd.DataFrame(
        portfolio_returns
    )

    trades = pd.DataFrame(records)

    return returns, trades


# ==============================================================
# PERFORMANCE METRICS
# ==============================================================

def calculate_metrics(returns):

    if returns.empty:

        return {
            "months": 0,
            "cagr": np.nan,
            "volatility": np.nan,
            "max_drawdown": np.nan,
            "positive_months_pct": np.nan,
            "worst_month": np.nan,
            "best_month": np.nan,
        }

    series = returns["net_return"].copy()

    equity = (
        1.0 + series
    ).cumprod()

    running_max = equity.cummax()

    drawdown = (
        equity / running_max
        - 1.0
    )

    max_drawdown = drawdown.min()

    months = len(series)

    years = months / 12.0

    ending_value = equity.iloc[-1]

    if (
        ending_value > 0
        and years > 0
    ):

        cagr = (
            ending_value
            **
            (1.0 / years)
            - 1.0
        )

    else:

        cagr = np.nan

    volatility = (
        series.std(ddof=1)
        *
        np.sqrt(12)
    )

    positive_months = (
        (series > 0).mean()
        * 100.0
    )

    return {
        "months": months,
        "cagr": cagr,
        "volatility": volatility,
        "max_drawdown": max_drawdown,
        "positive_months_pct": positive_months,
        "worst_month": series.min(),
        "best_month": series.max(),
    }


# ==============================================================
# YEARLY RETURNS
# ==============================================================

def yearly_results(
    returns,
    top_n,
    cost_rate
):

    if returns.empty:

        return pd.DataFrame()

    df = returns.copy()

    df["year"] = (
        pd.to_datetime(
            df["date"]
        ).dt.year
    )

    rows = []

    for year, group in df.groupby(
        "year"
    ):

        gross_equity = (
            1.0
            +
            group["gross_return"]
        ).prod()

        net_equity = (
            1.0
            +
            group["net_return"]
        ).prod()

        rows.append(
            {
                "portfolio_size": top_n,
                "cost_rate": cost_rate,
                "year": year,
                "gross_return": (
                    gross_equity - 1.0
                ),
                "net_return": (
                    net_equity - 1.0
                ),
                "average_turnover": (
                    group["turnover"].mean()
                ),
                "months": len(group),
            }
        )

    return pd.DataFrame(rows)


# ==============================================================
# WALK-FORWARD OOS
# ==============================================================

def run_oos(
    monthly,
    top_n,
    cost_rate
):

    all_dates = monthly.index

    # Use only complete calendar years after
    # an initial training period.
    #
    # Training:
    # 2018 through 2021
    #
    # OOS:
    # 2022 onward
    #
    # The strategy itself has NO parameters selected
    # from training data. Training is therefore used
    # only as a chronological separation.

    oos_start = pd.Timestamp(
        "2022-01-31"
    )

    returns, trades = run_backtest(
        monthly,
        top_n,
        cost_rate
    )

    if returns.empty:

        return (
            pd.DataFrame(),
            pd.DataFrame()
        )

    oos_returns = returns[
        returns["date"] >= oos_start
    ].copy()

    oos_trades = trades[
        trades["date"] >= oos_start
    ].copy()

    return (
        oos_returns,
        oos_trades
    )


# ==============================================================
# MAIN
# ==============================================================

def main():

    start = datetime.now()

    print("=" * 64)
    print(
        "TRADELENS — CLASSIC 12–1 MOMENTUM"
    )
    print(
        "ROBUSTNESS + COST VALIDATION"
    )
    print("=" * 64)

    print()
    print("Strategy:")
    print()
    print(
        "Momentum       : "
        "12-month return excluding latest month"
    )
    print(
        "Ranking        : Cross-sectional"
    )
    print(
        "Portfolio      : Top 10 / 20 / 30 / 50"
    )
    print(
        "Rebalance      : Monthly"
    )
    print(
        "Stop loss      : NONE"
    )
    print(
        "Target         : NONE"
    )
    print(
        "Optimization    : NONE"
    )
    print(
        "Survivorship    : CURRENT universe "
        "limitation remains"
    )

    # ----------------------------------------------------------
    # UNIVERSE
    # ----------------------------------------------------------

    symbols = load_symbols()

    # ----------------------------------------------------------
    # DATA
    # ----------------------------------------------------------

    data = download_data(
        symbols
    )

    # ----------------------------------------------------------
    # MONTHLY MATRIX
    # ----------------------------------------------------------

    print()
    print(
        "Building monthly price matrix..."
    )

    monthly = build_monthly_matrix(
        data
    )

    print(
        f"Monthly observations : "
        f"{len(monthly)}"
    )

    print(
        f"Usable symbols       : "
        f"{len(monthly.columns)}"
    )

    if len(monthly) < MIN_MONTHS:

        raise RuntimeError(
            "Insufficient monthly history."
        )

    # ----------------------------------------------------------
    # TEST
    # ----------------------------------------------------------

    all_results = []
    all_yearly = []
    all_trades = []

    for top_n in PORTFOLIO_SIZES:

        print()
        print("=" * 64)
        print(
            f"PORTFOLIO TOP {top_n}"
        )
        print("=" * 64)

        for cost_rate in COST_LEVELS:

            print()
            print(
                f"Transaction cost : "
                f"{cost_rate * 100:.2f}%"
            )

            oos_returns, oos_trades = run_oos(
                monthly,
                top_n,
                cost_rate
            )

            metrics = calculate_metrics(
                oos_returns
            )

            yearly = yearly_results(
                oos_returns,
                top_n,
                cost_rate
            )

            print(
                f"OOS months       : "
                f"{metrics['months']}"
            )

            print(
                f"OOS CAGR         : "
                f"{metrics['cagr'] * 100:.2f}%"
                if pd.notna(metrics["cagr"])
                else "OOS CAGR         : N/A"
            )

            print(
                f"Volatility       : "
                f"{metrics['volatility'] * 100:.2f}%"
                if pd.notna(
                    metrics["volatility"]
                )
                else "Volatility       : N/A"
            )

            print(
                f"Max drawdown     : "
                f"{metrics['max_drawdown'] * 100:.2f}%"
                if pd.notna(
                    metrics["max_drawdown"]
                )
                else "Max drawdown     : N/A"
            )

            print(
                f"Positive months  : "
                f"{metrics['positive_months_pct']:.2f}%"
                if pd.notna(
                    metrics[
                        "positive_months_pct"
                    ]
                )
                else "Positive months  : N/A"
            )

            print(
                f"Average turnover : "
                f"{oos_returns['turnover'].mean() * 100:.2f}%"
                if not oos_returns.empty
                else "Average turnover : N/A"
            )

            all_results.append(
                {
                    "portfolio_size": top_n,
                    "cost_rate": cost_rate,
                    **metrics,
                    "average_turnover": (
                        oos_returns[
                            "turnover"
                        ].mean()
                        if not oos_returns.empty
                        else np.nan
                    ),
                }
            )

            if not yearly.empty:

                all_yearly.append(
                    yearly
                )

            if not oos_trades.empty:

                all_trades.append(
                    oos_trades
                )

    # ----------------------------------------------------------
    # SAVE
    # ----------------------------------------------------------

    results_df = pd.DataFrame(
        all_results
    )

    yearly_df = (
        pd.concat(
            all_yearly,
            ignore_index=True
        )
        if all_yearly
        else pd.DataFrame()
    )

    trades_df = (
        pd.concat(
            all_trades,
            ignore_index=True
        )
        if all_trades
        else pd.DataFrame()
    )

    results_df.to_csv(
        OUTPUT_RESULTS,
        index=False
    )

    yearly_df.to_csv(
        OUTPUT_YEARLY,
        index=False
    )

    trades_df.to_csv(
        OUTPUT_TRADES,
        index=False
    )

    # ----------------------------------------------------------
    # FINAL SUMMARY
    # ----------------------------------------------------------

    print()
    print("=" * 64)
    print(
        "FINAL OOS ROBUSTNESS SUMMARY"
    )
    print("=" * 64)

    print()

    print(
        f"{'Portfolio':<12}"
        f"{'Cost':>8}"
        f"{'CAGR':>10}"
        f"{'Max DD':>10}"
        f"{'Positive':>12}"
        f"{'Turnover':>12}"
    )

    print("-" * 64)

    for _, row in results_df.iterrows():

        cagr = row["cagr"]

        dd = row["max_drawdown"]

        positive = row[
            "positive_months_pct"
        ]

        turnover = row[
            "average_turnover"
        ]

        print(
            f"Top {int(row['portfolio_size']):<7}"
            f"{row['cost_rate'] * 100:>7.2f}%"
            f"{cagr * 100:>9.2f}%"
            f"{dd * 100:>9.2f}%"
            f"{positive:>10.2f}%"
            f"{turnover * 100:>10.2f}%"
        )

    print()
    print("=" * 64)
    print(
        "VALIDATION CONCLUSION"
    )
    print("=" * 64)

    # Use 20 bps as the conservative reference.
    reference = results_df[
        results_df["cost_rate"] == 0.0020
    ].copy()

    if not reference.empty:

        best = reference.sort_values(
            "cagr",
            ascending=False
        ).iloc[0]

        print()
        print(
            f"Best portfolio at 20 bps "
            f"transaction cost : "
            f"Top {int(best['portfolio_size'])}"
        )

        print(
            f"CAGR              : "
            f"{best['cagr'] * 100:.2f}%"
        )

        print(
            f"Max drawdown       : "
            f"{best['max_drawdown'] * 100:.2f}%"
        )

        print(
            f"Positive months    : "
            f"{best['positive_months_pct']:.2f}%"
        )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "This test does NOT prove absence of "
        "survivorship bias."
    )

    print(
        "A true point-in-time Nifty 500 test "
        "requires historical index membership "
        "for every rebalance date."
    )

    print(
        "Do not interpret the result as a "
        "fully survivorship-bias-free backtest."
    )

    print()
    print(
        "No parameters were optimized."
    )

    print(
        "No strategy was selected because it "
        "hit an arbitrary target."
    )

    print()
    print(
        f"Saved : {OUTPUT_RESULTS.name}"
    )

    print(
        f"Saved : {OUTPUT_YEARLY.name}"
    )

    print(
        f"Saved : {OUTPUT_TRADES.name}"
    )

    runtime = (
        datetime.now() - start
    ).total_seconds()

    print()
    print(
        f"Total runtime : "
        f"{runtime:.2f} seconds"
    )

    print("=" * 64)
    print(
        "ROBUSTNESS VALIDATION COMPLETE"
    )
    print("=" * 64)


if __name__ == "__main__":
    main()