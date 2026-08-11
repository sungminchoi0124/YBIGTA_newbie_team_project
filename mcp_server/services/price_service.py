from repositories.price_repository import PriceRepository

class PriceService:
    def __init__(self):
        self.repo = PriceRepository()
        
        self.ALLOWED_SYMBOLS = {"BTC", "ETH", "SOL", "XRP"}

    def _validate_symbol(self, symbol: str) -> str:
        clean_symbol = symbol.strip().upper()
        if clean_symbol not in self.ALLOWED_SYMBOLS:
            raise ValueError(f"지원하지 않는 종목입니다: '{symbol}'. (허용 종목: {list(self.ALLOWED_SYMBOLS)})")
        return clean_symbol

    def get_latest_prices(self, limit: int = 10) -> list:
        
        safe_limit = min(max(1, limit), 50)
        return self.repo.fetch_latest_prices(limit=safe_limit)

    def search_prices_by_symbol(self, symbol: str, limit: int = 20) -> list:
        
        valid_symbol = self._validate_symbol(symbol)
        
        safe_limit = min(max(1, limit), 100)
        return self.repo.fetch_prices_by_symbol(symbol=valid_symbol, limit=safe_limit)

    def get_aggregated_stats(self, symbol: str) -> dict:
        valid_symbol = self._validate_symbol(symbol)
        result = self.repo.fetch_aggregated_stats(symbol=valid_symbol)
        
        if result and result.get("avg_price") is not None:
            result["avg_price"] = float(result["avg_price"])
            result["max_price"] = float(result["max_price"])
            result["min_price"] = float(result["min_price"])
        return result