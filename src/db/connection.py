# connection.py

from typing import Optional
from psycopg_pool import AsyncConnectionPool
from config import config

_pool: Optional[AsyncConnectionPool] = None

async def create_pool() -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(config.DATABASE_URL)
        await _pool.open()
    if not _pool.open:
        await _pool.open()

    return _pool

# --usage--
# from db.connection import create_pool
# async def some_function():
#     pool = await create_pool()