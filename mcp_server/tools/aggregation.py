from services.price_service import PriceService

price_service = PriceService()

def aggregate_data(symbol: str) -> dict:
    """
    특정 암호화폐 종목의 평균, 최고, 최저 가격 및 총 수집 건수를 집계합니다.
    :param symbol: 집계할 암호화폐 심볼 (예: BTC, ETH)
    """
    return price_service.get_aggregated_stats(symbol=symbol)