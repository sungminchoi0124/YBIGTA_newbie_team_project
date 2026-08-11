from services.price_service import PriceService

price_service = PriceService()

def get_latest_data(limit: int = 10) -> list:
    """
    가장 최근에 수집된 암호화폐 가격 데이터 목록을 조회합니다.
    :param limit: 조회할 데이터 개수 (기본값: 10, 최대: 50)
    """
    return price_service.get_latest_prices(limit=limit)