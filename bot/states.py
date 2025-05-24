# bot/states.py

from aiogram.fsm.state import StatesGroup, State

class ScreenerSettings(StatesGroup):
    waiting_for_period = State()
    waiting_for_threshold = State()