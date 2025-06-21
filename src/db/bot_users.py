"""
bot_users.py

Handles interaction with the SQLite database to store and retrieve user-specific screener settings.
This includes user preferences such as scan period, threshold percentage, and selected exchanges.

Functions:
    init_db(): Initializes the database and creates the 'user_settings' table if it doesn't exist.
    get_user_settings(user_id): Retrieves the screener settings for a given user.
    update_user_settings(user_id, period, threshold, active_exchanges): Inserts or updates screener settings for a user.
"""

import aiosqlite
from config import config
import json
from app_logic.default_settings import DEFAULT_SETTINGS, DEFAULT_EXCHANGES, DEFAULT_TIME_ZONE

config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)


async def init_db():
    """
    Initializes the SQLite database by creating the 'user_settings' table if it doesn't exist.
    Sets default values for active exchanges using the DEFAULT_EXCHANGES list.
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        default_exchanges_str = json.dumps(DEFAULT_EXCHANGES)
        await db.execute(f'''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                period INTEGER,
                threshold REAL,
                active_exchanges TEXT DEFAULT '{default_exchanges_str}',
                time_zone TEXT DEFAULT '{DEFAULT_TIME_ZONE}'
            )
        ''')
        await db.commit()


async def get_user_settings(user_id: int):
    """
    Retrieves the user's screener settings from the database.

    Args:
        user_id (int): Telegram user ID.

    Returns:
        dict or None: A dictionary with keys 'period', 'threshold', and 'active_exchanges'.
                      Returns None if the user is not found in the database.
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute("SELECT period, threshold, active_exchanges, time_zone FROM user_settings WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return {
                "period": row[0] if row[0] else DEFAULT_SETTINGS["period"],
                "threshold": row[1] if row[1] else DEFAULT_SETTINGS["threshold"],
                "active_exchanges": json.loads(row[2]) if row[2] else DEFAULT_EXCHANGES,
                "time_zone": row[3] if row[3] else DEFAULT_TIME_ZONE
            }
        else:
            return None


async def update_user_settings(user_id: int, period=None, threshold=None, active_exchanges=None, time_zone=None):
    """
    Inserts new or updates existing screener settings for a given user.

    Args:
        user_id (int): Telegram user ID.
        period (int, optional): Time period in minutes to check for growth.
        threshold (float, optional): Growth percentage threshold.
        active_exchanges (list[str], optional): List of exchange names to monitor.
        time_zone (str, optional): IANA time zone ("Europe/Kiev", "America/New_York", "UTC").
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        existing = await get_user_settings(user_id)
        if existing is None:
            await db.execute(
                "INSERT INTO user_settings (user_id, period, threshold, active_exchanges, time_zone) VALUES (?, ?, ?, ?, ?)",
                (
                    user_id,
                    period or DEFAULT_SETTINGS["period"],
                    threshold or DEFAULT_SETTINGS["threshold"],
                    json.dumps(active_exchanges or DEFAULT_EXCHANGES),
                    time_zone or DEFAULT_TIME_ZONE
                )
            )
        else:
            new_period = period if period is not None else existing["period"]
            new_threshold = threshold if threshold is not None else existing["threshold"]
            new_exchanges = json.dumps(active_exchanges if active_exchanges is not None else existing["active_exchanges"])
            new_time_zone = time_zone if time_zone is not None else existing["time_zone"]
            await db.execute(
                "UPDATE user_settings SET period = ?, threshold = ?, active_exchanges = ?, time_zone = ? WHERE user_id = ?",
                (new_period, new_threshold, new_exchanges, new_time_zone, user_id)
            )
        await db.commit()
