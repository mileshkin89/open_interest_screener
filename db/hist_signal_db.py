"""
hist_signal_db.py

Provides functionality to manage historical open interest data in a temporary SQLite database.
Includes operations for initialization, insertion, cleanup, and retrieval of historical data.

Functions:
    init_db(): Initializes the database and creates the 'history_temp' table with appropriate indexes.
    trim_old_records(table_name, current_timestamp, days): Deletes outdated records older than a specified number of days.
    add_history_in_db(symbol, exchange, timestamp, open_interest): Inserts a new open interest record into the database.
    get_historical_oi(symbol, exchange, before_date): Retrieves open interest records for the past 24 hours for a given symbol and exchange.
"""

import aiosqlite
from config import config

config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)


async def init_db():
    """
    Initializes the SQLite database and creates the 'history_temp' table if it doesn't exist.
    Also creates necessary indexes for performance optimization.
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
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
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON history_temp (timestamp)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol_exchange_time
            ON history_temp(symbol, exchange, timestamp)
        """)
        await db.commit()


async def trim_old_records(table_name: str, current_timestamp: int, days: int = 1):
    """
    Deletes records older than the specified number of days from the given table.

    Args:
        table_name (str): Name of the table to clean up.
        current_timestamp (int): Current timestamp in milliseconds.
        days (int, optional): Number of days to retain. Defaults to 1.
    """
    threshold_timestamp = (current_timestamp - days * 24 * 60 * 60) * 1000
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(f"DELETE FROM {table_name} WHERE  timestamp < ?", (threshold_timestamp,))
        await db.commit()


async def add_history_in_db(symbol: str, exchange: str, timestamp: int, open_interest: float):
    """
    Inserts a new record of open interest data into the 'history_temp' table.

    Args:
        symbol (str): Trading symbol (e.g. BTCUSDT).
        exchange (str): Exchange name (e.g. Binance, Bybit).
        timestamp (int): Timestamp in milliseconds.
        open_interest (float): Value of open interest.
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            INSERT INTO  history_temp (symbol, exchange, timestamp, open_interest)
            VALUES (?, ?, ?, ?)
        """, (symbol, exchange, timestamp, open_interest))
        await db.commit()


async def get_historical_oi(symbol: str, exchange: str, before_date: int) -> list[dict]:
    """
    Retrieves open interest history for a specific symbol and exchange within 24 hours before the given timestamp.

    Args:
        symbol (str): Trading symbol.
        exchange (str): Exchange name.
        before_date (int): Upper bound timestamp in milliseconds.

    Returns:
        list[dict]: List of historical open interest records as dictionaries, ordered by timestamp descending.
    """
    since_date = before_date - 24 * 60 * 60 *1000
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row  # strings will be returned as dictionaries
        async with db.execute("""
            SELECT * FROM history_temp
            WHERE symbol = ? AND exchange = ? AND timestamp <= ? AND timestamp >= ?
            ORDER BY timestamp DESC
        """, (symbol, exchange, before_date, since_date)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

