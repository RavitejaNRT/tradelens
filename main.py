from universe import symbols
from trade_data import get_market_data_for_symbols


def calculate_one_year_return(close_prices):
    start_price = close_prices.iloc[0]
    latest_price = close_prices.iloc[-1]

    return ((latest_price - start_price) / start_price) * 100


def analyze_stock(symbol, data):
    close_prices = data["Close"][symbol]
    high_prices = data["High"][symbol]
    volume = data["Volume"][symbol]

    one_year_return = calculate_one_year_return(close_prices)

    ema_50 = close_prices.ewm(span=50, adjust=False).mean()
    ema_200 = close_prices.ewm(span=200, adjust=False).mean()

    close = close_prices.iloc[-1]
    latest_ema_50 = ema_50.iloc[-1]
    latest_ema_200 = ema_200.iloc[-1]

    high_52_week = high_prices.max()

    distance_from_high = (
        (high_52_week - close) / high_52_week
    ) * 100

    near_52_week_high = distance_from_high <= 5

    average_volume_20 = volume.rolling(20).mean()
    latest_volume = volume.iloc[-1]

    volume_pass = latest_volume > (
        1.5 * average_volume_20.iloc[-1]
    )

    trend_pass = (
        close > latest_ema_200
        and close > latest_ema_50
        and latest_ema_50 > latest_ema_200
    )

    return {
        "symbol": symbol,
        "close": close,
        "ema_50": latest_ema_50,
        "ema_200": latest_ema_200,
        "trend_pass": trend_pass,
        "high_52_week": high_52_week,
        "distance_from_high": distance_from_high,
        "near_52_week_high": near_52_week_high,
        "latest_volume": latest_volume,
        "average_volume_20": average_volume_20.iloc[-1],
        "volume_pass": volume_pass,
        "one_year_return": one_year_return,
    }


data = get_market_data_for_symbols(symbols)

passed_count = 0

for symbol in symbols:
    result = analyze_stock(symbol, data)

    trend_pass = result["trend_pass"]
    near_52_week_high = result["near_52_week_high"]
    volume_pass = result["volume_pass"]

    all_pass = (
        trend_pass
        and near_52_week_high
        and volume_pass
    )

    print(
        result["symbol"],
        "| Trend:", "PASS" if trend_pass else "FAIL",
        "| 52W High:", "PASS" if near_52_week_high else "FAIL",
        "| Volume:", "PASS" if volume_pass else "FAIL",
        "| Overall:", "PASS" if all_pass else "FAIL",
        "| 1Y Return:", round(result["one_year_return"], 2), "%"
    )

    if all_pass:
        passed_count += 1

print()
print("Stocks passing all filters:", passed_count)