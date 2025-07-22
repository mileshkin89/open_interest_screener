# retention_worker.py

import asyncio
from psycopg_pool import AsyncConnectionPool

async def retention_worker(pool: AsyncConnectionPool):
    while True:
        try:
            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        SELECT job_id
                        FROM timescaledb_information.jobs
                        WHERE hypertable_name = 'history_data'
                        LIMIT 1
                    """)
                    row = await cur.fetchone()
                    if row:
                        job_id = row[0]
                        await cur.execute("CALL run_job(%s)", (job_id,))
                    else:
                        print("[retention_worker] Warning: No job_id found for 'history_data'")
        except Exception as e:
            print(f"[retention_worker] Error: {e}")
        await asyncio.sleep(15 * 60)  # 15 min
