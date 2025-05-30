import aiosqlite
from config import config


async def init_db():
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                period INTEGER,
                threshold REAL
            )
        ''')
        await db.commit()


async def get_user_settings(user_id: int):
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute("SELECT period, threshold FROM user_settings WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return {"period": row[0], "threshold": row[1]}
        else:
            return None


async def update_user_settings(user_id: int, period=None, threshold=None):
    async with aiosqlite.connect(config.DB_PATH) as db:
        existing = await get_user_settings(user_id)
        if existing is None:
            await db.execute(
                "INSERT INTO user_settings (user_id, period, threshold) VALUES (?, ?, ?)",
                (user_id, period or 15, threshold or 0.02)
            )
        else:
            new_period = period if period is not None else existing["period"]
            new_threshold = threshold if threshold is not None else existing["threshold"]
            await db.execute(
                "UPDATE user_settings SET period = ?, threshold = ? WHERE user_id = ?",
                (new_period, new_threshold, user_id)
            )
        await db.commit()

