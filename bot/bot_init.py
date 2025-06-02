from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums.parse_mode import ParseMode

from config import config


dp = Dispatcher(storage=MemoryStorage())
bot = Bot(
    token=config.TG_BOT_API_KEY,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)