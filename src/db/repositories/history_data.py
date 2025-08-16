from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from psycopg import errors
from settings.default_settings import DEFAULT_EXCHANGES
from settings.logging_config import get_logger

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
                            symbol CHARACTER(50) NOT NULL,
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
                            symbol CHARACTER(50) NOT NULL,
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

        if not data:
            logger.warning(f"write_oi `{exchange}_history_oi`: Missing required keys in data.")
            return

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

        if not data:
            logger.warning(f"write_ohlcv `{exchange}_history_ohlcv`: Missing required keys in data.")
            return

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(f"""
                    INSERT INTO {exchange}_history_ohlcv 
                    (symbol, timestamp, open, high, low, close, volume)
                    VALUES (%(symbol)s, %(timestamp)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s)
                    ON CONFLICT (symbol, timestamp) DO NOTHING
                """, data)
                await conn.commit()
                logger.info(f"Wrote {len(data)} OHLCV rows to `{exchange}_history_ohlcv` table.")




    async def get_oi_by_period(self, exchange: str, symbol: str, before_date: int, period_in_minutes: int = 24 *60) -> list[dict]:

        since_date = before_date - period_in_minutes * 60 * 1000

        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    f"""
                    SELECT timestamp, open_interest
                    FROM {exchange}_history_oi
                    WHERE symbol = %s
                    AND timestamp <= to_timestamp(%s)
                    AND timestamp >= to_timestamp(%s)
                    ORDER BY timestamp DESC
                    """,
                    (symbol, before_date / 1000.0, since_date / 1000.0)
                )
                rows = await cur.fetchall()
                return rows


    async def get_ohlcv_by_period(self, exchange: str, symbol: str, before_date: int, since_date: int) -> list[dict]:

        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    f"""
                    SELECT timestamp, close, volume
                    FROM {exchange}_history_ohlcv
                    WHERE symbol = %s
                    AND timestamp <= to_timestamp(%s)
                    AND timestamp >= to_timestamp(%s)
                    ORDER BY timestamp DESC
                    """,
                    (symbol, before_date / 1000.0, since_date / 1000.0)
                )
                rows = await cur.fetchall()
                return rows