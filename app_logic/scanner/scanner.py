# scanner.py

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
    def __init__(self, manager: ListenerManager, handler: ConditionHandler):
        self.manager = manager
        self.handler = handler
        self.last_day = None
        self.symbols_by_exchange: dict[str, list[str]] = {}


    async def run_scanner(self, user_id, notify_callback: Callable,
                          threshold_period: int = DEFAULT_SETTINGS["period"],
                          threshold: float = DEFAULT_SETTINGS["threshold"]):
        await init_db()
        while True:

            now = datetime.now().date()

            # Executed once a day:
            if now != self.last_day:
                self.symbols_by_exchange.clear()

                # Removing signals and history older than a day
                now_timestamp = int(datetime.now().timestamp())
                try:
                    await trim_old_records("signals_temp", now_timestamp)
                    await trim_old_records("history_temp", now_timestamp)
                    await trim_old_records("signals_total", now_timestamp, 7)
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
