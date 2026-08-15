import yfinance as yf


def get_market_data(symbol):
    data = yf.download(
        symbol,
        period="1y",
        interval="1d"
    )

    return data


def get_market_data_for_symbols(symbols):
    data = yf.download(
        symbols,
        period="1y",
        interval="1d"
    )

    return data