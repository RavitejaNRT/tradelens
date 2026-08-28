"""
TRADELENS
CLASSIC 12–1 MOMENTUM — TOP 30
LIVE MONTHLY PORTFOLIO SIGNAL

Strategy:
    Universe       : Latest Nifty 500
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
    The latest Nifty 500 universe is refreshed on every run.

    The market-data cache is NOT treated as the universe.

    Existing cached price data is reused where possible.
    Newly added Nifty 500 constituents are downloaded automatically.
    Stocks no longer in the current Nifty 500 are excluded from
    the portfolio calculation.

    Only the latest COMPLETED month is used.
    The current incomplete month is excluded.

Output:
    current_12_1_top30.csv
"""

import os
import time
import pickle
import warnings

import pandas as pd
import yfinance as yf

from trade_data import refresh_nifty500_universe


# Refresh the latest Nifty 500 universe BEFORE importing symbols.
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
# NORMALIZE SYMBOLS
# ================================================================

def normalize_symbol(symbol):
    """
    Normalize an NSE symbol for yfinance.

    Examples:
        RELIANCE      -> RELIANCE.NS
        RELIANCE.NS   -> RELIANCE.NS
    """

    symbol = str(symbol).strip().upper()

    if not symbol:
        return None

    if not symbol.endswith(".NS"):
        symbol += ".NS"

    return symbol


def normalize_universe(symbol_list):
    """
    Normalize and deduplicate the current Nifty 500 universe.
    """

    normalized = []

    for symbol in symbol_list:

        symbol = normalize_symbol(symbol)

        if symbol:
            normalized.append(symbol)

    return list(dict.fromkeys(normalized))


# ================================================================
# LOAD / REFRESH MARKET DATA
# ================================================================

def download_symbol_data(symbol):
    """
    Download historical adjusted closing prices for one symbol.

    Returns:
        pandas Series or None
    """

    try:

        data = yf.download(
            symbol,
            start=START_DATE,
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if data is None or data.empty:
            return None

        # Handle yfinance MultiIndex columns.
        if isinstance(data.columns, pd.MultiIndex):

            if "Close" not in data.columns.get_level_values(0):
                return None

            close = data["Close"]

            if isinstance(close, pd.DataFrame):

                if close.shape[1] == 0:
                    return None

                close = close.iloc[:, 0]

        else:

            if "Close" not in data.columns:
                return None

            close = data["Close"]

        close = pd.to_numeric(
            close,
            errors="coerce"
        ).dropna()

        if len(close) < 260:
            return None

        close.index = pd.to_datetime(close.index)

        return close

    except Exception:
        return None


def load_or_refresh_market_data(current_symbols):
    """
    Reconcile the market-data cache with the latest Nifty 500 universe.

    The cache is a PRICE-DATA CACHE only.

    It is NOT treated as the stock universe.

    Process:

        1. Load existing cache if available.
        2. Identify current Nifty 500 constituents missing from cache.
        3. Download only missing constituents.
        4. Keep only current Nifty 500 constituents for the
           returned portfolio dataset.
        5. Save the complete cache.

    Existing cached data for stocks that have left the Nifty 500
    may remain in the physical cache file, but those stocks are
    excluded from the returned dataset.
    """

    print_header("MARKET DATA / CACHE RECONCILIATION")

    print(
        f"Current Nifty 500 symbols : "
        f"{len(current_symbols)}"
    )

    cache = {}

    # ------------------------------------------------------------
    # LOAD EXISTING CACHE
    # ------------------------------------------------------------

    if os.path.exists(CACHE_FILE):

        try:

            print(
                f"Loading existing cache : "
                f"{CACHE_FILE}"
            )

            with open(CACHE_FILE, "rb") as f:
                loaded_cache = pickle.load(f)

            if isinstance(loaded_cache, dict):

                for symbol, close in loaded_cache.items():

                    normalized = normalize_symbol(symbol)

                    if (
                        normalized
                        and isinstance(close, pd.Series)
                    ):

                        cache[normalized] = close

            print(
                f"Cached symbols          : "
                f"{len(cache)}"
            )

        except Exception as error:

            print(
                "Existing cache could not be loaded."
            )

            print(
                f"Reason                  : "
                f"{error}"
            )

            cache = {}

    else:

        print(
            "No existing cache found."
        )

    # ------------------------------------------------------------
    # FIND MISSING CURRENT CONSTITUENTS
    # ------------------------------------------------------------

    current_set = set(current_symbols)
    cached_set = set(cache.keys())

    missing_symbols = sorted(
        current_set - cached_set
    )

    removed_symbols = sorted(
        cached_set - current_set
    )

    print()
    print(
        f"Cached current constituents : "
        f"{len(current_set & cached_set)}"
    )

    print(
        f"New / missing constituents  : "
        f"{len(missing_symbols)}"
    )

    print(
        f"No longer in Nifty 500      : "
        f"{len(removed_symbols)}"
    )

    # ------------------------------------------------------------
    # DOWNLOAD ONLY MISSING CURRENT CONSTITUENTS
    # ------------------------------------------------------------

    if missing_symbols:

        print()
        print(
            "DOWNLOADING NEW / MISSING "
            "NIFTY 500 CONSTITUENTS"
        )
        print()

        total = len(missing_symbols)
        downloaded = 0
        failed = 0

        for i, symbol in enumerate(
            missing_symbols,
            start=1
        ):

            close = download_symbol_data(
                symbol
            )

            if close is not None:

                cache[symbol] = close
                downloaded += 1

            else:

                failed += 1

            if (
                i % 25 == 0
                or i == total
            ):

                print(
                    f"Processed {i}/{total} | "
                    f"downloaded {downloaded} | "
                    f"failed {failed}"
                )

    else:

        print()
        print(
            "No new Nifty 500 constituents "
            "require downloading."
        )

    # ------------------------------------------------------------
    # SAVE COMPLETE PRICE CACHE
    # ------------------------------------------------------------

    with open(CACHE_FILE, "wb") as f:

        pickle.dump(
            cache,
            f
        )

    print()
    print(
        f"Saved cache              : "
        f"{CACHE_FILE}"
    )

    print(
        f"Total cached symbols     : "
        f"{len(cache)}"
    )

    # ------------------------------------------------------------
    # CRITICAL:
    # RETURN ONLY CURRENT NIFTY 500
    # ------------------------------------------------------------

    current_cache = {}

    for symbol in current_symbols:

        if symbol in cache:

            current_cache[symbol] = cache[symbol]

    print()
    print(
        f"Current universe with data : "
        f"{len(current_cache)}"
    )

    if len(current_cache) < 50:

        raise RuntimeError(
            "Insufficient usable market data "
            "for the current Nifty 500 universe."
        )

    return current_cache


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

            monthly_close = (
                monthly_close
                .dropna()
            )

            if len(monthly_close) >= MONTHS_REQUIRED:

                monthly[symbol] = monthly_close

        except Exception:
            continue

    prices = pd.DataFrame(monthly)

    prices = prices.sort_index()

    print(
        f"Monthly observations : "
        f"{len(prices)}"
    )

    print(
        f"Usable symbols       : "
        f"{len(prices.columns)}"
    )

    if len(prices) < MONTHS_REQUIRED:

        raise RuntimeError(
            "Insufficient monthly history."
        )

    if len(prices.columns) < TOP_N:

        raise RuntimeError(
            f"Only {len(prices.columns)} stocks have "
            f"sufficient monthly history. "
            f"Need at least {TOP_N}."
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
    print(
        "Calculating classic 12–1 momentum..."
    )

    # ------------------------------------------------------------
    # EXCLUDE CURRENT INCOMPLETE MONTH
    # ------------------------------------------------------------

    today = pd.Timestamp.today().normalize()

    last_completed_month = (
        today
        .to_period("M")
        .to_timestamp("M")
    )

    prices = prices[
        prices.index <= last_completed_month
    ]

    if len(prices) < MONTHS_REQUIRED:

        raise RuntimeError(
            "Insufficient completed monthly history."
        )

    # ------------------------------------------------------------
    # SIGNAL MONTH
    # ------------------------------------------------------------

    if len(prices) < 13:

        raise RuntimeError(
            "Need at least 13 monthly observations."
        )

    # Latest completed month is prices.index[-1].
    #
    # Exclude it from the momentum calculation.
    #
    # Therefore:
    #
    # signal month   = latest completed month - 1
    # lookback month = signal month - 12 months

    signal_month = prices.index[-2]

    lookback_month = prices.index[-13]

    latest_prices = prices.loc[
        signal_month
    ]

    old_prices = prices.loc[
        lookback_month
    ]

    momentum = (
        latest_prices
        /
        old_prices
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

    result = result.reset_index(
        drop=True
    )

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
        f"Eligible stocks   : "
        f"{len(result)}"
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

    selected = momentum_df.head(
        TOP_N
    ).copy()

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
        f"Stocks selected   : "
        f"{TOP_N}"
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
        "Latest Nifty 500 universe was "
        "refreshed before processing."
    )

    print(
        "Only current Nifty 500 constituents "
        "were used."
    )

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

    # ------------------------------------------------------------
    # CURRENT NIFTY 500 UNIVERSE
    # ------------------------------------------------------------

    current_symbols = normalize_universe(
        symbols
    )

    print()
    print(
        f"Latest Nifty 500 symbols : "
        f"{len(current_symbols)}"
    )

    # ------------------------------------------------------------
    # MARKET DATA / CACHE
    # ------------------------------------------------------------

    cache = load_or_refresh_market_data(
        current_symbols
    )

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

    runtime = (
        time.time()
        - start_time
    )

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
        "Latest Nifty 500 universe "
        "refreshed before processing."
    )

    print(
        "Cache reconciled with current "
        "Nifty 500 constituents."
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