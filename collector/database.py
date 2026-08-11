import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def get_engine():
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    database_url = (
        f"mysql+pymysql://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

    return create_engine(database_url, pool_pre_ping=True)


def insert_candle(data: dict):
    engine = get_engine()

    query = text("""
        INSERT INTO crypto_prices (
            symbol,
            market,
            candle_time,
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
            trade_value,
            collected_at
        )
        VALUES (
            :symbol,
            :market,
            :candle_time,
            :open_price,
            :high_price,
            :low_price,
            :close_price,
            :volume,
            :trade_value,
            :collected_at
        )
        ON DUPLICATE KEY UPDATE
            open_price = VALUES(open_price),
            high_price = VALUES(high_price),
            low_price = VALUES(low_price),
            close_price = VALUES(close_price),
            volume = VALUES(volume),
            trade_value = VALUES(trade_value),
            collected_at = VALUES(collected_at)
    """)

    with engine.begin() as connection:
        connection.execute(query, data)

def test_connection():
    engine = get_engine()

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("DB connection successful")