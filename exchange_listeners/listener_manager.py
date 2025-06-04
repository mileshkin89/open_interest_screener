from exchange_listeners.binance_listener import BinanceListener
from exchange_listeners.bybit_listener import BybitListener
from typing import Any
from logging_config import get_logger

logger = get_logger(__name__)


class ListenerManager:
    def __init__(self, enabled_exchanges: list[str]):
        self.enabled_exchanges = [e.lower() for e in enabled_exchanges]
        self.exchange_map = {
            "binance": BinanceListener(),
            "bybit": BybitListener(),
        }

    def get_listener(self, exchange_name: str) -> Any | None:
        exchange_name = exchange_name.lower()
        try:
            if exchange_name in self.enabled_exchanges:
                return self.exchange_map[exchange_name]
            else:
                raise ValueError(f"Exchange '{exchange_name}' is not activated in ListenerManager.")
        except ValueError as e:
            logger.error(f"Exchange not available. {e}", exc_info=True)

    def get_all_active_listeners(self) -> list[dict]:
        return [{name: self.exchange_map[name]} for name in self.enabled_exchanges]

    def get_all_active_names(self) -> list[str]:
        return self.enabled_exchanges

    def get_all_listeners(self) -> dict:
        return self.exchange_map


