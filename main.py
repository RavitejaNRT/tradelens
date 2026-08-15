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
    "trend_pass": trend_pass
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

    if result["trend_pass"]:
        print("TREND PASS:", result["symbol"])
        passed_count += 1
    else:
        print("TREND FAIL:", result["symbol"])

print()
print("Stocks passing trend filter:", passed_count)