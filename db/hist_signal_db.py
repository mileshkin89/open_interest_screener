# hist_signal_db.py

import aiosqlite
from config import config

config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)


async def init_db():
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS signals_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                exchange TEXT,
                threshold_period INTEGER,
                threshold REAL,
                delta_oi REAL,
                timestamp INTEGER
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_temp_symbol_time 
            ON signals_temp (symbol, timestamp)
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS signals_total (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                exchange TEXT,
                timestamp INTEGER,
                delta_oi REAL,
                delta_price REAL,
                delta_volume REAL,
                threshold_period INTEGER,
                threshold REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS history_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                exchange TEXT,
                timestamp INTEGER,
                open_interest REAL
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_timestamp
            ON history_temp (timestamp)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_symbol_exchange
            ON history_temp (symbol, exchange)
        """)
        await db.commit()


async def add_history_in_db(symbol: str, exchange: str, timestamp: int, open_interest: float):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            INSERT INTO  history_temp (symbol, exchange, timestamp, open_interest)
            VALUES (?, ?, ?, ?)
        """, (symbol, exchange, timestamp, open_interest))
        await db.commit()


async def add_signal_in_db(symbol: str, exchange: str, threshold_period: int, threshold: float, delta_oi: float, timestamp: int):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            INSERT INTO signals_temp (symbol, exchange, threshold_period, threshold, delta_oi, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (symbol, exchange, threshold_period, threshold, delta_oi, timestamp))
        await db.commit()


async def count_symbol_in_db(symbol: str, exchange: str, threshold_period: int, threshold: float) -> int:
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("""
            SELECT COUNT(*) FROM signals_temp
            WHERE symbol = ? AND exchange = ? AND threshold_period = ? AND threshold >= ?
        """, (symbol, exchange, threshold_period, threshold)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def trim_old_records(table_name: str, current_timestamp: int, days: int = 1):
    threshold_timestamp = (current_timestamp - days * 24 * 60 * 60) * 1000
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(f"DELETE FROM {table_name} WHERE  timestamp < ?", (threshold_timestamp,))
        await db.commit()


async def add_signal_in_total_db(symbol: str, exchange: str, timestamp: int, delta_oi: float,
                                 delta_price: float, delta_volume: float,
                                 threshold_period: int, threshold: float):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            INSERT INTO signals_total (symbol, exchange, timestamp, delta_oi, delta_price, delta_volume, threshold_period, threshold)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (symbol, exchange, timestamp, delta_oi, delta_price, delta_volume, threshold_period, threshold))
        await db.commit()


async def get_historical_oi(symbol: str, exchange: str, before_date: int) -> list[dict]:
    since_date = before_date + 24 * 60 * 60 *1000
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row  # strings will be returned as dictionaries
        async with db.execute("""
            SELECT * FROM history_temp
            WHERE symbol = ? AND exchange = ? AND timestamp <= ? AND timestamp >= ?
            ORDER BY timestamp DESC
        """, (symbol, exchange, before_date, since_date)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
