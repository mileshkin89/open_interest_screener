"""
bot_init.py

Initializes and configures the Telegram bot and dispatcher using the Aiogram framework.

This module sets up:
- `Dispatcher` with in-memory storage for managing FSM (Finite State Machine) state.
- `Bot` instance configured with API token and HTML parse mode for formatting messages.

Modules:
    - aiogram: Telegram bot framework.
    - config: Project configuration file that provides the Telegram Bot API key.

Exports:
    - dp (Dispatcher): The main dispatcher for registering and handling bot events and middleware.
    - bot (Bot): The Telegram bot instance used to send and receive messages.
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums.parse_mode import ParseMode
from config import config

# Dispatcher responsible for handling updates and storing FSM state in memory.
dp = Dispatcher(storage=MemoryStorage())

# Bot instance configured with token and default parse mode (HTML formatting for messages).
bot = Bot(
    token=config.TG_BOT_API_KEY,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)