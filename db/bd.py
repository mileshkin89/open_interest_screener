# bd.py

import aiosqlite
from config import config


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
            WHERE symbol = ? AND exchange = ? AND threshold_period = ? AND threshold = ?
        """, (symbol, exchange, threshold_period, threshold)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def trim_signal_bd(current_timestamp: int):
    threshold = (current_timestamp - 24 * 60 * 60) * 1000  # 24 hours ago
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("DELETE FROM signals_temp WHERE timestamp < ?", (threshold,))
        await db.commit()


async def trim_history_bd(current_timestamp: int):
    threshold = (current_timestamp - 24 * 60 * 60) * 1000  # 24 hours ago
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("DELETE FROM history_temp WHERE timestamp < ?", (threshold,))
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
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row  # strings will be returned as dictionaries
        async with db.execute("""
            SELECT * FROM history_temp
            WHERE symbol = ? AND exchange = ? AND timestamp < ?
            ORDER BY timestamp ASC
        """, (symbol, exchange, before_date)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
