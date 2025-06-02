from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards import settings_menu
from bot.states import ScreenerSettings
from db.bot_users import get_user_settings, update_user_settings  # init_db,
from app_logic.default_settings import DEFAULT_SETTINGS


router = Router()


async def show_settings_menu(target):
    """Показывает меню настроек: либо в ответ на message, либо callback."""
    await target.answer(
        "⚙️ Please select the screener settings:\n\n"
        "⏱️ <b>Period</b> – how many minutes to check for growth (5–30 min)\n"
        "📈 <b>Threshold</b> – %growth needed to trigger a signal (0.01–100 % )\n"
        "▶️ <b>Run scanner</b> – start scanning using your current settings",
        reply_markup=settings_menu
    )


@router.message(F.text == "/settings")
async def cmd_settings(message: Message, state: FSMContext):
    await show_settings_menu(message.message)


@router.callback_query(F.data == "set_period")
async def set_period(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Enter the growth period from 5 to 30 (in minutes):")
    await state.set_state(ScreenerSettings.waiting_for_period)


@router.message(ScreenerSettings.waiting_for_period)
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


@router.callback_query(F.data == "set_threshold")
async def set_threshold(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Enter the growth percentage (eg 5 for 5%):")
    await state.set_state(ScreenerSettings.waiting_for_threshold)


@router.message(ScreenerSettings.waiting_for_threshold)
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