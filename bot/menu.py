from aiogram.types import BotCommand, BotCommandScopeDefault
from bot.bot_init import bot

async def set_commands():
    commands = [BotCommand(command='start', description='Старт бот'),
                BotCommand(command='settings', description='Настройка параметров'),
                BotCommand(command='exchanges', description='Выбор бирж')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())