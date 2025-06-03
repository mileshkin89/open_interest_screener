import asyncio
import logging

from bot.bot_init import bot, dp
from bot.menu import set_commands
from db.bot_users import init_db
from bot.commands import start, settings, exchanges
from app_logic.user_activity import monitor_user_activity
from app_logic import user_activity
from bot.msg_sender import notify


async def main():
    await init_db()
    await set_commands()

    asyncio.create_task(monitor_user_activity(notify))

    dp.include_router(start.router)
    dp.include_router(settings.router)
    dp.include_router(exchanges.router)
    dp.include_router(user_activity.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

