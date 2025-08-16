# repositories/user_settings.py

import json
from psycopg_pool import AsyncConnectionPool
from settings.default_settings import DEFAULT_SETTINGS, DEFAULT_EXCHANGES, DEFAULT_TIME_ZONE
from settings.logging_config import get_logger

logger = get_logger(__name__)


class UserSettingsRepository:
    CREATE_TABLE_QUERY = f"""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id BIGINT PRIMARY KEY,
        period INTEGER DEFAULT {DEFAULT_SETTINGS["period"]},
        threshold REAL DEFAULT {DEFAULT_SETTINGS["threshold"]},
        active_exchanges VARCHAR(250) DEFAULT '{json.dumps(DEFAULT_EXCHANGES)}',
        time_zone VARCHAR(50) DEFAULT '{DEFAULT_TIME_ZONE}'
    )
    """

    def __init__(self, pool: AsyncConnectionPool):
        self.pool = pool

    async def init_table(self):
        async with self.pool.connection() as conn:
            await conn.execute(self.CREATE_TABLE_QUERY)
            await conn.commit()


    async def get_user_settings(self, user_id: int):
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT period, threshold, active_exchanges, time_zone FROM user_settings WHERE user_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
        if row:
            period, threshold, active_exchanges, time_zone = row

            return {
                "period": period or DEFAULT_SETTINGS["period"],
                "threshold": threshold or DEFAULT_SETTINGS["threshold"],
                "active_exchanges": json.loads(active_exchanges) if active_exchanges else DEFAULT_EXCHANGES,
                "time_zone": time_zone or DEFAULT_TIME_ZONE,
            }
        return None

    async def update_user_settings(self, user_id: int, period=None, threshold=None, active_exchanges=None, time_zone=None):
        existing = await self.get_user_settings(user_id)

        if existing is None:
            query = """
                INSERT INTO user_settings (user_id, period, threshold, active_exchanges, time_zone)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (
                user_id,
                period or DEFAULT_SETTINGS["period"],
                threshold or DEFAULT_SETTINGS["threshold"],
                json.dumps(active_exchanges or DEFAULT_EXCHANGES),
                time_zone or DEFAULT_TIME_ZONE,
            )
        else:
            query = """
                UPDATE user_settings
                SET period = %s, threshold = %s, active_exchanges = %s, time_zone = %s
                WHERE user_id = %s
            """
            values = (
                period if period is not None else existing["period"],
                threshold if threshold is not None else existing["threshold"],
                json.dumps(active_exchanges if active_exchanges is not None else existing["active_exchanges"]),
                time_zone if time_zone is not None else existing["time_zone"],
                user_id
            )

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, values)
            await conn.commit()

