# scanner_init.py

from exchange_listeners.listener_manager import ListenerManager
from app_logic.condition_handler import ConditionHandler
from .scanner import Scanner  #app_logic

exchanges = ["binance","bybit"]     #

manager = ListenerManager(enabled_exchanges=exchanges)

cond = ConditionHandler()
scanner_ = Scanner(manager=manager, handler=cond)






