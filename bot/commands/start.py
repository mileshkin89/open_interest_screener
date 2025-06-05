"""
start.py

This module defines the `/start` command and related handlers for the Telegram bot.

Main functionality:
- Presents the start menu with options to configure screener settings, select exchanges, or start the scanner.
- Allows quick access to settings and exchanges configuration via buttons.
- Launches the scanner using default or saved user settings.

Integrates with:
- User activity tracking
- Persistent user settings (from the database)
- Scanner lifecycle management
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from bot.keyboards import start_menu
from db.bot_users import get_user_settings, update_user_settings
from app_logic import start_or_restart_scanner
from app_logic.user_activity import mark_user_active
from app_logic.default_settings import DEFAULT_SETTINGS, DEFAULT_EXCHANGES
from bot.commands.settings import show_settings_menu
from bot.commands.exchanges import show_exchanges_menu
from bot. msg_sender import notify


router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    """
    Handles the `/start` command.

    Sends a welcome message with buttons to:
    - Configure screener settings
    - Choose exchanges
    - Start the scanner using saved or default settings

    Also marks the user as active.
    """
    await message.answer(
        "Welcome! Please choose what you want to do:\n\n"
        "🔧 <b>Settings</b> – set up screener time period and growth threshold\n"
        "🌐 <b>Exchanges</b> – choose which exchanges to monitor\n"
        "▶️ <b>Run scanner by default</b> – start scanning using default settings (15 min, 5%)"
        " or your current settings if set",
        reply_markup=start_menu
    )
    user_id = message.from_user.id
    mark_user_active(user_id)

@router.callback_query(F.data == "jump_settings")
async def jump_settings_menu(callback: CallbackQuery):
    """
    Handles the "Settings" button press from the start menu.

    Redirects the user to the screener settings configuration menu.
    """
    await callback.answer()
    await show_settings_menu(callback.message)


@router.callback_query(F.data == "jump_exchanges")
async def jump_exchanges_menu(callback: CallbackQuery):
    """
    Handles the "Exchanges" button press from the start menu.

    Redirects the user to the exchange selection menu.
    """
    await callback.answer()
    await show_exchanges_menu(callback.message)


@router.callback_query(F.data == "start_scanner")
async def start_scan(callback: CallbackQuery):
    """
    Handles the "Run scanner" button press from the start menu.

    Retrieves user settings (or uses defaults), then starts or restarts the screener scanner.
    Sends a confirmation message showing the scanner's configuration.

    Args:
        callback (CallbackQuery): The callback data triggered from inline button.
    """
    user_id = callback.from_user.id
    mark_user_active(user_id)

    settings = await get_user_settings(user_id)

    if settings is None:
        settings = DEFAULT_SETTINGS.copy()
        settings["active_exchanges"] = DEFAULT_EXCHANGES.copy()
        await update_user_settings(user_id, **settings)
    else:
        if "period" not in settings:
            settings["period"] = DEFAULT_SETTINGS["period"]
        if "threshold" not in settings:
            settings["threshold"] = DEFAULT_SETTINGS["threshold"]
        if "active_exchanges" not in settings:
            settings["active_exchanges"] = DEFAULT_EXCHANGES.copy()

    exchanges = settings["active_exchanges"]

    status = await start_or_restart_scanner(user_id, settings, exchanges, notify)

    exchanges_str = ", ".join(f"'{name.capitalize()}'" for name in exchanges)

    if status == "already_running":
        await callback.message.answer(
            f"ℹ️ The scanner is already running with these settings:\n\n"
            f"Period: {settings['period']} minutes\n"
            f"Threshold: {settings['threshold'] * 100:.2f}%\n"
            f"Active exchanges: {exchanges_str}"
        )
    elif status == "started":
        await callback.message.answer(
            f"✅ The scanner has been launched with new settings:\n\n"
            f"Period: {settings['period']} minutes\n"
            f"Threshold: {settings['threshold'] * 100:.2f}%\n"
            f"Active exchanges: {exchanges_str}"
        )
