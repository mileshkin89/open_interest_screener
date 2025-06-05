"""
states.py

Defines the FSM (Finite State Machine) states used in the Telegram bot
to guide the user through configuration steps for the screener.

Classes:
    ScreenerSettings: FSM states for receiving user input related to scanner settings.
"""

from aiogram.fsm.state import StatesGroup, State

class ScreenerSettings(StatesGroup):
    """
    States for configuring the screener's parameters.

    Attributes:
        waiting_for_period (State): Bot is waiting for the user to enter the time period in minutes.
        waiting_for_threshold (State): Bot is waiting for the user to enter the growth threshold in percent.
    """
    waiting_for_period = State()
    waiting_for_threshold = State()