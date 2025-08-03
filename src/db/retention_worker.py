"""
retention_worker.py

This module provides a background task that manually triggers TimescaleDB
retention policies for all hypertables related to Open Interest (OI) and OHLCV
data, for each configured exchange.

It queries the `timescaledb_information.jobs` view to locate retention jobs
registered via `add_retention_policy(...)`, and calls `run_job(job_id)` for each.

This is useful when jobs are not scheduled automatically, or if you want more
control over when and how retention is applied (e.g., in a containerized app).

"""

import asyncio
from psycopg_pool import AsyncConnectionPool
from app_logic.default_settings import DEFAULT_EXCHANGES
from db.repo_factory import create_pool
from logging_config import get_logger

logger = get_logger(__name__)

TABLE_SUFFIXES = ["history_oi", "history_ohlcv"]


async def retention_worker():
    """
    Periodically runs TimescaleDB retention policies for all exchange hypertables.

    This function loops indefinitely, and every 15 minutes:
    - Iterates over all exchanges defined in DEFAULT_EXCHANGES
    - Looks for corresponding `*_history_oi` and `*_history_ohlcv` hypertables
    - Queries for associated job_id from `timescaledb_information.jobs`
    - Executes `CALL run_job(job_id)` if a job is found

    Logs:
        - Info when a job is successfully run
        - Warning when no job_id is found for a hypertable
        - Error if any unexpected exception occurs during the loop
    """
    pool: AsyncConnectionPool = await create_pool()

    while True:
        try:
            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    for exchange in DEFAULT_EXCHANGES:
                        for suffix in TABLE_SUFFIXES:
                            hypertable_name = f"{exchange}_{suffix}"

                            await cur.execute("""
                                SELECT job_id
                                FROM timescaledb_information.jobs
                                WHERE hypertable_name = %s
                                LIMIT 1
                            """, (hypertable_name,))
                            row = await cur.fetchone()

                            if row:
                                job_id = row[0]
                                await cur.execute("CALL run_job(%s)", (job_id,))
                                logger.info(f"[retention_worker] Ran job for {hypertable_name}")
                            else:
                                logger.warning(f"[retention_worker] Warning: No job_id found for '{hypertable_name}'")

        except Exception as e:
            logger.error(f"[retention_worker] Error: {e}")

        await asyncio.sleep(15 * 60)
