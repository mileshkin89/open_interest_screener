import asyncio
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards import start_menu
from db.bot_users import get_user_settings, update_user_settings
from app_logic import start_or_restart_scanner
from app_logic.default_settings import DEFAULT_SETTINGS
from bot.bot_init import bot
from bot.commands.settings import show_settings_menu
from bot.commands.exchanges import show_exchanges_menu

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        "Welcome! Please choose what you want to do:\n\n"
        "🔧 <b>Settings</b> – set up screener time period and growth threshold\n"
        "🌐 <b>Exchanges</b> – choose which exchanges to monitor\n"
        "▶️ <b>Run scanner by default</b> – start scanning using default settings (15 min, 5%)"
        " or your current settings if set",
        reply_markup=start_menu
    )

@router.callback_query(F.data == "jump_settings")
async def jump_settings_menu(callback: CallbackQuery):
    await callback.answer()
    await show_settings_menu(callback.message)


@router.callback_query(F.data == "jump_exchanges")
async def jump_exchanges_menu(callback: CallbackQuery):
    await callback.answer()
    await show_exchanges_menu(callback.message)


@router.callback_query(F.data == "start_scanner")
async def start_scan(callback: CallbackQuery):
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    exchanges = settings["active_exchanges"]

    if settings is None:
        settings = DEFAULT_SETTINGS.copy()
        await update_user_settings(user_id, **settings)
    else:
        if "period" not in settings:
            settings["period"] = DEFAULT_SETTINGS["period"]
        if "threshold" not in settings:
            settings["threshold"] = DEFAULT_SETTINGS["threshold"]

    async def notify(msg: str):
        await asyncio.sleep(0.3)
        await bot.send_message(chat_id=user_id, text=msg)

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