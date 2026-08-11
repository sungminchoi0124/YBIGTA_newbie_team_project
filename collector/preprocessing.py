from datetime import datetime


def preprocess_candle(data: dict) -> dict:
    market = data["market"]
    symbol = market.split("-")[1]

    return {
        "symbol": symbol,
        "market": market,
        "candle_time": data["candle_date_time_kst"],
        "open_price": data["opening_price"],
        "high_price": data["high_price"],
        "low_price": data["low_price"],
        "close_price": data["trade_price"],
        "volume": data["candle_acc_trade_volume"],
        "trade_value": data["candle_acc_trade_price"],
        "collected_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }