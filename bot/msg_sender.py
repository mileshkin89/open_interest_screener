# bot.msg_sender

import asyncio
from bot.bot_init import bot
from aiogram.types import InlineKeyboardMarkup


async def notify(user_id: int, msg: str, reply_markup: InlineKeyboardMarkup = None):
    await asyncio.sleep(0.3)
    await bot.send_message(chat_id=user_id, text=msg, reply_markup=reply_markup)


