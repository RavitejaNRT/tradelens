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

NEW:
    Top 30 stocks now include:
        - Sector
        - Industry

    Sector / industry metadata is cached separately so that
    repeated runs do not repeatedly query Yahoo Finance.

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

# Separate metadata cache.
METADATA_CACHE_FILE = (
    "tradelens_sector_industry_cache.pkl"
)

MONTHS_REQUIRED = 13

# EMA breadth periods
EMA_PERIODS = [20, 50, 200]


# ================================================================
# DISPLAY
# ================================================================

def print_header(title):

    print()
    print("=" * 120)
    print(title)
    print("=" * 120)


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
# SECTOR / INDUSTRY METADATA
# ================================================================

def load_metadata_cache():
    """
    Load previously saved sector / industry metadata.

    Returns:
        dict
    """

    metadata_cache = {}

    if not os.path.exists(
        METADATA_CACHE_FILE
    ):

        return metadata_cache

    try:

        with open(
            METADATA_CACHE_FILE,
            "rb"
        ) as f:

            loaded = pickle.load(f)

        if isinstance(
            loaded,
            dict
        ):

            metadata_cache = loaded

    except Exception as error:

        print()
        print(
            "Sector / industry metadata cache "
            "could not be loaded."
        )

        print(
            f"Reason : {error}"
        )

        metadata_cache = {}

    return metadata_cache


def save_metadata_cache(
    metadata_cache
):
    """
    Save sector / industry metadata.
    """

    try:

        with open(
            METADATA_CACHE_FILE,
            "wb"
        ) as f:

            pickle.dump(
                metadata_cache,
                f
            )

    except Exception as error:

        print()
        print(
            "Warning: Could not save "
            "sector / industry metadata cache."
        )

        print(
            f"Reason : {error}"
        )


def get_sector_industry(
    symbol,
    metadata_cache
):
    """
    Get sector and industry for one stock.

    Existing metadata is reused from cache.

    Yahoo Finance is queried only when the symbol
    is not already present in the metadata cache.

    Returns:
        sector, industry
    """

    symbol = normalize_symbol(
        symbol
    )

    # ------------------------------------------------------------
    # USE EXISTING CACHE
    # ------------------------------------------------------------

    if symbol in metadata_cache:

        cached = metadata_cache[
            symbol
        ]

        if isinstance(
            cached,
            dict
        ):

            sector = cached.get(
                "sector",
                "Unknown"
            )

            industry = cached.get(
                "industry",
                "Unknown"
            )

            return (
                sector or "Unknown",
                industry or "Unknown"
            )

    # ------------------------------------------------------------
    # QUERY YAHOO FINANCE
    # ------------------------------------------------------------

    try:

        ticker = yf.Ticker(
            symbol
        )

        info = ticker.get_info()

        sector = info.get(
            "sector",
            "Unknown"
        )

        industry = info.get(
            "industry",
            "Unknown"
        )

        sector = (
            str(sector).strip()
            if sector
            else "Unknown"
        )

        industry = (
            str(industry).strip()
            if industry
            else "Unknown"
        )

    except Exception:

        sector = "Unknown"
        industry = "Unknown"

    # ------------------------------------------------------------
    # SAVE IN MEMORY CACHE
    # ------------------------------------------------------------

    metadata_cache[
        symbol
    ] = {
        "sector": sector,
        "industry": industry,
    }

    return (
        sector,
        industry
    )


def add_sector_industry(
    selected
):
    """
    Add sector and industry information to the
    already-selected Top 30 stocks.

    IMPORTANT:
        This happens AFTER momentum ranking and selection.

        Therefore sector / industry metadata has NO
        effect on the strategy or stock selection.
    """

    print_header(
        "ADDING SECTOR / INDUSTRY INFORMATION"
    )

    metadata_cache = load_metadata_cache()

    print(
        f"Metadata cache entries : "
        f"{len(metadata_cache)}"
    )

    new_metadata = 0

    sectors = []
    industries = []

    for _, row in selected.iterrows():

        symbol = row["symbol"]

        existed_before = (
            symbol in metadata_cache
        )

        sector, industry = (
            get_sector_industry(
                symbol,
                metadata_cache
            )
        )

        if not existed_before:
            new_metadata += 1

        sectors.append(
            sector
        )

        industries.append(
            industry
        )

    selected = selected.copy()

    selected["sector"] = sectors

    selected["industry"] = industries

    save_metadata_cache(
        metadata_cache
    )

    print()
    print(
        f"New metadata fetched : "
        f"{new_metadata}"
    )

    print(
        f"Metadata cache total : "
        f"{len(metadata_cache)}"
    )

    print(
        f"Saved metadata cache : "
        f"{METADATA_CACHE_FILE}"
    )

    return selected


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
        if isinstance(
            data.columns,
            pd.MultiIndex
        ):

            if (
                "Close"
                not in data.columns.get_level_values(0)
            ):

                return None

            close = data["Close"]

            if isinstance(
                close,
                pd.DataFrame
            ):

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

        close.index = pd.to_datetime(
            close.index
        )

        return close

    except Exception:
        return None


def load_or_refresh_market_data(
    current_symbols
):
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

    print_header(
        "MARKET DATA / CACHE RECONCILIATION"
    )

    print(
        f"Current Nifty 500 symbols : "
        f"{len(current_symbols)}"
    )

    cache = {}

    # ------------------------------------------------------------
    # LOAD EXISTING CACHE
    # ------------------------------------------------------------

    if os.path.exists(
        CACHE_FILE
    ):

        try:

            print(
                f"Loading existing cache : "
                f"{CACHE_FILE}"
            )

            with open(
                CACHE_FILE,
                "rb"
            ) as f:

                loaded_cache = pickle.load(
                    f
                )

            if isinstance(
                loaded_cache,
                dict
            ):

                for symbol, close in (
                    loaded_cache.items()
                ):

                    normalized = normalize_symbol(
                        symbol
                    )

                    if (
                        normalized
                        and isinstance(
                            close,
                            pd.Series
                        )
                    ):

                        cache[
                            normalized
                        ] = close

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

    current_set = set(
        current_symbols
    )

    cached_set = set(
        cache.keys()
    )

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

        total = len(
            missing_symbols
        )

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

                cache[
                    symbol
                ] = close

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

    with open(
        CACHE_FILE,
        "wb"
    ) as f:

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

            current_cache[
                symbol
            ] = cache[symbol]

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

def build_monthly_prices(
    cache
):

    print()
    print(
        "Building monthly price matrix..."
    )

    monthly = {}

    for symbol, close in cache.items():

        try:

            series = close.copy()

            series.index = pd.to_datetime(
                series.index
            )

            series = series.sort_index()

            # Month-end price.
            monthly_close = (
                series
                .resample("ME")
                .last()
            )

            monthly_close = (
                monthly_close
                .dropna()
            )

            if (
                len(monthly_close)
                >= MONTHS_REQUIRED
            ):

                monthly[
                    symbol
                ] = monthly_close

        except Exception:
            continue

    prices = pd.DataFrame(
        monthly
    )

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

def calculate_momentum(
    prices
):
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
        prices.index
        <= last_completed_month
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
        [
            float("inf"),
            float("-inf")
        ],
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

    return (
        result,
        signal_month
    )


# ================================================================
# SELECT TOP 30
# ================================================================

def select_top_30(
    momentum_df
):

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

    # ------------------------------------------------------------
    # DISPLAY COLUMNS
    # ------------------------------------------------------------

    print(
        f"{'Rank':>4}  "
        f"{'Symbol':<20}  "
        f"{'Sector':<24}  "
        f"{'Industry':<34}  "
        f"{'Momentum':>10}  "
        f"{'Weight':>8}"
    )

    print(
        "-" * 120
    )

    # ------------------------------------------------------------
    # DISPLAY ROWS
    # ------------------------------------------------------------

    for _, row in selected.iterrows():

        print(
            f"{int(row['rank']):>4}  "
            f"{str(row['symbol']):<20}  "
            f"{str(row['sector']):<24}  "
            f"{str(row['industry']):<34}  "
            f"{row['momentum'] * 100:>9.2f}%  "
            f"{row['weight_pct']:>7.2f}%"
        )

    print(
        "-" * 120
    )

    # ------------------------------------------------------------
    # PORTFOLIO IMPLEMENTATION
    # ------------------------------------------------------------

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

    print(
        "Sector and industry are "
        "display-only metadata."
    )

    print(
        "Sector and industry do NOT affect "
        "ranking or stock selection."
    )


# ================================================================
# NIFTY 500 EMA MARKET BREADTH
# ================================================================

def get_latest_data_dates(
    cache
):
    """
    Get the latest available market-data date for every
    current Nifty 500 constituent.

    Returns:
        dict {symbol: latest_date}
    """

    latest_dates = {}

    for symbol, close in cache.items():

        try:

            series = close.copy()

            series.index = pd.to_datetime(
                series.index
            )

            series = series.sort_index()

            series = pd.to_numeric(
                series,
                errors="coerce"
            ).dropna()

            if not series.empty:

                latest_dates[
                    symbol
                ] = (
                    series
                    .index[-1]
                    .normalize()
                )

        except Exception:
            continue

    return latest_dates


def get_breadth_label(
    percentage
):
    """
    Classify Nifty 500 participation.

    High    : 70% and above
    Medium  : 50% to below 70%
    Low     : below 50%
    """

    if percentage >= 70.0:
        return "High"

    if percentage >= 50.0:
        return "Medium"

    return "Low"


def get_market_breadth_pattern(
    pct_20,
    pct_50,
    pct_200
):
    """
    Describe the relationship between short-, medium-,
    and long-term market participation.
    """

    if (
        pct_20 < pct_50
        and pct_50 < pct_200
    ):

        return (
            "Short-term participation is weaker than "
            "medium- and long-term participation."
        )

    if (
        pct_20 > pct_50
        and pct_50 > pct_200
    ):

        return (
            "Short-term participation is stronger than "
            "medium- and long-term participation."
        )

    if (
        pct_20 > pct_50
        and pct_20 > pct_200
    ):

        return (
            "Short-term participation is stronger than "
            "medium- and long-term participation."
        )

    if (
        pct_20 < pct_50
        and pct_20 < pct_200
    ):

        return (
            "Short-term participation is weaker than "
            "medium- and long-term participation."
        )

    if (
        pct_20 < pct_50
        and pct_50 > pct_200
    ):

        return (
            "Medium-term participation is strongest, "
            "while short-term participation remains weaker."
        )

    if (
        pct_20 > pct_50
        and pct_50 < pct_200
    ):

        return (
            "Medium-term participation is weakest "
            "relative to short- and long-term participation."
        )

    return (
        "Market participation is mixed across "
        "short-, medium-, and long-term timeframes."
    )


def calculate_nifty500_ema_breadth(
    cache
):
    """
    Calculate Nifty 500 participation above 20D/50D/200D EMAs.

    Date handling:
    - Program run date is reported separately.
    - The latest available market-data date is the maximum latest date
      across the Nifty 500 stocks.
    - Each stock is assigned its own latest available data date.
    - Stocks whose latest available date is not the overall latest date
      are excluded from the EMA breadth denominator.
    - The distribution of stocks by latest available data date is reported
      so missing/stale market data is visible.

    This is an isolated reporting calculation. It does not modify the existing
    market/fundamental research dataframe or any existing scoring logic.
    """

    print_header(
        "CALCULATING NIFTY 500 EMA MARKET BREADTH"
    )

    # ------------------------------------------------------------
    # PROGRAM RUN DATE
    # ------------------------------------------------------------

    program_run_date = (
        pd.Timestamp.today()
        .normalize()
    )

    # ------------------------------------------------------------
    # GET EACH STOCK'S LATEST AVAILABLE DATA DATE
    # ------------------------------------------------------------

    latest_dates = get_latest_data_dates(
        cache
    )

    if not latest_dates:

        raise RuntimeError(
            "No usable market-data dates available "
            "for EMA breadth calculation."
        )

    # ------------------------------------------------------------
    # OVERALL LATEST MARKET-DATA DATE
    # ------------------------------------------------------------

    latest_market_data_date = max(
        latest_dates.values()
    )

    print(
        f"Program run date: "
        f"{program_run_date.strftime('%Y-%m-%d')}"
    )

    print(
        f"Latest available market-data date: "
        f"{latest_market_data_date.strftime('%Y-%m-%d')}"
    )

    # ------------------------------------------------------------
    # LATEST DATA DISTRIBUTION
    # ------------------------------------------------------------

    date_counts = (
        pd.Series(
            list(latest_dates.values())
        )
        .value_counts()
        .sort_index(
            ascending=False
        )
    )

    print()
    print(
        "Latest available data by date:"
    )

    for date, count in date_counts.items():

        print(
            f"{date.strftime('%Y-%m-%d')}: "
            f"{count} stocks"
        )

    # ------------------------------------------------------------
    # ONLY STOCKS WITH OVERALL LATEST DATE ARE ELIGIBLE
    # ------------------------------------------------------------

    eligible_symbols = [
        symbol
        for symbol, latest_date
        in latest_dates.items()
        if latest_date
        == latest_market_data_date
    ]

    valid_count = 0

    above_20 = 0
    above_50 = 0
    above_200 = 0

    # ------------------------------------------------------------
    # CALCULATE EMA BREADTH
    # ------------------------------------------------------------

    for symbol in eligible_symbols:

        try:

            close = cache[
                symbol
            ]

            series = close.copy()

            series.index = pd.to_datetime(
                series.index
            )

            series = series.sort_index()

            series = pd.to_numeric(
                series,
                errors="coerce"
            ).dropna()

            # ----------------------------------------------------
            # USE DATA ONLY THROUGH THE OVERALL LATEST DATE
            # ----------------------------------------------------

            data = series[
                series.index
                <= latest_market_data_date
            ]

            if data.empty:
                continue

            # Require sufficient history for the longest EMA.
            if len(data) < 200:
                continue

            # The stock must actually have a closing price
            # on the breadth date.
            if (
                latest_market_data_date
                not in data.index
            ):

                continue

            current_close = float(
                data.loc[
                    latest_market_data_date
                ]
            )

            # ----------------------------------------------------
            # 20D EMA
            # ----------------------------------------------------

            ema_20 = (
                data
                .ewm(
                    span=20,
                    adjust=False,
                    min_periods=20
                )
                .mean()
                .iloc[-1]
            )

            # ----------------------------------------------------
            # 50D EMA
            # ----------------------------------------------------

            ema_50 = (
                data
                .ewm(
                    span=50,
                    adjust=False,
                    min_periods=50
                )
                .mean()
                .iloc[-1]
            )

            # ----------------------------------------------------
            # 200D EMA
            # ----------------------------------------------------

            ema_200 = (
                data
                .ewm(
                    span=200,
                    adjust=False,
                    min_periods=200
                )
                .mean()
                .iloc[-1]
            )

            if (
                pd.isna(ema_20)
                or pd.isna(ema_50)
                or pd.isna(ema_200)
            ):

                continue

            valid_count += 1

            if current_close > ema_20:
                above_20 += 1

            if current_close > ema_50:
                above_50 += 1

            if current_close > ema_200:
                above_200 += 1

        except Exception:
            continue

    if valid_count == 0:

        raise RuntimeError(
            "No valid Nifty 500 stocks available "
            "for EMA breadth calculation."
        )

    # ------------------------------------------------------------
    # CALCULATE PARTICIPATION PERCENTAGES
    # ------------------------------------------------------------

    pct_20 = (
        above_20
        /
        valid_count
    ) * 100

    pct_50 = (
        above_50
        /
        valid_count
    ) * 100

    pct_200 = (
        above_200
        /
        valid_count
    ) * 100

    # ------------------------------------------------------------
    # CLASSIFICATION
    # ------------------------------------------------------------

    label_20 = get_breadth_label(
        pct_20
    )

    label_50 = get_breadth_label(
        pct_50
    )

    label_200 = get_breadth_label(
        pct_200
    )

    # ------------------------------------------------------------
    # MARKET BREADTH PATTERN
    # ------------------------------------------------------------

    pattern = get_market_breadth_pattern(
        pct_20,
        pct_50,
        pct_200
    )

    # ------------------------------------------------------------
    # DISPLAY FINAL BREADTH
    # ------------------------------------------------------------

    print()
    print(
        f"Breadth date: "
        f"{latest_market_data_date.strftime('%Y-%m-%d')}"
    )

    print(
        f"Valid Nifty 500 stocks: "
        f"{valid_count}"
    )

    print(
        f"Above 20D EMA: "
        f"{above_20} "
        f"({pct_20:.2f}%) — "
        f"{label_20}"
    )

    print(
        f"Above 50D EMA: "
        f"{above_50} "
        f"({pct_50:.2f}%) — "
        f"{label_50}"
    )

    print(
        f"Above 200D EMA: "
        f"{above_200} "
        f"({pct_200:.2f}%) — "
        f"{label_200}"
    )

    print(
        f"Market Breadth Pattern: "
        f"{pattern}"
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
            "sector",
            "industry",
            "momentum",
            "weight",
            "weight_pct",
        ]
    ].copy()

    output["signal_month"] = (
        signal_month.strftime(
            "%Y-%m"
        )
    )

    output["holding_month"] = (
        holding_month.strftime(
            "%Y-%m"
        )
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
        "Optimization   : NONE"
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
        calculate_momentum(
            prices
        )
    )

    # ------------------------------------------------------------
    # TOP 30
    # ------------------------------------------------------------

    selected = select_top_30(
        momentum_df
    )

    # ------------------------------------------------------------
    # SECTOR / INDUSTRY
    #
    # IMPORTANT:
    # This happens AFTER Top 30 selection.
    # It cannot influence ranking or selection.
    # ------------------------------------------------------------

    selected = add_sector_industry(
        selected
    )

    # ------------------------------------------------------------
    # DISPLAY
    # ------------------------------------------------------------

    display_portfolio(
        selected,
        signal_month
    )

    # ------------------------------------------------------------
    # NIFTY 500 EMA MARKET BREADTH
    # ------------------------------------------------------------

    calculate_nifty500_ema_breadth(
        cache
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
        f"Runtime : "
        f"{runtime:.2f} seconds"
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

    print(
        "Sector and industry are "
        "display-only metadata."
    )

    # ------------------------------------------------------------
    # PROGRAM RUNTIME
    # ------------------------------------------------------------

    print_header(
        "PROGRAM RUNTIME"
    )

    end_timestamp = pd.Timestamp.now()

    elapsed_seconds = (
        time.time()
        - start_time
    )

    elapsed_minutes = int(
        elapsed_seconds // 60
    )

    elapsed_remaining_seconds = (
        elapsed_seconds
        -
        (elapsed_minutes * 60)
    )

    print(
        f"Start timestamp : "
        f"{pd.Timestamp.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        f"End timestamp   : "
        f"{end_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        f"Elapsed seconds : "
        f"{elapsed_seconds:.2f}"
    )

    print(
        f"Total runtime   : "
        f"{elapsed_minutes:02d}:"
        f"{elapsed_remaining_seconds:05.2f}"
    )

    print(
        "=" * 120
    )


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    main()
