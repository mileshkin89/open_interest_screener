from aiogram.types import BotCommand, BotCommandScopeDefault
from bot.bot_init import bot

async def set_commands():
    commands = [BotCommand(command='start', description='Bot start menu'),
                BotCommand(command='settings', description='Setting options'),
                BotCommand(command='exchanges', description='Selection of exchanges')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())