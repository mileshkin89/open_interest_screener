# connection.py

from typing import Optional
from psycopg_pool import AsyncConnectionPool
from config import config

_pool: Optional[AsyncConnectionPool] = None

def create_pool() -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(config.DATABASE_URL)
    return _pool

