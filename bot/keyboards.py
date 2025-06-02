# bot/keyboards.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


start_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Settings", callback_data="jump_settings"),
        InlineKeyboardButton(text="Exchanges", callback_data="jump_exchanges")],
        [InlineKeyboardButton(text="Run scanner by default", callback_data="start_scanner")]
    ]
)

settings_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Period", callback_data="set_period"),
        InlineKeyboardButton(text="Threshold", callback_data="set_threshold")],
        [InlineKeyboardButton(text="Run scanner", callback_data="start_scanner")]
    ]
)

exchanges_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Binance", callback_data="binance_on"),
        InlineKeyboardButton(text="🟢 Bybit", callback_data="bybit_on")],
        [InlineKeyboardButton(text="Run scanner", callback_data="start_scanner")]
    ]
)
