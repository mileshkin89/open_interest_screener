# scanner_init.py

from exchange_listeners.listener_manager import ListenerManager
from cond_handler import ConditionHandler
from scanner import Scanner

exchanges = ["binance","bybit"]  # ,"bybit"

manager = ListenerManager(enabled_exchanges=exchanges)

cond = ConditionHandler()
scanner_ = Scanner(manager=manager, handler=cond)






