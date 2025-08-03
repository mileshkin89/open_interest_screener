"""
main.py

Entry point of the Telegram bot application.

This module:
- Initializes the database.
- Sets up Telegram bot commands.
- Starts the user activity monitor.
- Registers all command routers.
- Starts the bot polling loop.

Designed for asynchronous execution using asyncio.
"""
import asyncio

from app_logic.default_settings import DEFAULT_EXCHANGES
from bot.bot_init import bot_, dp
from bot.menu import set_commands
from db.repo_factory import create_pool, get_user_settings_repo
from db.repositories.user_settings import UserSettingsRepository
from db.repositories.history_data import init_timescale_table, enable_retention_policy
from db.retention_worker import retention_worker
from app_logic.user_activity import monitor_user_activity
from app_logic.symbol_list_handler import symbol_list
from data_collector.start_collector import start_collector_process
from logging_config import get_logger

logger = get_logger(__name__)


async def main():

    pool = await create_pool()
    user_repo: UserSettingsRepository = await get_user_settings_repo()

    await user_repo.init_table()
    logger.info("Initialization 'user_settings' table complete.")
    await init_timescale_table(pool)
    logger.info("Initialization 'history_data' table complete.")


    try:
        await enable_retention_policy(pool)
        logger.info("Retention policy enabled for 'history_data'")
    except Exception as e:
        logger.warning(f"Retention policy might already exist or failed: {e}")

    asyncio.create_task(retention_worker(pool))
    logger.info("Started delete old data from 'history_data' table.")


    asyncio.create_task(symbol_list.get_symbol_list())
    logger.info("Started update symbol list task.")

    # Start user activity monitor in the background (checks for inactive users)
    asyncio.create_task(monitor_user_activity())
    logger.info("Started user activity monitor task.")

    for exchange in DEFAULT_EXCHANGES:
        start_collector_process(exchange)


    await set_commands()
    # dp.include_router(start.router)
    # dp.include_router(settings.router)
    # dp.include_router(exchanges.router)
    # dp.include_router(user_activity.router)
    # logger.info("Started bot commands.")


    # Start polling the Telegram API
    await bot_.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started successfully.")
    await dp.start_polling(bot_)



if __name__ == "__main__":
    logger.info("Bot started...")
    asyncio.run(main())

