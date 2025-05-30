# bot/bot_handler.py

import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import config
from bot.keyboards import main_menu
from bot.states import ScreenerSettings
from db.bot_users import init_db, get_user_settings, update_user_settings
from app_logic import start_or_restart_scanner  #.scanner.scanner_manager


dp = Dispatcher(storage=MemoryStorage())
bot = Bot(
    token=config.TG_BOT_API_KEY,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

DEFAULT_SETTINGS = {"period": 15, "threshold": 0.02}


@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Select action:", reply_markup=main_menu)


@dp.callback_query(F.data == "set_period")
async def set_period(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Enter the growth period from 5 to 30 (in minutes):")
    await state.set_state(ScreenerSettings.waiting_for_period)


@dp.message(ScreenerSettings.waiting_for_period)
async def process_period(message: Message, state: FSMContext):
    try:
        period = int(message.text)
        if not 5 <= period <= 30:
            raise ValueError("The period should be from 5 to 30 minutes")

        user_id = message.from_user.id

        existing = await get_user_settings(user_id)
        threshold = existing["threshold"] if existing else DEFAULT_SETTINGS["threshold"]

        await update_user_settings(user_id, period=period, threshold=threshold)

        await message.answer(f"✅ The period is set: {period} minutes.")
        await state.clear()

    except ValueError as e:
        await message.answer(str(e))


@dp.callback_query(F.data == "set_threshold")
async def set_threshold(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Enter the growth percentage (eg 5 for 5%):")
    await state.set_state(ScreenerSettings.waiting_for_threshold)


@dp.message(ScreenerSettings.waiting_for_threshold)
async def process_threshold(message: Message, state: FSMContext):
    try:
        threshold = float(message.text.replace(",", "."))
        if not 0.01 <= threshold <= 100:
            raise ValueError("The percentage must be between 0.01 and 100")
        threshold = threshold / 100

        user_id = message.from_user.id

        existing = await get_user_settings(user_id)
        period = existing["period"] if existing else DEFAULT_SETTINGS["period"]

        await update_user_settings(user_id, period=period, threshold=threshold)

        await message.answer(f"Growth threshold set: {threshold * 100:.2f}%")
        await state.clear()

    except ValueError as e:
        await message.answer(str(e))


@dp.callback_query(F.data == "start_scanner")
async def start_scan(callback: CallbackQuery):
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)

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

    status = await start_or_restart_scanner(user_id, settings, notify)

    if status == "already_running":
        await callback.message.answer(
            f"ℹ️ The scanner is already running with these settings:\n"
            f"Period: {settings['period']} minutes\n"
            f"Threshold: {settings['threshold'] * 100:.2f}%"
        )
    elif status == "started":
        await callback.message.answer(
            f"✅ The scanner has been launched with new settings:\n"
            f"Period: {settings['period']} minutes\n"
            f"Threshold: {settings['threshold'] * 100:.2f}%"
        )


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())
    dp.run_polling(bot)


