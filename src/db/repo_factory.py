"""
repo_factory.py

This module provides a global factory for creating and accessing shared resources,
such as the PostgreSQL async connection pool and repository instances.

It implements lazy initialization for:
- `AsyncConnectionPool`: used to interact with the PostgreSQL database via psycopg_pool.
- `UserSettingsRepository`: used to perform queries on the `user_settings` table.

Usage example:
--------------
from db.repo_factory import create_pool, get_user_settings_repo, get_history_repo

async def some_function():
    pool = await create_pool()

async def handle_user_command(user_id: int):
    repo = await get_user_settings_repo()
    settings = await repo.get_user_settings(user_id)

 async def handle_data_command(data: list[dict]):
    repo = await get_history_repo()
    await repo.write_ohlcv(data)
"""

from typing import Optional
from psycopg_pool import AsyncConnectionPool

from settings.config import config
from db.repositories.user_settings import UserSettingsRepository
from db.repositories.history_data import HistoryDataRepository


_pool: Optional[AsyncConnectionPool] = None
_user_settings_repo: Optional[UserSettingsRepository] = None
_history_repo: Optional[HistoryDataRepository] = None


async def create_pool() -> AsyncConnectionPool:
    """
    Lazily creates and returns a shared AsyncConnectionPool instance.

    The pool is created only once and reused across the application. If already created but closed,
    it will be reopened.

    Returns:
        AsyncConnectionPool: A connected and ready-to-use async connection pool.

    Example:
        >>> from db.repo_factory import create_pool
        >>> async def some_function():
        ...     pool = await create_pool()
    """
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(config.DATABASE_URL)
        await _pool.open()
    if not _pool.open:
        await _pool.open()
    return _pool


async def get_user_settings_repo() -> UserSettingsRepository:
    """
    Lazily creates and returns a singleton instance of UserSettingsRepository.

    Ensures the repository is initialized with a valid connection pool, using `create_pool()` if necessary.

    Returns:
        UserSettingsRepository: An instance ready to perform database operations on user settings.

    Example:
        >>> from db.repo_factory import get_user_settings_repo
        >>> async def handle_user_command(user_id: int):
        ...     repo = await get_user_settings_repo()
        ...     settings = await repo.get_user_settings(user_id)
    """
    global _user_settings_repo
    if _user_settings_repo is None:
        pool = await create_pool()
        _user_settings_repo = UserSettingsRepository(pool)
    return _user_settings_repo


async def get_history_repo() -> HistoryDataRepository:
    """
    Lazily creates and returns a singleton instance of HistoryDataRepository.

    Ensures the repository is initialized with a valid connection pool, using `create_pool()` if necessary.

    Returns:
        HistoryDataRepository: An instance ready to perform database operations on historical data.

    Example:
        >>> from db.repo_factory import get_history_repo
        >>> async def collect_and_store(data: list[dict]):
        ...     repo = await get_history_repo()
        ...     await repo.write_ohlcv(data)
    """
    global _history_repo
    if _history_repo is None:
        pool = await create_pool()
        _history_repo = HistoryDataRepository(pool)
    return _history_repo