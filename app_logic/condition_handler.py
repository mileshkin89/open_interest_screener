# condition_handler.py

import asyncio
import aiohttp
import traceback
from datetime import datetime
from exchange_listeners.base_listener import BaseExchangeListener
from db.hist_signal_db import add_signal_in_db, count_symbol_in_db, add_signal_in_total_db, add_history_in_db, get_historical_oi

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

    def format_delta(self, value: float) -> str:
        return f"{value * 100:.2f}%"


    async def is_signal(self, symbols: list, threshold_period: int = 15, interval: str = "5", threshold: float = 0.05):
        self.symbols = symbols
        self.interval = interval
        self.threshold_period = threshold_period
        self.limit = int(self.threshold_period / AVAILABLE_INTERVAL[self.interval]) + 1
        self.threshold = threshold

        signal_coins = []

        print("threshold_period = ",  self.threshold_period)
        print(f"threshold = {self.threshold*100}%")

        # Download the OI data from exchange
        coins = await self.fetch_oi_data()

        for coin in coins:
            if isinstance(coin, Exception):
                print(f"Error while receiving data: {coin}")
                continue

            result = await self.process_coin_data(coin)
            if result:
                signal_coins.append(result)

        return signal_coins


    async def fetch_oi_data(self) -> list:
        _session = aiohttp.ClientSession()
        try:
            tasks = [
                self.client.fetch_oi(symbol.upper(), self.interval, self.limit, _session)
                for symbol in self.symbols
            ]
            coins = await asyncio.gather(*tasks, return_exceptions=True)
            return [coin for coin in coins if not isinstance(coin, Exception)]
        finally:
            await _session.close()


    async def process_coin_data(self, coin: list[dict]) -> dict | None:
        coin = self.sort_by_timestamp_reverse(coin)
        signal = {}

        for i in range(1, len(coin)):
            symbol = coin[0].get('symbol', 'unknown')
            exchange_name = coin[0].get('exchange', 'unknown')

            try:
                await add_history_in_db(symbol, exchange_name, coin[0]['timestamp'], coin[0]['open_interest'])
            except Exception as e:
                print(f"Error saving history to database: {e}")
                traceback.print_exc()

            delta_oi = self.delta_calculate(coin[0]['open_interest'], coin[i]['open_interest'])
            if delta_oi is None or delta_oi <= self.threshold:
                continue

            signal = await self.process_signal(coin, i, delta_oi, symbol, exchange_name)
            if signal:
                break

        return signal


    async def process_signal(self, coin: list[dict], i: int, delta_oi: float, symbol: str,
                             exchange_name: str) -> dict | None:
        start_date = coin[i]['timestamp']
        end_date = coin[0]['timestamp']

        _session = aiohttp.ClientSession()
        try:
            ohlcv = await self.client.fetch_ohlcv(symbol, start_date, end_date, str(self.interval), _session)
        except Exception as e:
            print(f"Error while getting OHLCV: {e}")
            traceback.print_exc()
            return None
        finally:
            await _session.close()

        if not ohlcv or len(ohlcv) < 2:
            return None

        ohlcv = self.sort_by_timestamp_reverse(ohlcv)

        delta_price = self.delta_calculate(ohlcv[0]['close'], ohlcv[i]['close'])
        delta_volume = self.delta_calculate(ohlcv[0]['volume'], ohlcv[i]['volume'])

        if delta_price is None or delta_volume is None:
            return None

        if not isinstance(coin[0]['datetime'], datetime) or not isinstance(coin[i]['datetime'], datetime):
            print("Incorrect datetime format")
            return None

        await add_signal_in_db(symbol, exchange_name, self.threshold_period, self.threshold, delta_oi, start_date)
        count_signal = await count_symbol_in_db(symbol, exchange_name, self.threshold_period, self.threshold)

        if count_signal == 1:
            _count_signal = 0
            try:
                _count_signal = await self.calculate_signal_from_history(symbol, exchange_name, int(start_date))
            except Exception as e:
                print(f"Error calculate signal from history: {e}")
                traceback.print_exc()
            if _count_signal != 0:
                count_signal = _count_signal

        await add_signal_in_total_db(
            symbol, exchange_name, start_date,
            delta_oi, delta_price, delta_volume,
            self.threshold_period, self.threshold
        )

        delta_time = coin[0]['datetime'] - coin[i]['datetime']
        delta_minutes = delta_time.total_seconds() / 60

        return {
            'exchange': exchange_name,
            'symbol': symbol,
            'timestamp': start_date,
            'datetime': coin[0]['datetime'],
            'delta_oi_%': self.format_delta(delta_oi),
            'delta_price_%': self.format_delta(delta_price),
            'delta_volume_%': self.format_delta(delta_volume),
            'delta_time_minutes': delta_minutes,
            'count_signal_24h': count_signal,
            'threshold_period': self.threshold_period,
            'threshold': self.threshold
        }


    async def calculate_signal_from_history(self, symbol: str, exchange_name: str, before_date: int):  #, threshold_period: int, threshold: float
        history_io = {}
        _count_signal = 0
        delta_oi = 0

        history_io = await get_historical_oi(symbol, exchange_name, before_date)
        if not history_io:
            return 0

        for i in range(len(history_io) - (self.limit - 1)):
            for j in range(1, self.limit):
                print("Вход перед условием")
                if history_io[i]['timestamp'] - history_io[i + j]['timestamp'] != j * AVAILABLE_INTERVAL[self.interval] * 60 * 1000:
                    print(history_io[i]['timestamp'] - history_io[i + j]['timestamp'])
                    print(j * AVAILABLE_INTERVAL[self.interval] * 60 * 1000)
                    continue
                print("После условия")

                delta_io = self.delta_calculate(history_io[i]['open_interest'], history_io[i + j]['open_interest'])

                if delta_oi is None or delta_oi <= self.threshold:
                    continue

                await add_signal_in_db(symbol, exchange_name, self.threshold_period, self.threshold, delta_oi, history_io[i + j]['timestamp'])

                _count_signal += 1

                break

        return _count_signal


