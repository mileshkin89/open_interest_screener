# bot/keyboards.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Период роста", callback_data="set_period")],
        [InlineKeyboardButton(text="Процент роста", callback_data="set_threshold")],
        [InlineKeyboardButton(text="Запустить сканер", callback_data="start_scanner")]
    ]
)