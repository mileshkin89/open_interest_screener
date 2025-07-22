# retention_worker.py

import asyncio
from psycopg_pool import AsyncConnectionPool

async def retention_worker(pool: AsyncConnectionPool):
    while True:
        try:
            async with pool.connection() as conn:
                await conn.execute("""
                    SELECT run_job(job_id)
                    FROM timescaledb_information.jobs
                    WHERE hypertable_name = 'history_data';
                """)
        except Exception as e:
            print(f"[retention_worker] Error: {e}")
        await asyncio.sleep(15 * 60)  # 15 min
