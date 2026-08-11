import requests


BASE_URL = "https://api.upbit.com/v1/candles/minutes/60"


def fetch_candles(market: str, count: int = 2) -> list[dict]:
    params = {
        "market": market,
        "count": count
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()