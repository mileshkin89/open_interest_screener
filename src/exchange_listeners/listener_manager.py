"""
listener_manager.py

This module defines the `ListenerManager` class, which is responsible for managing
exchange listeners (e.g., Binance, Bybit). It provides functionality to retrieve
active listeners, all listeners, or specific ones based on the enabled exchanges.
"""

from src.exchange_listeners.binance_listener import BinanceListener
from src.exchange_listeners.bybit_listener import BybitListener
from typing import Any
from src.logging_config import get_logger

logger = get_logger(__name__)


class ListenerManager:
    """
    Manages listener instances for supported crypto exchanges.

    Stores mappings between exchange names and their corresponding listener classes,
    and provides methods to access them based on which exchanges are currently enabled.
    """

    def __init__(self, enabled_exchanges: list[str]):
        """
        Initializes the listener manager with a list of enabled exchanges.

        Args:
            enabled_exchanges (list[str]): List of exchange names to activate (e.g., ["binance", "bybit"]).
        """
        self.enabled_exchanges = [e.lower() for e in enabled_exchanges]
        self.exchange_map = {
            "binance": BinanceListener(),
            "bybit": BybitListener(),
        }

    def get_listener(self, exchange_name: str) -> Any | None:
        """
        Returns the listener instance for the given exchange, if it's enabled.

        Args:
        exchange_name (str): Name of the exchange (case-insensitive).

        Returns:
        Any | None: Listener instance if found and enabled, otherwise None.

        Logs an error if the requested exchange is not enabled.
        """
        exchange_name = exchange_name.lower()
        try:
            if exchange_name in self.enabled_exchanges:
                return self.exchange_map[exchange_name]
            else:
                raise ValueError(f"Exchange '{exchange_name}' is not activated in ListenerManager.")
        except ValueError as e:
            logger.error(f"Exchange not available. {e}", exc_info=True)

    def get_all_active_listeners(self) -> list[dict]:
        """
        Returns a list of dictionaries with names and listener instances for all enabled exchanges.

        Returns:
            list[dict]: List of dictionaries in the form [{"binance": BinanceListener}, ...].
        """
        return [{name: self.exchange_map[name]} for name in self.enabled_exchanges]


