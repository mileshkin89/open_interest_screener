import aiosqlite
from config import config
import json
from app_logic.default_settings import DEFAULT_SETTINGS, DEFAULT_EXCHANGES

config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)


async def init_db():
    async with aiosqlite.connect(config.DB_PATH) as db:
        default_exchanges_str = json.dumps(DEFAULT_EXCHANGES)
        await db.execute(f'''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                period INTEGER,
                threshold REAL,
                active_exchanges TEXT DEFAULT '{default_exchanges_str}'
            )
        ''')
        await db.commit()


async def get_user_settings(user_id: int):
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute("SELECT period, threshold, active_exchanges FROM user_settings WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return {
                "period": row[0] if row[0] else DEFAULT_SETTINGS["period"],
                "threshold": row[1] if row[1] else DEFAULT_SETTINGS["threshold"],
                "active_exchanges": json.loads(row[2]) if row[2] else DEFAULT_EXCHANGES
            }
        else:
            return None

# async def get_user_settings(user_id: int):
#     async with aiosqlite.connect(config.DB_PATH) as db:
#         cursor = await db.execute("SELECT period, threshold FROM user_settings WHERE user_id = ?", (user_id,))
#         row = await cursor.fetchone()
#         if row:
#             return {"period": row[0], "threshold": row[1]}
#         else:
#             return None


async def update_user_settings(user_id: int, period=None, threshold=None, active_exchanges=None):
    async with aiosqlite.connect(config.DB_PATH) as db:
        existing = await get_user_settings(user_id)
        if existing is None:
            await db.execute(
                "INSERT INTO user_settings (user_id, period, threshold, active_exchanges) VALUES (?, ?, ?, ?)",
                (
                    user_id,
                    period or DEFAULT_SETTINGS["period"],
                    threshold or DEFAULT_SETTINGS["threshold"],
                    json.dumps(active_exchanges or DEFAULT_EXCHANGES)
                )
            )
        else:
            new_period = period if period is not None else existing["period"]
            new_threshold = threshold if threshold is not None else existing["threshold"]
            new_exchanges = json.dumps(active_exchanges if active_exchanges is not None else existing["active_exchanges"])
            await db.execute(
                "UPDATE user_settings SET period = ?, threshold = ?, active_exchanges = ? WHERE user_id = ?",
                (new_period, new_threshold, new_exchanges, user_id)
            )
        await db.commit()

# async def update_user_settings(user_id: int, period=None, threshold=None):
#     async with aiosqlite.connect(config.DB_PATH) as db:
#         existing = await get_user_settings(user_id)
#         if existing is None:
#             await db.execute(
#                 "INSERT INTO user_settings (user_id, period, threshold) VALUES (?, ?, ?)",
#                 (user_id, period or DEFAULT_SETTINGS["period"], threshold or DEFAULT_SETTINGS["threshold"])
#             )
#         else:
#             new_period = period if period is not None else existing["period"]
#             new_threshold = threshold if threshold is not None else existing["threshold"]
#             await db.execute(
#                 "UPDATE user_settings SET period = ?, threshold = ? WHERE user_id = ?",
#                 (new_period, new_threshold, user_id)
#             )
#         await db.commit()

