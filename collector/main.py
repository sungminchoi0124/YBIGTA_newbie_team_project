from api import fetch_candles
from database import insert_candle
from preprocessing import preprocess_candle


MARKETS = ["KRW-BTC", "KRW-ETH"]


def main():
    for market in MARKETS:
        candles = fetch_candles(market, count=2)

        completed_candle = candles[1]

        processed = preprocess_candle(completed_candle)

        insert_candle(processed)

        print(f"[SUCCESS] {market} {processed['candle_time']} saved")


if __name__ == "__main__":
    main()