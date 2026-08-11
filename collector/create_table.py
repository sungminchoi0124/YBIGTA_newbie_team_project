from sqlalchemy import text

from database import get_engine


CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS crypto_prices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    market VARCHAR(20) NOT NULL,
    candle_time DATETIME NOT NULL,
    open_price DECIMAL(20, 8) NOT NULL,
    high_price DECIMAL(20, 8) NOT NULL,
    low_price DECIMAL(20, 8) NOT NULL,
    close_price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(30, 12) NOT NULL,
    trade_value DECIMAL(30, 8) NOT NULL,
    collected_at DATETIME NOT NULL,
    UNIQUE KEY uq_market_candle (market, candle_time)
);
"""


def create_table():
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(text(CREATE_TABLE_QUERY))

    print("crypto_prices table ready")


if __name__ == "__main__":
    create_table()