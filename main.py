import asyncio
import logging

from bot.bot_init import bot, dp
from bot.menu import set_commands
from db.bot_users import init_db
from bot.commands import start, settings, exchanges


async def main():
    dp.include_router(start.router)
    dp.include_router(settings.router)
    dp.include_router(exchanges.router)

    await set_commands()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())
    asyncio.run(main())

