from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards import exchanges_menu
from db.bot_users import get_user_settings, update_user_settings


router = Router()


async def show_exchanges_menu(target):
    await target.answer(
        "🌐 Select the exchanges you want to monitor:\n\n"
        "Click on an exchange to enable or disable it.\n"
        "When you\'re ready, press 'Run scanner' to start with your current settings.",
        reply_markup=exchanges_menu
        )

@router.message(F.text == "/exchanges")
async def cmd_exchanges(message: Message, state: FSMContext):
    await show_exchanges_menu(message)


@router.callback_query(F.data.in_({"binance_on", "bybit_on"}))
async def toggle_exchange(callback: CallbackQuery):
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    active = set(settings["active_exchanges"])
    exchange = callback.data.split("_")[0]

    if exchange in active:
        active.remove(exchange)
        status = f"❌ Exchange {exchange.capitalize()} deactivated"
    else:
        active.add(exchange)
        status = f"✅ Exchange {exchange.capitalize()} activated"

    await update_user_settings(user_id, active_exchanges=list(active))
    await callback.answer(status, show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=generate_exchange_keyboard(active))


def generate_exchange_keyboard(active_exchanges: list[str]) -> InlineKeyboardMarkup:
    def button_text(name):
        return f"{'🟢' if name in active_exchanges else '🔴'} {name.capitalize()}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=button_text("binance"), callback_data="binance_on"),
                InlineKeyboardButton(text=button_text("bybit"), callback_data="bybit_on")
            ],
            [InlineKeyboardButton(text="▶️ Run scanner", callback_data="start_scanner")]
        ]
    )