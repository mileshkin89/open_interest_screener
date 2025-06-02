import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import config
from bot.keyboards import exchanges_menu
from bot.states import ScreenerSettings
from db.bot_users import get_user_settings, update_user_settings  # init_db,
from app_logic import start_or_restart_scanner  #.scanner.scanner_manager


router = Router()


async def show_exchanges_menu(target):
    await target.answer("Select settings:", reply_markup=exchanges_menu)


@router.message(F.text == "/exchanges")
async def cmd_exchanges(message: Message, state: FSMContext):
    await show_exchanges_menu(message.message)

