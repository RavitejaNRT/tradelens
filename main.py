from trade_data import get_market_data


def analyze_stock(symbol):
    data = get_market_data(symbol)

    close_prices = data["Close"].iloc[:, 0]

    data["EMA_50"] = close_prices.ewm(span=50, adjust=False).mean()
    data["EMA_200"] = close_prices.ewm(span=200, adjust=False).mean()

    latest = data.iloc[-1]

    close = latest["Close"].iloc[0]
    ema_50 = latest["EMA_50"].iloc[0]
    ema_200 = latest["EMA_200"].iloc[0]

    high_52_week = data["High"].iloc[:, 0].max()

    distance_from_high = (
        (high_52_week - close) / high_52_week
    ) * 100

    near_52_week_high = distance_from_high <= 5

    volume = data["Volume"].iloc[:, 0]

    average_volume_20 = volume.rolling(20).mean()

    latest_volume = volume.iloc[-1]

    volume_pass = latest_volume > (1.5 * average_volume_20.iloc[-1])

    trend_pass = (
        close > ema_200
        and close > ema_50
        and ema_50 > ema_200
    )

    return {
    "symbol": symbol,
    "close": close,
    "ema_50": ema_50,
    "ema_200": ema_200,
    "trend_pass": trend_pass,
    "high_52_week": high_52_week,
    "distance_from_high": distance_from_high,
    "near_52_week_high": near_52_week_high,
    "latest_volume": latest_volume,
    "average_volume_20": average_volume_20.iloc[-1],
    "volume_pass": volume_pass
    }

symbols = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS"
]

passed_count = 0

for symbol in symbols:
    result = analyze_stock(symbol)

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
        "| Overall:", "PASS" if all_pass else "FAIL"
    )

    if all_pass:
        passed_count += 1

print()
print("Stocks passing all filters:", passed_count)