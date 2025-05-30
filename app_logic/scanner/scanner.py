# scanner.py

import asyncio
from datetime import datetime
import traceback
from app_logic.condition_handler import ConditionHandler
from exchange_listeners.listener_manager import ListenerManager
from db.hist_signal_db import init_db, trim_signal_bd, trim_history_bd
from logging_config import get_logger

logger = get_logger(__name__)
#logger.exception(f"Unexpected error during conversion convert_text_to_file(): {e}")
#logger.warning(f"Invalid format selected convert_text_to_file(): {e}")

class Scanner:
    def __init__(self, manager: ListenerManager, handler: ConditionHandler):
        self.manager = manager
        self.handler = handler
        self.last_day = None
        self.symbols_by_exchange: dict[str, list[str]] = {}


    async def run_scanner(self, notify_callback, threshold_period: int = 15, threshold: float = 0.05):
        await init_db()
        while True:

            now = datetime.now().date()

            if now != self.last_day:
                self.symbols_by_exchange.clear()

                now_timestamp = int(datetime.now().timestamp())
                try:
                    await trim_signal_bd(now_timestamp)  # removing signals older than a day
                    await trim_history_bd(now_timestamp) # removing history older than a day
                except Exception as e:
                    print(f"Database cleanup error: {e}")
                    traceback.print_exc()

                # Downloading the current list of cryptocurrencies
                for exchange in self.manager.get_all_active_listeners():
                    for name, listener in exchange.items():
                        try:
                            if name != None and listener != None:
                                symbols = await listener.fetch_usdt_symbols()
                                self.symbols_by_exchange[name] = symbols
                                print(f"{name.upper()} symbols: {len(symbols)}")
                        except Exception as e:
                            print(f"Error receiving exchange {name}: {e}")
                            traceback.print_exc()

                self.last_day = now


            for exchange_name, symbols in self.symbols_by_exchange.items():
                listener = self.manager.get_listener(exchange_name)
                self.handler.set_client(listener)

                signal_coins = []

                # Getting a list of cryptocurrencies for which a condition is met on a specific exchange
                try:
                    signal_coins = await self.handler.is_signal(symbols, threshold_period, "5", threshold)
                except AttributeError as e:
                    print(f"Error AttributeError: {e}")
                    traceback.print_exc()
                except Exception as e:
                    print(f"Error: {e}")
                    traceback.print_exc()

                if signal_coins:
                    for coin in signal_coins:
                        # Sending a signal message
                        msg = (
                            f"🚨 [{coin['exchange']}]  {coin['datetime'].time()}" 
                            f"\n<b>{coin['symbol']}</b> in {coin['delta_time_minutes']} min: "
                            f"\nOI {coin['delta_oi_%']},  price {coin['delta_price_%']},  volume {coin['delta_volume_%']}"
                            f"\nNumber of signals per day: {coin['count_signal_24h']}"
                        )
                        print(msg)
                        await notify_callback(msg)
                else:
                    print(f"[{exchange_name.upper()}] No signal.")

            print("=" * 40)
            await asyncio.sleep(300)
