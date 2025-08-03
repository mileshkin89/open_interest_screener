from psycopg_pool import AsyncConnectionPool
from psycopg import errors
from app_logic.default_settings import DEFAULT_EXCHANGES
from logging_config import get_logger

logger = get_logger(__name__)


class HistoryDataRepository:

    def __init__(self, pool: AsyncConnectionPool):
        self.pool = pool


    async def init_table(self):
        async with self.pool.connection() as conn:
            for exchange in DEFAULT_EXCHANGES:
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {exchange}_history_oi (
                            symbol TEXT NOT NULL,
                            timestamp TIMESTAMPTZ NOT NULL,
                            open_interest DOUBLE PRECISION,
                            PRIMARY KEY (symbol, timestamp)
                        );
                    """
                )
                await conn.execute(
                    f"""
                    SELECT create_hypertable('{exchange}_history_oi', 'timestamp', if_not_exists => TRUE);
                    """
                )
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {exchange}_history_ohlcv (
                            symbol TEXT NOT NULL,
                            timestamp TIMESTAMPTZ NOT NULL,
                            open DOUBLE PRECISION,
                            high DOUBLE PRECISION,
                            low DOUBLE PRECISION,
                            close DOUBLE PRECISION,
                            volume DOUBLE PRECISION,
                            PRIMARY KEY (symbol, timestamp)
                        );
                    """
                )
                await conn.execute(
                    f"""
                    SELECT create_hypertable('{exchange}_history_ohlcv', 'timestamp', if_not_exists => TRUE);
                    """
                )
            await conn.commit()


    async def enable_retention_policy(self):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                for exchange in DEFAULT_EXCHANGES:
                    try:
                        await cur.execute(f"""
                            SELECT add_retention_policy('{exchange}_history_oi', INTERVAL '1 day');
                        """)
                        await cur.execute(f"""
                            SELECT add_retention_policy('{exchange}_history_ohlcv', INTERVAL '1 day');
                        """)
                    except errors.DuplicateObject:
                        pass


    def _filter_valid_keys(self, data: list[dict], required_keys: set[str]) -> list[dict]:
        return [d for d in data if required_keys.issubset(d)]

    async def write_oi(self, data: list[dict], exchange: str):

        if not data or not exchange:
            return

        required_keys = {"symbol", "timestamp", "open_interest"}
        data = self._filter_valid_keys(data, required_keys)

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(f"""
                    INSERT INTO {exchange}_history_oi (symbol, timestamp, open_interest)
                    VALUES (%(symbol)s, %(timestamp)s, %(open_interest)s)
                    ON CONFLICT (symbol, timestamp) DO NOTHING
                """, data)
            await conn.commit()
        logger.info(f"Wrote {len(data)} OI rows to `{exchange}_history_oi` table.")


    async def write_ohlcv(self, data: list[dict], exchange: str):

        if not data or not exchange:
            return

        required_keys = {"symbol", "timestamp", "open", "high", "low", "close", "volume"}
        data = self._filter_valid_keys(data, required_keys)

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(f"""
                    INSERT INTO {exchange}_history_ohlcv (symbol, timestamp, open, high, low, close, volume)
                    VALUES (%(symbol)s, %(timestamp)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s)
                    ON CONFLICT (symbol, timestamp) DO NOTHING
                """, data)
            await conn.commit()
        logger.info(f"Wrote {len(data)} OHLCV rows to `{exchange}_history_ohlcv` table.")


    async def get_historical_oi(self, symbol: str, exchange: str, before_date: int) -> list[dict]:
        """
        Returns Open Interest history for the last 24 hours before a given timestamp.

        Args:
            symbol (str): Trading pair symbol.
            exchange (str): Exchange name.
            before_date (int): Upper bound for timestamp (in milliseconds).

        Returns:
            list[dict]: List of rows with timestamp and open_interest.
        """
        since_date = before_date - 24 * 60 * 60 * 1000  # 24 hours in ms

        async with self.pool.connection() as conn:
            async with conn.execute(
                f"""
                SELECT timestamp, open_interest FROM {exchange}_history_oi
                WHERE symbol = $1  AND timestamp <= $2 AND timestamp >= $3
                ORDER BY timestamp DESC
                """,
                (symbol, before_date, since_date)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
