"""
scanner.py

Module that defines the Scanner class, which periodically fetches market data from different
exchanges via listeners, checks for trading signals using given conditions, and triggers
notifications when such signals occur.

The scanner:
- Initializes database and trims outdated data.
- Fetches up-to-date USDT trading pairs for each exchange.
- Periodically checks conditions using a condition handler.
- Sends notifications through a callback when signals are found.

Classes:
    Scanner: Manages periodic market scanning and signal detection per user.

Requires:
    - Initialized `ListenerManager` and `ConditionHandler` instances.
    - Asynchronous environment for continuous execution.
"""

import asyncio
from datetime import datetime
from typing import Callable

from app_logic.condition_handler import ConditionHandler
from exchange_listeners.listener_manager import ListenerManager
from db.hist_signal_db import init_db, trim_old_records
from app_logic.default_settings import DEFAULT_SETTINGS, MIN_INTERVAL, SLEEP_TIMER_SECOND
from logging_config import get_logger

logger = get_logger(__name__)


class Scanner:
    """
    Class responsible for periodically scanning multiple exchanges for trading signals.

    Attributes:
        manager (ListenerManager): Manages access to exchange listeners.
        handler (ConditionHandler): Applies signal-checking logic to exchange data.
        last_day (date): The last date the daily operations were performed.
        symbols_by_exchange (dict[str, list[str]]): Maps exchange names to their trading symbols.
    """
    def __init__(self, manager: ListenerManager, handler: ConditionHandler):
        """
        Initializes the Scanner with exchange manager and signal handler.

        Args:
            manager (ListenerManager): Instance managing exchange listeners.
            handler (ConditionHandler): Logic handler to check if signal conditions are met.
        """
        self.manager = manager
        self.handler = handler
        self.last_day = None
        self.symbols_by_exchange: dict[str, list[str]] = {}


    async def run_scanner(self,
                          user_id,
                          notify_callback: Callable,
                          threshold_period: int = DEFAULT_SETTINGS["period"],
                          threshold: float = DEFAULT_SETTINGS["threshold"]):
        """
        Runs the scanner loop to detect signals and notify the user if any are found.

        This method:
            - Initializes the database on the first run.
            - Cleans up old signal data once per day.
            - Refreshes the list of symbols for each active exchange daily.
            - Every fixed interval (e.g., 5 minutes), checks for signals.
            - If signals are found, sends them via the notify_callback function.

        Args:
            user_id (int): Telegram user ID to whom the alerts will be sent.
            notify_callback (Callable): Async function used to send signal messages to the user.
            threshold_period (int, optional): Time period to measure open interest change. Defaults to config value.
            threshold (float, optional): Minimum open interest change (in percent) to trigger a signal. Defaults to config value.

        Raises:
            Exception: Logs errors if fetching data, cleaning DB, or processing conditions fails.
        """
        await init_db()
        while True:

            now = datetime.now().date()

            # Executed once a day:
            if now != self.last_day:
                self.symbols_by_exchange.clear()

                # Removing history older than a day
                now_timestamp = int(datetime.now().timestamp())
                try:
                    await trim_old_records("history_temp", now_timestamp)
                except Exception as e:
                    logger.error(f"Database cleanup error: {e}", exc_info=True)

                # Downloading the current list of cryptocurrencies
                for exchange in self.manager.get_all_active_listeners():
                    for name, listener in exchange.items():
                        try:
                            if name != None and listener != None:
                                symbols = await listener.fetch_usdt_symbols()
                                self.symbols_by_exchange[name] = symbols
                                logger.debug(f"{name.upper()} symbols: {len(symbols)}")
                        except Exception as e:
                            logger.error(f"Error receiving exchange {name}: {e}", exc_info=True)

                self.last_day = now

            # Executed every 5 minutes. Can be changed in SLEEP_TIMER_SECOND
            for exchange_name, symbols in self.symbols_by_exchange.items():
                listener = self.manager.get_listener(exchange_name)
                self.handler.set_client(listener)

                signal_coins = []

                # Getting a list of cryptocurrencies for which a condition is met on a specific exchange
                try:
                    signal_coins = await self.handler.is_signal(symbols, threshold_period, MIN_INTERVAL, threshold)
                except AttributeError as e:
                    logger.error(f"Error AttributeError: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"Error: {e}", exc_info=True)

                if signal_coins:
                    for coin in signal_coins:
                        # Sending a signal message
                        msg = (
                            f"🚨 [{coin['exchange']}]  {coin['datetime'].time()}" 
                            f"\n<b>{coin['symbol']}</b> in {coin['delta_time_minutes']} min: "
                            f"\nOI {coin['delta_oi_%']},  price {coin['delta_price_%']},  volume {coin['delta_volume_%']}"
                            f"\nNumber of signals per day: {coin['count_signal_24h']}"
                        )
                        logger.debug(f"{msg}")
                        await notify_callback(user_id, msg)
                else:
                    logger.debug(f"[{exchange_name.upper()}] No signal.")

            await asyncio.sleep(SLEEP_TIMER_SECOND)
