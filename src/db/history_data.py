# history_data.py

from psycopg_pool import AsyncConnectionPool
from psycopg import errors

CREATE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS history_data (
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open_interest DOUBLE PRECISION,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    PRIMARY KEY (symbol, exchange, timestamp)
);
"""

CREATE_HYPERTABLE = """
SELECT create_hypertable('history_data', 'timestamp', if_not_exists => TRUE);
"""


async def init_timescale_table(pool: AsyncConnectionPool):
    async with pool.connection() as conn:
        # remove later
        await conn.execute("DROP TABLE IF EXISTS history_data;")
        await conn.commit()

        await conn.execute(CREATE_HISTORY_TABLE)
        await conn.execute(CREATE_HYPERTABLE)
        await conn.commit()


async def enable_retention_policy(pool: AsyncConnectionPool):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("""
                    SELECT add_retention_policy('history_data', INTERVAL '1 day');
                """)
            except errors.DuplicateObject:
                pass


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


async def get_historical_oi(pool: AsyncConnectionPool, symbol: str, exchange: str, before_date: int) -> list[dict]:
    since_date = before_date - 24 * 60 * 60 * 1000  # 24 часа в миллисекундах

    async with pool.connection() as conn:
        async with conn.execute(
            """
            SELECT timestamp, open_interest FROM history_data
            WHERE symbol = $1 AND exchange = $2 AND timestamp <= $3 AND timestamp >= $4
            ORDER BY timestamp DESC
            """,
            (symbol, exchange, before_date, since_date)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]