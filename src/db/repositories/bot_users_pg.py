# bot_users_pg.py

import json
from psycopg_pool import AsyncConnectionPool
from app_logic.default_settings import DEFAULT_SETTINGS, DEFAULT_EXCHANGES, DEFAULT_TIME_ZONE


CREATE_TABLE_QUERY = f"""
CREATE TABLE IF NOT EXISTS user_settings (
    user_id BIGINT PRIMARY KEY,
    period INTEGER DEFAULT {DEFAULT_SETTINGS["period"]},
    threshold INTEGER DEFAULT {DEFAULT_SETTINGS["threshold"]},
    active_exchanges TEXT DEFAULT '{json.dumps(DEFAULT_EXCHANGES)}',
    time_zone VARCHAR(50) DEFAULT '{DEFAULT_TIME_ZONE}'
)
"""


async def init_user_table(pool: AsyncConnectionPool):
    async with pool.connection() as conn:
        await conn.execute(
            CREATE_TABLE_QUERY,
            {
                "period": DEFAULT_SETTINGS["period"],
                "threshold": DEFAULT_SETTINGS["threshold"],
                "exchanges": json.dumps(DEFAULT_EXCHANGES),
                "time_zone": DEFAULT_TIME_ZONE
            }
        )


async def get_user_settings(pool: AsyncConnectionPool, user_id: int):
    async with pool.connection() as conn:
        row = await conn.execute(
            "SELECT period, threshold, active_exchanges, time_zone FROM user_settings WHERE user_id = %s",
            (user_id,)
        )
        result = await row.fetchone()
        if result:
            period, threshold, active_exchanges, time_zone = result
            return {
                "period": period or DEFAULT_SETTINGS["period"],
                "threshold": threshold or DEFAULT_SETTINGS["threshold"],
                "active_exchanges": json.loads(active_exchanges) if active_exchanges else DEFAULT_EXCHANGES,
                "time_zone": time_zone or DEFAULT_TIME_ZONE,
            }
        return None


async def update_user_settings(pool: AsyncConnectionPool, user_id: int, period=None, threshold=None, active_exchanges=None, time_zone=None):
    existing = await get_user_settings(user_id)

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

    async with pool.connection() as conn:
        await conn.execute(query, values)
        await conn.commit()
