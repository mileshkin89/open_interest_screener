
from psycopg_pool import AsyncConnectionPool
from psycopg import errors
from settings.logging_config import get_logger

logger = get_logger(__name__)


class SignalRepository:

    def __init__(self, pool: AsyncConnectionPool):
        self.pool = pool


    async def init_table(self):
        async with self.pool.connection() as conn:
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS signals (
                        symbol CHARACTER(50) NOT NULL,
                        exchange CHARACTER(30) NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        delta_oi DOUBLE PRECISION NOT NULL,
                        delta_minutes INTEGER NOT NULL,
                        PRIMARY KEY (symbol, timestamp)
                    );
                """
            )
            await conn.execute(
                f"""
                SELECT create_hypertable('signals', 'timestamp', if_not_exists => TRUE);
                """
            )
            await conn.commit()


    async def enable_retention_policy(self):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(f"""
                        SELECT add_retention_policy('signals', INTERVAL '1 day');
                    """)
                except errors.DuplicateObject:
                    pass



    async def write_signal(self, exchange: str, symbol: str, timestamp: int, delta_oi: float, delta_minutes: int):

        # "timestamp" - time since which open interest exceeded the threshold value
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"""
                    INSERT INTO signals (symbol, exchange, timestamp, delta_oi, delta_minutes)
                    VALUES (%(symbol)s, %(exchange)s, %(timestamp)s, %(delta_oi)s, %(delta_minutes)s)
                    ON CONFLICT (symbol, timestamp) DO NOTHING
                """, (symbol, exchange, timestamp, delta_oi, delta_minutes))
            await conn.commit()


        logger.info(f"Wrote signal for symbol `{symbol}` at {timestamp} to `signals` table.")


    async def count_signals(self, exchange: str, symbol: str, timestamp: int, delta_minutes: int, threshold: float) -> int:
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"""
                    SELECT COUNT(*)
                    FROM signals
                    WHERE symbol = %(symbol)s
                        AND exchange = %(exchange)s
                        AND timestamp >= %(timestamp)s
                        AND delta_minutes <= %(delta_minutes)s
                        AND delta_oi >= %(threshold)s
                """, (symbol, exchange, timestamp, delta_minutes, threshold))
                row = await cur.fetchone()
                return row[0]













