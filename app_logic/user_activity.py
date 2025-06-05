"""
user_activity.py

This module tracks user activity to manage scanner lifecycle for inactive users.

Main responsibilities:
- Track last active timestamps per user.
- Send confirmation requests after a period of inactivity.
- Reactivate the user upon confirmation via Telegram button.
- Stop the scanner if the user remains inactive.

Requires:
    - notify() to send messages via Telegram
    - running_scanners: currently active scanner tasks
    - aiogram router for callback handling
"""

import asyncio
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.msg_sender import notify
from app_logic.default_settings import INACTIVITY_DAYS, WAITING_DAYS
from app_logic.scanner.scanner_manager import running_scanners
from logging_config import get_logger

logger = get_logger(__name__)

router = Router()

user_activity: dict[int, datetime] = {}
"""
Tracks last known activity timestamp per user.
Used to determine inactivity duration.
"""
pending_confirmation: dict[int, datetime] = {}
"""
Tracks when a confirmation message was sent to each user.
Used to wait a few more days before shutting down the scanner.
"""

def mark_user_active(user_id: int):
    """
    Updates a user's last activity timestamp and cancels any pending inactivity warnings.

    Args:
        user_id (int): Telegram user ID.
    """
    user_activity[user_id] = datetime.now()
    pending_confirmation.pop(user_id, None)

    if user_id not in running_scanners:
        logger.debug(f"User {user_id} marked active, but no scanner is running.")


async def send_confirmation_request(user_id: int):
    """
    Sends a message with a confirmation button to the user to verify if they still want to keep the scanner running.

    Args:
        user_id (int): Telegram user ID to notify.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❓ Сonfirm", callback_data=f"confirm:{user_id}")]
        ]
    )
    await notify(
        user_id=user_id,
        msg = "❗️ It looks like you haven't used the scanner for a few days.\n"
              "If you still need it, press the button below — otherwise, it will be stopped.",
        reply_markup=keyboard
    )


async def monitor_user_activity():
    """
    Background coroutine that runs daily to check for user inactivity.

    - If a user has been inactive for INACTIVITY_DAYS, sends a confirmation button.
    - If the user ignores it for WAITING_DAYS, the scanner is stopped automatically.

    This loop runs forever with a 1-day delay between checks.
    """
    while True:

        now = datetime.now()

        for user_id, last_active in list(user_activity.items()):
            if user_id in pending_confirmation:
                # Already waiting for confirmation
                if (now - pending_confirmation[user_id]).days >= WAITING_DAYS:
                    # No response - turn off the scanner
                    running = running_scanners.get(user_id)

                    if running:
                        running["task"].cancel()
                        try:
                            await running["task"]
                        except asyncio.CancelledError:
                            pass

                        running_scanners.pop(user_id, None)
                        await notify(user_id, "❌ Scanner stopped.")
                        logger.info(f"Scanner stopped for inactive user {user_id}.")

                    pending_confirmation.pop(user_id, None)
                    user_activity.pop(user_id, None)

                continue

            if (now - last_active).days >= INACTIVITY_DAYS:
                await send_confirmation_request(user_id)
                pending_confirmation[user_id] = now

        await asyncio.sleep(86400)   #  1 day


@router.callback_query(F.data.startswith("confirm:"))
async def handle_confirm_button(callback: CallbackQuery):
    """
    Handles the 'Confirm' button press from a user.

    - Marks the user as active.
    - Cancels pending shutdown.
    - Sends confirmation message via Telegram.

    Args:
        callback (CallbackQuery): Telegram callback query object.
    """
    user_id = int(callback.data.split(":")[1])
    mark_user_active(user_id)

    await callback.answer()
    await notify(user_id, "✅ Activity confirmed. The scanner will continue running.")
    logger.info(f"Activity confirmed for user {user_id}")
