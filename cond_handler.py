# cond_handler.py

import asyncio
from datetime import datetime
from exchange_listeners.base_listener import BaseExchangeListener
from db.bd import add_signal_in_db, count_symbol_in_db, add_signal_in_total_db

AVAILABLE_INTERVAL = {
    "5": 5,
    "15": 15,
    "30": 30
}

class ConditionHandler:
    def __init__(self):
        self.client: BaseExchangeListener = None
        self.symbols = ""
        self.interval = ""
        self.limit = None
        self.threshold = None
        self.threshold_period: int = None


    def set_client(self, client: BaseExchangeListener):
        self.client = client

    def sort_by_timestamp(self, coin_list: list[dict]) -> list[dict]:
        return sorted(coin_list, key=lambda x: x['timestamp'])

    def sort_by_timestamp_reverse(self, coin_list: list[dict]) -> list[dict]:
        return sorted(coin_list, key=lambda x: x['timestamp'], reverse=True)

    def delta_calculate(self, data_last, data_first) -> float:
        if float(data_last) == 0:
            return None
        delta = (float(data_last) - float(data_first)) / float(data_last)
        return delta


    async def is_signal(self, symbols: list, threshold_period: int = 15, interval: str = "5", threshold: float = 0.05):
        self.symbols = symbols
        self.interval = interval
        self.threshold_period = threshold_period
        self.limit = int(self.threshold_period / AVAILABLE_INTERVAL[self.interval]) + 1
        self.threshold = threshold
        start_date: int = None          # the latest data
        end_date: int = None            # the oldest data
        signal_coins = []


        print("threshold_period = ",  self.threshold_period)
        print(f"threshold = {self.threshold*100}%")

        # Download the OI data from exchange
        tasks = [self.client.fetch_oi(symbol.upper(), self.interval, self.limit) for symbol in self.symbols]
        coins = await asyncio.gather(*tasks, return_exceptions=True)

        for coin in coins:
            if isinstance(coin, Exception):
                print(f"Error while receiving data: {coin}")
                continue

            coin = self.sort_by_timestamp_reverse(coin)

            for i in range(1,len(coin)):
                exchange_name = coin[0]['exchange']
                symbol = coin[0]['symbol']

                # Finding the OI change
                delta_oi = self.delta_calculate(coin[0]['open_interest'], coin[i]['open_interest'])
                if delta_oi is None:
                    continue
                formatted_delta_oi = f"{delta_oi*100:.2f}%"

                # Comparison of OI change with threshold value
                if delta_oi > self.threshold:

                    count_signal = 0                     # number of signals in the last 24 hours
                    start_date = coin[i]['timestamp']    # the latest data
                    end_date = coin[0]['timestamp']      # the oldest data


                    # Downloading historical data on price and volume for the period where the OI condition was met
                    try:
                        signal_coin_price_volume = await self.client.fetch_ohlcv(coin[0]['symbol'], start_date, end_date, str(self.interval))
                    except Exception as e:
                        print(f"Error while getting OHLCV: {e}")
                        continue

                    # If the data is empty or an error occurs, skip the iteration
                    if not signal_coin_price_volume or len(signal_coin_price_volume) < 2:
                        continue

                    signal_coin_price_volume = self.sort_by_timestamp_reverse(signal_coin_price_volume)


                    # Adding signal data to the DB
                    await add_signal_in_db(symbol, exchange_name, self.threshold_period, self.threshold, delta_oi, start_date)
                    # Counting the number of signals for this symbol in the DB
                    # Correct value of 'count_signal' if the screener works for more than a day without interruption
                    count_signal = await count_symbol_in_db(symbol, exchange_name, self.threshold_period, self.threshold)

                    delta_price = self.delta_calculate(signal_coin_price_volume[0]['close'], signal_coin_price_volume[i]['close'])
                    delta_volume = self.delta_calculate(signal_coin_price_volume[0]['volume'], signal_coin_price_volume[i]['volume'])
                    if delta_price is None or delta_volume is None:
                        continue
                    formatted_delta_price = f"{delta_price * 100:.2f}%"
                    formatted_delta_volume = f"{delta_volume * 100:.2f}%"

                    if not isinstance(coin[0]['datetime'], datetime) or not isinstance(coin[i]['datetime'], datetime):
                        print("Incorrect datetime format")
                        continue
                    delta_time = coin[0]['datetime'] - coin[i]['datetime']
                    delta_minutes = delta_time.total_seconds() / 60

                    # generation of output data for a specific signal
                    is_signal_coin = {
                        'exchange': exchange_name,
                        'symbol': symbol,
                        'timestamp': start_date,
                        'datetime': coin[i]['datetime'],
                        'delta_oi_%': formatted_delta_oi,
                        'delta_price_%': formatted_delta_price,
                        'delta_volume_%': formatted_delta_volume,
                        'delta_time_minutes': delta_minutes,
                        'count_signal_24h': count_signal,
                        'threshold_period': self.threshold_period,
                        'threshold': self.threshold
                    }

                    # Adding a signal record to the long-term database
                    await add_signal_in_total_db(symbol, exchange_name, start_date, delta_oi,
                                                     delta_price, delta_volume,
                                                     self.threshold_period, self.threshold)

                    signal_coins.append(is_signal_coin)
                    break

        return signal_coins



