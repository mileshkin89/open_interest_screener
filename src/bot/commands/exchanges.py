"""
exchange.py

Handlers and UI logic for managing user-selected exchanges in the Telegram bot.

Includes:
- `/exchanges` command to open the exchange selection menu.
- Callback handlers for enabling/disabling specific exchanges.
- Dynamic inline keyboard generation reflecting current user preferences.
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from src.app_logic.user_activity import mark_user_active
from src.db.bot_users import get_user_settings, update_user_settings
from src.bot.msg_sender import notify


router = Router()


async def show_exchanges_menu(target: Message | CallbackQuery):
    """
    Displays an inline keyboard allowing the user to enable or disable exchanges for scanning.

    This function retrieves the user's current exchange preferences from the database,
    marks the user as active, and sends a message with a keyboard for toggling exchange selections.

    Args:
        target (Message | CallbackQuery): The incoming Telegram message or callback query from the user.

    Behavior:
        - Marks the user as active (for activity tracking).
        - Retrieves current settings from storage.
        - Generates a keyboard with exchange toggle buttons.
        - Sends a message with instructions and the generated keyboard.
    """
    user_id = target.from_user.id
    mark_user_active(user_id)

    settings = await get_user_settings(user_id)

    active_exchanges = settings.get("active_exchanges", [])
    keyboard = generate_exchange_keyboard(active_exchanges)
    text = (
        "🌐 Select the exchanges you want to monitor:\n\n"
        "Click on an exchange to enable or disable it.\n"
        "When you\'re ready, press 'Run scanner' to start with your current settings."
    )
    await notify(user_id, text, keyboard)


@router.message(F.text == "/exchanges")
async def cmd_exchanges(message: Message):
    """
    Handler for the `/exchanges` command.

    Displays the exchange selection menu to the user.
    """
    await show_exchanges_menu(message)


@router.callback_query(F.data.in_({"binance_on", "bybit_on"}))
async def toggle_exchange(callback: CallbackQuery):
    """
    Toggles the activation status of a selected exchange.

    Updates the user's active exchange list and updates the inline keyboard.

    Args:
        callback (CallbackQuery): Callback data triggered when user clicks on an exchange button.
    """
    user_id = callback.from_user.id
    mark_user_active(user_id)
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
    """
    Creates an inline keyboard showing active/inactive status of available exchanges.

    Args:
        active_exchanges (list[str]): List of currently active exchanges for the user.

    Returns:
        InlineKeyboardMarkup: A keyboard with toggle buttons for each exchange and a 'Run scanner' button.
    """
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