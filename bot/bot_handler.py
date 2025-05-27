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
from scanner_init import scanner_


dp = Dispatcher(storage=MemoryStorage())
bot = Bot(
    token=config.TG_BOT_API_KEY,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

user_settings = {}
DEFAULT_SETTINGS = {"period": 15, "threshold": 0.02}


@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Выберите действие:", reply_markup=main_menu)


@dp.callback_query(F.data == "set_period")
async def set_period(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите период роста (в минутах):")
    await state.set_state(ScreenerSettings.waiting_for_period)


@dp.message(ScreenerSettings.waiting_for_period)
async def process_period(message: Message, state: FSMContext):
    try:
        period = int(message.text)
        user_settings[message.from_user.id] = user_settings.get(message.from_user.id, {})
        user_settings[message.from_user.id]["period"] = period
        await message.answer(f"✅ Период установлен: {period} минут.")
        await state.clear()
    except ValueError:
        await message.answer("Ошибка. Введите целое число.")


@dp.callback_query(F.data == "set_threshold")
async def set_threshold(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите процент роста (например, 5 для 5%):")
    await state.set_state(ScreenerSettings.waiting_for_threshold)


@dp.message(ScreenerSettings.waiting_for_threshold)
async def process_threshold(message: Message, state: FSMContext):
    try:
        threshold = float(message.text) / 100
        user_settings[message.from_user.id] = user_settings.get(message.from_user.id, {})
        user_settings[message.from_user.id]["threshold"] = threshold
        await message.answer(f"✅ Процент установлен: {threshold * 100:.2f}%.")
        await state.clear()
    except ValueError:
        await message.answer("Ошибка. Введите число.")


@dp.callback_query(F.data == "start_scanner")
async def start_scan(callback: CallbackQuery):
    uid = callback.from_user.id
    settings = user_settings.get(uid, {}).copy()

    if "period" not in settings:
        settings["period"] = DEFAULT_SETTINGS["period"]
    if "threshold" not in settings:
        settings["threshold"] = DEFAULT_SETTINGS["threshold"]

    user_settings[uid] = settings

    async def notify(msg: str):
        await bot.send_message(chat_id=uid, text=msg)

    await callback.message.answer(
        f"🚀 Сканер запущен с настройками:\n"
        f"Период: {settings['period']} минут\n"
        f"Порог: {settings['threshold']*100:.2f}%"
    )
    asyncio.create_task(scanner_.run_scanner(notify, settings["period"], settings["threshold"]))


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    dp.run_polling(bot)
