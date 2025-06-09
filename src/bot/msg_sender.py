import asyncio
from src.bot.bot_init import bot_
from aiogram.types import InlineKeyboardMarkup


async def notify(user_id: int, msg: str, reply_markup: InlineKeyboardMarkup = None):
    """
    Sends a message to the specified Telegram user.

    Args:
        user_id (int): The Telegram user ID to whom the message will be sent.
        msg (str): The message text to send.
        reply_markup (InlineKeyboardMarkup, optional): Optional inline keyboard to include with the message.

    Notes:
        A small delay (0.2 seconds) is added before sending the message
        to prevent hitting rate limits when sending many messages in sequence.
    """
    await asyncio.sleep(0.2)
    await bot_.send_message(chat_id=user_id, text=msg, reply_markup=reply_markup)


