"""
keyboards.py

Defines inline keyboard layouts used in the Telegram bot interface.
These keyboards provide users with interactive buttons for navigation
and configuration of the scanner's settings.

Exports:
    - start_menu: Main menu with navigation to settings and exchanges, and option to run scanner.
    - settings_menu: Menu for adjusting scanner parameters like period and threshold.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


start_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Settings", callback_data="jump_settings"),
        InlineKeyboardButton(text="Exchanges", callback_data="jump_exchanges")],
        [InlineKeyboardButton(text="Run scanner by default", callback_data="start_scanner")],
        [InlineKeyboardButton(text="Stop scanner running", callback_data="stop_scanner")]
    ]
)

settings_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Period", callback_data="set_period"),
        InlineKeyboardButton(text="Threshold", callback_data="set_threshold")],
        [InlineKeyboardButton(text="Run scanner", callback_data="start_scanner")]
    ]
)
