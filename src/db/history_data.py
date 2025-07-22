# history_data.py

from psycopg_pool import AsyncConnectionPool

CREATE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS history_data (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_interest FLOAT,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT
);
"""

CREATE_HYPERTABLE = """
SELECT create_hypertable('history_data', 'timestamp', if_not_exists => TRUE);
"""


async def init_timescale_table(pool: AsyncConnectionPool):
    async with pool.connection() as conn:
        await conn.execute(CREATE_HISTORY_TABLE)
        await conn.execute(CREATE_HYPERTABLE)
        await conn.commit()


async def write_oi_to_db(pool: AsyncConnectionPool, data: list[dict]):
    if not data:
        return

    async with pool.connection() as conn:
        await conn.executemany("""
            INSERT INTO history_data (symbol, exchange, timestamp, open_interest)
            VALUES (%(symbol)s, %(exchange)s, %(timestamp)s, %(open_interest)s)
        """, data)
        await conn.commit()


async def write_ohlcv_to_db(pool: AsyncConnectionPool, data: list[dict]):
    if not data:
        return

    async with pool.connection() as conn:
        await conn.executemany("""
            INSERT INTO history_data (symbol, exchange, timestamp, open, high, low, close, volume)
            VALUES (%(symbol)s, %(exchange)s, %(timestamp)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s)
        """, data)
        await conn.commit()
