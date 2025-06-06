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
from src.bot.bot_init import bot, dp
from src.bot.menu import set_commands
from src.db.bot_users import init_db
from src.bot.commands import start, settings, exchanges
from src.app_logic.user_activity import monitor_user_activity
from src.app_logic import user_activity
from src.logging_config import get_logger

logger = get_logger(__name__)


async def main():
    """
    Main asynchronous function that initializes and starts the bot.

    - Initializes the SQLite database for storing user settings.
    - Sets bot commands for the Telegram interface.
    - Launches a background task to monitor inactive users.
    - Registers command handlers (routers) for user interaction.
    - Clears any pending updates and starts polling the Telegram API.
    """
    await init_db()
    await set_commands()

    # Start user activity monitor in the background (checks for inactive users)
    asyncio.create_task(monitor_user_activity())

    # Register command routers
    dp.include_router(start.router)
    dp.include_router(settings.router)
    dp.include_router(exchanges.router)
    dp.include_router(user_activity.router)

    # Start polling the Telegram API
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



if __name__ == "__main__":
    logger.info("Bot started successfully.")
    asyncio.run(main())

