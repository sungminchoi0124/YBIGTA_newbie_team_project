import os
import pymysql

def get_latest_data(limit: int = 10):
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
                    id, 
                    symbol, 
                    market, 
                    candle_time, 
                    open_price, 
                    high_price, 
                    low_price, 
                    close_price AS price, 
                    volume, 
                    trade_value, 
                    collected_at
                FROM crypto_prices
                ORDER BY collected_at DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            return cursor.fetchall()
    finally:
        conn.close()