# scanner.py

import asyncio
from datetime import datetime
import traceback
from cond_handler import ConditionHandler
from exchange_listeners.listener_manager import ListenerManager
from db.bd import init_db, trim_signal_bd, trim_history_bd


class Scanner:
    def __init__(self, manager: ListenerManager, handler: ConditionHandler):
        self.manager = manager
        self.handler = handler
        self.last_day = None
        self.symbols_by_exchange: dict[str, list[str]] = {}


    async def run_scanner(self, notify_callback, threshold_period: int = 15, threshold: float = 0.03):
        await init_db()
        while True:

            now = datetime.now().date()

            if now != self.last_day:
                self.symbols_by_exchange.clear()

                now_timestamp = int(datetime.now().timestamp())
                await trim_signal_bd(now_timestamp)  # Удаляем сигналы старше суток
                await trim_history_bd(now_timestamp) # Удаляем историю по OI старше суток

                for exchange in self.manager.get_all_active_listeners():
                    for name, listener in exchange.items():
                        # print("name = ", name)
                        # print("listener = ", listener)
                        try:
                            if name != None and listener != None:
                                symbols = await listener.fetch_usdt_symbols()
                                self.symbols_by_exchange[name] = symbols
                                print(f"{name.upper()} symbols: {len(symbols)}")
                        except Exception as e:
                            print(f"Ошибка при получении символов {name}: {e}")

                self.last_day = now

            for exchange_name, symbols in self.symbols_by_exchange.items():
                listener = self.manager.get_listener(exchange_name)
                self.handler.set_client(listener)

                signal_coins = []
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
                        msg = (
                            f"🚨 [{coin['exchange']}]  {coin['datetime'].time()}" 
                            f"\n<b>{coin['symbol']}</b> за {coin['delta_time_minutes']} мин: "
                            f"\nOI {coin['delta_oi_%']},  цена {coin['delta_price_%']},  объём {coin['delta_volume_%']}"
                            f"\nКоличество сигналов за сутки: {coin['count_signal_24h']}"
                        )
                        print(msg)
                        await notify_callback(msg)
                else:
                    print(f"[{exchange_name.upper()}] Сигнал отсутствует.")

            print("=" * 40)
            await asyncio.sleep(300)
