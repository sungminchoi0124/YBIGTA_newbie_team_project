from services.price_service import PriceService

price_service = PriceService()

def search_data(symbol: str, limit: int = 20) -> list:
    """
    특정 암호화폐 종목(BTC, ETH 등)의 과거 가격 수집 내역을 검색합니다.
    :param symbol: 검색할 암호화폐 심볼 (예: BTC, ETH)
    :param limit: 조회할 데이터 개수 (기본값: 20, 최대: 100)
    """
    return price_service.search_prices_by_symbol(symbol=symbol, limit=limit)