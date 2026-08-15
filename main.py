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
    "near_52_week_high": near_52_week_high
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

    both_pass = trend_pass and near_52_week_high

    print(
        result["symbol"],
        "| Trend:", "PASS" if trend_pass else "FAIL",
        "| 52W High:", "PASS" if near_52_week_high else "FAIL",
        "| Overall:", "PASS" if both_pass else "FAIL"
    )

    if both_pass:
        passed_count += 1

print()
print("Stocks passing all filters:", passed_count)