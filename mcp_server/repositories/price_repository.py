import os
import pymysql

class PriceRepository:
    def __init__(self):
        self.db_host = os.getenv("DB_HOST")
        self.db_user = os.getenv("DB_USER", "mcp_user")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME", "crypto_db")
        self.db_port = int(os.getenv("DB_PORT", 3306))

    def _get_connection(self):
        return pymysql.connect(
            host=self.db_host,
            user=self.db_user,
            password=self.db_password,
            database=self.db_name,
            port=self.db_port,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5
        )

    def fetch_latest_prices(self, limit: int):
        query = """
            SELECT symbol, price, collected_at 
            FROM crypto_prices 
            ORDER BY collected_at DESC 
            LIMIT %s
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (limit,))
                return cursor.fetchall()

    def fetch_prices_by_symbol(self, symbol: str, limit: int):
        query = """
            SELECT symbol, price, collected_at 
            FROM crypto_prices 
            WHERE symbol = %s 
            ORDER BY collected_at DESC 
            LIMIT %s
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (symbol, limit))
                return cursor.fetchall()

    def fetch_aggregated_stats(self, symbol: str):
        query = """
            SELECT 
                symbol, 
                AVG(price) AS avg_price, 
                MAX(price) AS max_price, 
                MIN(price) AS min_price, 
                COUNT(*) AS total_records 
            FROM crypto_prices 
            WHERE symbol = %s
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (symbol,))
                return cursor.fetchone()