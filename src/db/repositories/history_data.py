from psycopg_pool import AsyncConnectionPool
from psycopg import errors
from logging_config import get_logger

logger = get_logger(__name__)


class HistoryDataRepository:
    """
    Repository for managing the `history_data` table, including initialization,
    retention policies, and insertions of Open Interest and OHLCV data.
    """

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

    def __init__(self, pool: AsyncConnectionPool):
        self.pool = pool

    async def init_table(self):
        """
        Initializes the `history_data` table as a TimescaleDB hypertable.
        Optionally drops the table before creation (useful for development).
        """
        async with self.pool.connection() as conn:
            # for dev, remove later:
            await conn.execute("DROP TABLE IF EXISTS history_data;")
            await conn.commit()

            await conn.execute(self.CREATE_HISTORY_TABLE)
            await conn.execute(self.CREATE_HYPERTABLE)
            await conn.commit()

    async def enable_retention_policy(self):
        """
        Adds a retention policy to the `history_data` hypertable, retaining only 1 day of data.
        """
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute("""
                        SELECT add_retention_policy('history_data', INTERVAL '1 day');
                    """)
                except errors.DuplicateObject:
                    pass

    def _filter_valid_keys(self, data: list[dict], required_keys: set[str]) -> list[dict]:
        return [d for d in data if required_keys.issubset(d)]

    async def write_oi(self, data: list[dict]):
        """
        Inserts Open Interest data into the table.

        Args:
            data (list[dict]): List of dictionaries with keys:
                - symbol, exchange, timestamp, open_interest
        """
        if not data:
            return

        required_keys = {"symbol", "exchange", "timestamp", "open_interest"}
        data = self._filter_valid_keys(data, required_keys)

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.executemany("""
                    INSERT INTO history_data (symbol, exchange, timestamp, open_interest)
                    VALUES (%(symbol)s, %(exchange)s, %(timestamp)s, %(open_interest)s)
                    ON CONFLICT (symbol, exchange, timestamp) DO NOTHING
                """, data)
            await conn.commit()
        logger.info(f"Wrote {len(data)} OI rows to history_data table.")

    async def write_ohlcv(self, data: list[dict]):
        """
        Inserts OHLCV data into the table.

        Args:
            data (list[dict]): List of dictionaries with keys:
                - symbol, exchange, timestamp, open, high, low, close, volume
        """
        if not data:
            return

        required_keys = {"symbol", "exchange", "timestamp", "open", "high", "low", "close", "volume"}
        data = self._filter_valid_keys(data, required_keys)

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.executemany("""
                    INSERT INTO history_data (symbol, exchange, timestamp, open, high, low, close, volume)
                    VALUES (%(symbol)s, %(exchange)s, %(timestamp)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s)
                    ON CONFLICT (symbol, exchange, timestamp) DO NOTHING
                """, data)
            await conn.commit()
        logger.info(f"Wrote {len(data)} OHLCV rows to history_data table.")

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
                """
                SELECT timestamp, open_interest FROM history_data
                WHERE symbol = $1 AND exchange = $2 AND timestamp <= $3 AND timestamp >= $4
                ORDER BY timestamp DESC
                """,
                (symbol, exchange, before_date, since_date)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
