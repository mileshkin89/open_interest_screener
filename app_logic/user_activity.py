# app_logic.user_activity.py

import asyncio
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.msg_sender import notify
from app_logic.default_settings import INACTIVITY_DAYS, WAITING_DAYS
from app_logic.scanner.scanner_manager import running_scanners

router = Router()

user_activity: dict[int, datetime] = {}
pending_confirmation: dict[int, datetime] = {}


def mark_user_active(user_id: int):
    user_activity[user_id] = datetime.now()
    pending_confirmation.pop(user_id, None)
    if user_id not in running_scanners:
        print(f"[INFO] User {user_id} marked active, but no scanner is running.")


async def send_confirmation_request(user_id: int, notify_func):
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


async def monitor_user_activity(notify_func):
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
                        print(f"[INFO] Scanner stopped for inactive user {user_id}.")
                        await notify(user_id, "❌ Scanner stopped.")
                    pending_confirmation.pop(user_id, None)
                    user_activity.pop(user_id, None)
                continue

            if (now - last_active).days >= INACTIVITY_DAYS:
                await send_confirmation_request(user_id, notify)
                pending_confirmation[user_id] = now

        await asyncio.sleep(86400)   #  1 day


@router.callback_query(F.data.startswith("confirm:"))
async def handle_confirm_button(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    mark_user_active(user_id)
    await callback.answer()
    await notify(user_id, "✅ Activity confirmed. The scanner will continue running.")
