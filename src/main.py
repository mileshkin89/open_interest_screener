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

from settings.default_settings import DEFAULT_EXCHANGES
from bot.bot_init import bot, dp
from bot.menu import set_commands
from bot.commands import start, settings, exchanges
from db.repo_factory import get_user_settings_repo, get_history_repo, get_signal_repo
from db.repositories.user_settings import UserSettingsRepository
from db.repositories.history_data import HistoryDataRepository
from db.repositories.signal import SignalRepository
from db.retention_worker import retention_worker
from app_logic import user_activity
from app_logic.user_activity import monitor_user_activity
from app_logic.symbol_list_handler import symbol_list
from data_collector.start_collector import start_collector_process
from settings.logging_config import get_logger

logger = get_logger(__name__)


async def main():

    user_repo: UserSettingsRepository = await get_user_settings_repo()
    history_repo: HistoryDataRepository = await get_history_repo()
    signal_repo: SignalRepository = await get_signal_repo()

    await user_repo.init_table()
    logger.info("Initialization 'user_settings' table complete.")
    await history_repo.init_table()
    logger.info("Initialization 'exchange_history_data' tables complete.")
    await signal_repo.init_table()
    logger.info("Initialization 'signals' tables complete.")


    try:
        await history_repo.enable_retention_policy()
        logger.info("Retention policy enabled for history data")
        await signal_repo.enable_retention_policy()
        logger.info("Retention policy enabled for signal table")
    except Exception as e:
        logger.warning(f"Retention policy might already exist or failed: {e}")

    asyncio.create_task(retention_worker())
    logger.info("Started delete old data from history.")


    asyncio.create_task(symbol_list.get_symbol_list())
    logger.info("Started update symbol list task.")

    # Start user activity monitor in the background (checks for inactive users)
    asyncio.create_task(monitor_user_activity())
    logger.info("Started user activity monitor task.")

    logger.info("Started data collectors:")
    for exchange in DEFAULT_EXCHANGES:
        start_collector_process(exchange)


    await set_commands()
    dp.include_router(start.router)
    dp.include_router(settings.router)
    dp.include_router(exchanges.router)
    dp.include_router(user_activity.router)
    logger.info("Started bot commands.")


    # Start polling the Telegram API
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started successfully.")
    await dp.start_polling(bot)



if __name__ == "__main__":
    logger.info("Bot started...")
    asyncio.run(main())

