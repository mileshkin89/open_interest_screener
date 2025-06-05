"""
condition_handler.py

This module defines the ConditionHandler class, which detects trading signals
based on open interest (OI), price, and volume changes across multiple crypto exchanges.

Core responsibilities:
- Calculate deltas of OI, price, and volume over a defined period.
- Fetch and analyze historical data to detect signal events.
- Interact with the database to store signals and historical records.

Classes:
    ConditionHandler: Main engine for detecting open interest–based signals.

Constants:
    AVAILABLE_INTERVAL: Maps interval strings (e.g. "5") to numeric minute values.

Requires:
    - BaseExchangeListener: Abstract class to unify data fetching from exchanges.
    - Database utilities (add_signal_in_db, etc.)
"""

import asyncio
import aiohttp
from datetime import datetime
from exchange_listeners.base_listener import BaseExchangeListener
from app_logic.default_settings import DEFAULT_SETTINGS, MIN_INTERVAL
from db.hist_signal_db import add_history_in_db, get_historical_oi
from logging_config import get_logger

logger = get_logger(__name__)

AVAILABLE_INTERVAL = {
    "5": 5,
    "15": 15,
    "30": 30
}

class ConditionHandler:
    """
    Handles signal detection logic based on open interest (OI), price, and volume deltas.

    Attributes:
        client (BaseExchangeListener): Exchange data client set by external controller.
        symbols (list): The list of symbols to scan.
        interval (str): Timeframe for fetching data (e.g., "5", "15").
        limit (int): Number of data points to fetch per symbol.
        threshold (float): OI change threshold to trigger a signal.
        threshold_period (int): Time range in minutes to evaluate signal criteria.
    """
    def __init__(self):
        self.client: BaseExchangeListener = None
        self.symbols = ""
        self.interval = ""
        self.limit = None
        self.threshold = None
        self.threshold_period: int = None


    def set_client(self, client: BaseExchangeListener):
        """
        Injects the exchange listener client into the handler.

        Args:
            client (BaseExchangeListener): A data-fetching interface implementation.
        """
        self.client = client

    def sort_by_timestamp(self, coin_list: list[dict]) -> list[dict]:
        """Sorts a list of coin data by ascending timestamp."""
        return sorted(coin_list, key=lambda x: x['timestamp'])

    def sort_by_timestamp_reverse(self, coin_list: list[dict]) -> list[dict]:
        """Sorts a list of coin data by descending timestamp (most recent first)."""
        return sorted(coin_list, key=lambda x: x['timestamp'], reverse=True)

    def delta_calculate(self, data_last, data_first) -> float:
        """
        Calculates relative change (delta) between two values.

        Args:
            data_last (float): Most recent value.
            data_first (float): Earlier value.

        Returns:
            float: Delta as a ratio. Returns None if `data_last` is 0.
        """
        if float(data_last) == 0:
            return None
        delta = (float(data_last) - float(data_first)) / float(data_last)
        return delta

    def format_delta(self, value: float) -> str:
        """
        Formats a float delta as a percentage string with two decimal places.

        Args:
            value (float): The delta value.

        Returns:
            str: Formatted string (e.g., "5.23%").
        """
        return f"{value * 100:.2f}%"


    async def is_signal(self,
                        symbols: list,
                        threshold_period: int = DEFAULT_SETTINGS["period"],
                        interval: str = MIN_INTERVAL,
                        threshold: float = DEFAULT_SETTINGS["threshold"]):
        """
        Main entry point to evaluate signals across given symbols.

        Args:
            symbols (list): List of trading symbols to evaluate.
            threshold_period (int): Time range in minutes to calculate deltas.
            interval (str): Timeframe for candles (e.g., "5").
            threshold (float): Required OI delta to trigger a signal.

        Returns:
            list[dict]: All symbols that triggered a signal.
        """

        self.symbols = symbols
        self.interval = interval
        self.threshold_period = threshold_period
        self.limit = int(self.threshold_period / AVAILABLE_INTERVAL[self.interval]) + 1
        self.threshold = threshold

        signal_coins = []

        # Download the OI data from exchange
        coins = await self.fetch_oi_data()

        for coin in coins:
            if isinstance(coin, Exception):
                logger.warning(f"Error while receiving data: {coin}")
                continue

            result = await self.process_coin_data(coin)
            if result:
                signal_coins.append(result)

        return signal_coins


    async def fetch_oi_data(self) -> list:
        """
        Downloads open interest (OI) data for all symbols concurrently.

        Returns:
            list: List of OI time series data for each symbol.
        """
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
        """
        Processes a single symbol's OI data and determines if a signal is present.

        Saves history to DB, calculates delta, and evaluates signal condition.

        Args:
            coin (list[dict]): OI data for a specific symbol.

        Returns:
            dict | None: Signal info if condition met, otherwise None.
        """
        if not coin:
            return None

        coin = self.sort_by_timestamp_reverse(coin)
        signal = {}
        symbol = coin[0].get('symbol', 'unknown')
        exchange_name = coin[0].get('exchange', 'unknown')

        try:
            await add_history_in_db(symbol, exchange_name, coin[0]['timestamp'], coin[0]['open_interest'])
        except Exception as e:
            logger.error(f"Error saving history to database: {e}", exc_info=True)

        for i in range(1, len(coin)):
            delta_oi = self.delta_calculate(coin[0]['open_interest'], coin[i]['open_interest'])
            if delta_oi is None or delta_oi <= self.threshold:
                continue

            signal = await self.process_signal(coin, i, delta_oi, symbol, exchange_name)
            if signal:
                break

        return signal


    async def process_signal(self, coin: list[dict], i: int, delta_oi: float, symbol: str,
                             exchange_name: str) -> dict | None:
        """
        Validates OI signal by checking correlated price and volume changes.

        Args:
            coin (list): OI time series for a symbol.
            i (int): Index of the "start" point in the time series.
            delta_oi (float): Precomputed OI change.
            symbol (str): Trading symbol (e.g., "BTCUSDT").
            exchange_name (str): Exchange name (e.g., "binance").

        Returns:
            dict | None: Signal metadata if criteria passed.
        """
        start_date = coin[i]['timestamp']
        end_date = coin[0]['timestamp']

        _session = aiohttp.ClientSession()
        try:
            ohlcv = await self.client.fetch_ohlcv(symbol, start_date, end_date, str(self.interval), _session)
        except Exception as e:
            logger.error(f"Error while getting OHLCV: {e}", exc_info=True)
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
            logger.warning("Incorrect datetime format")
            return None

        # Calculate the number of signals from history
        count_signal = 1
        try:
            count_signal += await self.calculate_signal_from_history(symbol, exchange_name, int(start_date))
        except Exception as e:
            logger.error(f"Error calculate signal from history: {e}", exc_info=True)


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


    async def calculate_signal_from_history(self, symbol: str, exchange_name: str, before_date: int):
        """
        Calculates how many signals would have triggered based on historical OI data.

        Args:
            symbol (str): Trading symbol.
            exchange_name (str): Exchange name.
            before_date (int): Timestamp to fetch data before.

        Returns:
            int: Count of matching historical signal events.
        """
        _count_signal = 0
        _delta_oi = 0

        history_io = await get_historical_oi(symbol, exchange_name, before_date)
        if not history_io:
            return 0

        for i in range(len(history_io) - (self.limit - 1)):
            for j in range(1, self.limit):
                # Check that the values in the time series are consistent
                if history_io[i]['timestamp'] - history_io[i + j]['timestamp'] != j * AVAILABLE_INTERVAL[self.interval] * 60 * 1000:
                    continue

                _delta_oi = self.delta_calculate(history_io[i]['open_interest'], history_io[i + j]['open_interest'])
                if _delta_oi is None or _delta_oi <= self.threshold:
                    continue

                _count_signal += 1
                break

        return _count_signal


