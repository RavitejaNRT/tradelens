"""
TRADELENS
CLASSIC 12–1 MOMENTUM — TOP 30
LIVE MONTHLY PORTFOLIO SIGNAL

Strategy:
    Universe       : Nifty 500
    Momentum       : 12-month return excluding latest month
    Formula        : Price[t-1] / Price[t-12] - 1
    Ranking        : Cross-sectional
    Selection      : Top 30 stocks
    Weight         : Equal weight
    Rebalance      : Monthly
    Holding        : 1 month
    Stop loss      : None
    Target         : None
    Optimization   : None

IMPORTANT:
    Only the latest COMPLETED month is used.
    The current incomplete month is excluded.

Output:
    current_12_1_top30.csv
"""

import os
import time
import pickle
import warnings
from datetime import datetime

import pandas as pd
import yfinance as yf

from trade_data import refresh_nifty500_universe

# Refresh Nifty 500 membership BEFORE importing symbols
refresh_nifty500_universe()

from universe import symbols


# ================================================================
# CONFIGURATION
# ================================================================

TOP_N = 30

START_DATE = "2018-01-01"

CACHE_FILE = "tradelens_market_cache_12_1.pkl"

OUTPUT_FILE = "current_12_1_top30.csv"

MONTHS_REQUIRED = 13


# ================================================================
# DISPLAY
# ================================================================

def print_header(title):
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


# ================================================================
# LOAD MARKET DATA
# ================================================================

def download_market_data(symbol_list):
    """
    Download sufficient historical data to calculate
    12–1 momentum.

    We use monthly adjusted close prices.

    Failed/delisted symbols are skipped safely.
    """

    print_header("DOWNLOADING MARKET DATA")

    print(f"Required history : {START_DATE}")
    print(f"Symbols          : {len(symbol_list)}")
    print()

    cache = {}

    total = len(symbol_list)

    for i, symbol in enumerate(symbol_list, start=1):

        try:
            data = yf.download(
                symbol,
                start=START_DATE,
                auto_adjust=True,
                progress=False,
                threads=False,
            )

            if data is None or data.empty:
                continue

            # Handle yfinance MultiIndex columns.
            if isinstance(data.columns, pd.MultiIndex):

                if "Close" in data.columns.get_level_values(0):
                    close = data["Close"]

                    if isinstance(close, pd.DataFrame):
                        close = close.iloc[:, 0]

                else:
                    continue

            else:

                if "Close" not in data.columns:
                    continue

                close = data["Close"]

            close = pd.to_numeric(
                close,
                errors="coerce"
            ).dropna()

            if len(close) < 260:
                continue

            cache[symbol] = close

        except Exception:
            continue

        if i % 25 == 0 or i == total:
            print(
                f"Downloaded {i}/{total} | "
                f"usable {len(cache)}"
            )

    print()
    print(f"Requested symbols : {len(symbol_list)}")
    print(f"Usable symbols    : {len(cache)}")

    if len(cache) < 50:
        raise RuntimeError(
            "Insufficient usable market data."
        )

    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache, f)

    print()
    print(f"Saved cache       : {CACHE_FILE}")

    return cache


# ================================================================
# LOAD CACHE OR DOWNLOAD
# ================================================================

def load_market_data():

    if os.path.exists(CACHE_FILE):

        try:

            print()
            print("Loading cached market data...")

            with open(CACHE_FILE, "rb") as f:
                cache = pickle.load(f)

            if isinstance(cache, dict) and len(cache) >= 50:

                print(
                    f"Cached usable symbols : "
                    f"{len(cache)}"
                )

                return cache

        except Exception:
            pass

    return download_market_data(symbols)


# ================================================================
# BUILD MONTHLY PRICE MATRIX
# ================================================================

def build_monthly_prices(cache):

    print()
    print("Building monthly price matrix...")

    monthly = {}

    for symbol, close in cache.items():

        try:

            series = close.copy()

            series.index = pd.to_datetime(
                series.index
            )

            series = series.sort_index()

            # Month-end price.
            monthly_close = series.resample(
                "ME"
            ).last()

            monthly_close = monthly_close.dropna()

            if len(monthly_close) >= MONTHS_REQUIRED:

                monthly[symbol] = monthly_close

        except Exception:
            continue

    prices = pd.DataFrame(monthly)

    prices = prices.sort_index()

    print(
        f"Monthly observations : {len(prices)}"
    )

    print(
        f"Usable symbols       : {len(prices.columns)}"
    )

    if len(prices) < MONTHS_REQUIRED:
        raise RuntimeError(
            "Insufficient monthly history."
        )

    return prices


# ================================================================
# CALCULATE 12–1 MOMENTUM
# ================================================================

def calculate_momentum(prices):

    """
    Classic 12–1 momentum:

        Price[t-1] / Price[t-12] - 1

    Therefore:

        latest completed month = t-1
        starting month         = t-12

    The latest incomplete month is never used.
    """

    print()
    print("Calculating classic 12–1 momentum...")

    # Use only completed month-end observations.
    today = pd.Timestamp.today().normalize()

    last_completed_month = (
        today.to_period("M").to_timestamp("M")
    )

    # If the last index represents the current month,
    # remove it because it is incomplete.
    prices = prices[
        prices.index <= last_completed_month
    ]

    if len(prices) < MONTHS_REQUIRED:
        raise RuntimeError(
            "Insufficient completed monthly history."
        )

    # The latest row is the latest completed month.
    latest_completed = prices.index[-1]

    # 12–1:
    #
    # Price at latest completed month
    # divided by
    # Price 12 months before that.
    #
    # Since latest month itself must be excluded,
    # use the previous completed month as numerator.

    if len(prices) < 13:
        raise RuntimeError(
            "Need at least 13 monthly observations."
        )

    signal_month = prices.index[-2]

    lookback_month = prices.index[-13]

    latest_prices = prices.loc[signal_month]

    old_prices = prices.loc[lookback_month]

    momentum = (
        latest_prices / old_prices
    ) - 1.0

    momentum = momentum.replace(
        [float("inf"), float("-inf")],
        pd.NA
    )

    momentum = momentum.dropna()

    momentum = momentum[
        momentum > -1
    ]

    result = pd.DataFrame({
        "symbol": momentum.index,
        "momentum": momentum.values,
    })

    result = result.sort_values(
        "momentum",
        ascending=False
    )

    result = result.reset_index(drop=True)

    print()
    print(
        f"Signal month      : "
        f"{signal_month.strftime('%Y-%m')}"
    )

    print(
        f"Lookback month    : "
        f"{lookback_month.strftime('%Y-%m')}"
    )

    print(
        f"Eligible stocks   : {len(result)}"
    )

    return result, signal_month


# ================================================================
# SELECT TOP 30
# ================================================================

def select_top_30(momentum_df):

    if len(momentum_df) < TOP_N:

        raise RuntimeError(
            f"Only {len(momentum_df)} stocks available. "
            f"Need at least {TOP_N}."
        )

    selected = momentum_df.head(TOP_N).copy()

    selected["rank"] = range(
        1,
        TOP_N + 1
    )

    selected["weight"] = (
        1.0 / TOP_N
    )

    selected["weight_pct"] = (
        selected["weight"] * 100
    )

    return selected


# ================================================================
# DISPLAY PORTFOLIO
# ================================================================

def display_portfolio(
    selected,
    signal_month
):

    print_header(
        "CURRENT 12–1 MOMENTUM TOP 30"
    )

    for _, row in selected.iterrows():

        print(
            f"{int(row['rank']):2d}. "
            f"{row['symbol']:<20} "
            f"Momentum: "
            f"{row['momentum'] * 100:8.2f}% "
            f"Weight: "
            f"{row['weight_pct']:5.2f}%"
        )

    # The portfolio is held during the month
    # following the completed signal month.
    holding_month = (
        signal_month
        + pd.offsets.MonthEnd(1)
    )

    print_header(
        "PORTFOLIO IMPLEMENTATION"
    )

    print(
        f"Signal month      : "
        f"{signal_month.strftime('%Y-%m')}"
    )

    print(
        f"Holding month     : "
        f"{holding_month.strftime('%Y-%m')}"
    )

    print(
        f"Stocks selected   : {TOP_N}"
    )

    print(
        f"Weight per stock  : "
        f"{100 / TOP_N:.2f}%"
    )

    print(
        "Rebalance         : Monthly"
    )

    print(
        "Holding period    : 1 month"
    )

    print(
        "Stop loss         : NONE"
    )

    print(
        "Target            : NONE"
    )

    print()
    print("IMPORTANT:")
    print(
        "Only the latest COMPLETED month "
        "was used."
    )

    print(
        "The current incomplete month "
        "is excluded."
    )


# ================================================================
# SAVE PORTFOLIO
# ================================================================

def save_portfolio(
    selected,
    signal_month
):

    holding_month = (
        signal_month
        + pd.offsets.MonthEnd(1)
    )

    output = selected[
        [
            "rank",
            "symbol",
            "momentum",
            "weight",
            "weight_pct",
        ]
    ].copy()

    output["signal_month"] = (
        signal_month.strftime("%Y-%m")
    )

    output["holding_month"] = (
        holding_month.strftime("%Y-%m")
    )

    output["strategy"] = (
        "Classic 12-1 Momentum Top 30"
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print(
        f"Saved : {OUTPUT_FILE}"
    )


# ================================================================
# MAIN
# ================================================================

def main():

    start_time = time.time()

    warnings.filterwarnings(
        "ignore"
    )

    print_header(
        "TRADELENS — CLASSIC 12–1 MOMENTUM"
    )

    print(
        "CURRENT TOP 30 PORTFOLIO"
    )

    print_header(
        "STRATEGY"
    )

    print(
        "Momentum       : "
        "12-month return excluding latest month"
    )

    print(
        "Ranking        : Cross-sectional"
    )

    print(
        "Portfolio      : Equal-weight Top 30"
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
        "Feature weights: NONE"
    )

    print(
        "Hard filters   : NONE"
    )

    print()
    print(
        f"Nifty 500 symbols loaded from "
        f"universe.py: {len(symbols)}"
    )

    # ------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------

    cache = load_market_data()

    # ------------------------------------------------------------
    # MONTHLY PRICES
    # ------------------------------------------------------------

    prices = build_monthly_prices(
        cache
    )

    # ------------------------------------------------------------
    # MOMENTUM
    # ------------------------------------------------------------

    momentum_df, signal_month = (
        calculate_momentum(prices)
    )

    # ------------------------------------------------------------
    # TOP 30
    # ------------------------------------------------------------

    selected = select_top_30(
        momentum_df
    )

    # ------------------------------------------------------------
    # DISPLAY
    # ------------------------------------------------------------

    display_portfolio(
        selected,
        signal_month
    )

    # ------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------

    save_portfolio(
        selected,
        signal_month
    )

    # ------------------------------------------------------------
    # COMPLETE
    # ------------------------------------------------------------

    runtime = time.time() - start_time

    print_header(
        "12–1 MOMENTUM SIGNAL COMPLETE"
    )

    print(
        f"Runtime : {runtime:.2f} seconds"
    )

    print()
    print(
        "Strategy is FROZEN."
    )

    print(
        "No optimization."
    )

    print(
        "No discretionary ranking."
    )

    print(
        "No stop loss."
    )

    print(
        "No target."
    )

    print(
        "Monthly rebalance using "
        "the latest completed month."
    )

    print("=" * 64)


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    main()