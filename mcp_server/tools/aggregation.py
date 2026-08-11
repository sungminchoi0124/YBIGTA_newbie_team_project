import os
import pymysql

def aggregate_data(symbol: str):
    conn = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT 
                    symbol,
                    ROUND(AVG(close_price), 2) AS avg_price,
                    MAX(close_price) AS max_price,
                    MIN(close_price) AS min_price,
                    COUNT(*) AS total_records
                FROM crypto_prices
                WHERE symbol = %s
                GROUP BY symbol
            """
            cursor.execute(query, (symbol,))
            result = cursor.fetchone()
            return result if result else {}
    finally:
        conn.close()