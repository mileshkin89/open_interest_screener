import asyncio
from datetime import datetime
from exchange_listeners.binance_listener import BinanceListener
from cond_handler import ConditionHandler


signal_coin = None
cond = ConditionHandler()
client_binance = BinanceListener()


async def main():
    last_day = 0
    symbols = []

    while True:
        now = datetime.now().date()

        if now != last_day:
            symbols = await client_binance.fetch_usdt_symbols()
            last_day = now
            print("symbols = ", symbols)
            print("len(symbols) = ", len(symbols))

        flag = True
        signal_coins = await cond.is_signal(symbols, 15, "5m", 0.03)
        for coin in signal_coins:
            print(f"[{coin['exchange']}] {coin['datetime']} | {coin['symbol']}  за {coin['delta_time_minutes']} минут: изменение OI {coin['delta_oi_%']}, цены {coin['delta_price_%']} объема {coin['delta_volume_%']}")
            flag = False

        if flag:
            print("Сигнал отсутствует.")
        print("="*40)
        await asyncio.sleep(300)



if __name__ == "__main__":
    asyncio.run(main())