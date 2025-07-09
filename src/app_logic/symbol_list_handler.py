"""
symbol_list_handler.py

This module handles the periodic fetching of available USDT trading pairs (symbols)
from all active exchanges using their respective listeners.

It initializes a manager for exchange listeners, retrieves updated symbol lists
at a defined time every minute, and stores them in memory for access by other components.
"""

import asyncio
from datetime import datetime
from app_logic.default_settings import DEFAULT_EXCHANGES, START_FETCH_SYMBOLS_SECOND, SLEEP_FETCH_SYMBOLS_SECOND
from exchange_listeners.listener_manager import ListenerManager
from logging_config import get_logger

logger = get_logger(__name__)


class SymbolListHandler:
    """
    A handler that periodically fetches and stores the list of tradable USDT symbols from all currently active exchanges.

    Attributes:
        symbols_by_exchange (dict[str, list[str]]):
            A mapping of exchange names to their current list of tradable USDT symbols.
        manager (ListenerManager):
            Manages exchange listeners for each supported exchange.
        first_time (bool):
            Ensures that symbol fetching happens immediately on first run.
    """
    def __init__(self):
        self.symbols_by_exchange: dict[str, list[str]] = {}
        self.manager = ListenerManager(enabled_exchanges=DEFAULT_EXCHANGES)
        self.first_time = True


    async def get_symbol_list(self):
        """
        Continuously checks the current time and triggers a symbol update
        once per minute at a defined second.

        Fetches USDT trading symbols from all active exchanges using their listener clients
        and stores the result in `symbols_by_exchange`. Handles and logs any errors encountered.

        The update runs:
            - Immediately on the first launch
            - At a precise second every minute (e.g., second 49)
            - With a cooldown defined by `SLEEP_FETCH_SYMBOLS_SECOND` to avoid rapid retries

        This coroutine is intended to run as a background task.
        """

        while True:

            seconds = datetime.now().second

            if seconds == START_FETCH_SYMBOLS_SECOND or seconds == START_FETCH_SYMBOLS_SECOND+1 or self.first_time:
                self.first_time = False

                for exchange in self.manager.get_all_active_listeners():
                    for name, listener in exchange.items():
                        try:
                            if name != None and listener != None:
                                symbols = await listener.fetch_usdt_symbols()
                                self.symbols_by_exchange[name] = symbols
                                logger.debug(f"{name.upper()} symbols: {len(symbols)}")
                        except Exception as e:
                            logger.error(f"Error receiving exchange {name}: {e}", exc_info=True)

                await asyncio.sleep(SLEEP_FETCH_SYMBOLS_SECOND)

            await asyncio.sleep(1)



symbol_list = SymbolListHandler()
"""
Singleton instance of SymbolListHandler used by other modules 
to access or manage the latest fetched symbol data.
"""
