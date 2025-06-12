"""
menu.py

This module defines the default slash commands for the Telegram bot
and registers them with the Telegram API.

Functions:
    - set_commands(): Asynchronously sets the list of bot commands
      (e.g. /start, /settings, /exchanges) with their descriptions
      visible in the Telegram chat interface.
"""

from aiogram.types import BotCommand, BotCommandScopeDefault
from src.bot.bot_init import bot_

async def set_commands():
    """
    Registers a predefined list of bot commands with descriptions.

    This function configures the commands that users see when typing `/` in the chat,
    such as:
        /start     - Bot start menu
        /stop      - Stopped active scanner
        /settings  - Setting options
        /exchanges - Selection of exchanges

    The commands are set globally for all users using the default command scope.
    """
    commands = [BotCommand(command='start', description='Bot start menu'),
                BotCommand(command='stop', description='Stopped active scanner'),
                BotCommand(command='settings', description='Setting options'),
                BotCommand(command='exchanges', description='Selection of exchanges')]
    await bot_.set_my_commands(commands, BotCommandScopeDefault())