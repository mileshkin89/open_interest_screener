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

from datetime import datetime
from exchange_listeners.api_listeners.base_listener import BaseExchangeListener
from settings.default_settings import DEFAULT_SETTINGS
from db.repo_factory import get_history_repo, get_signal_repo
from db.repositories.history_data import HistoryDataRepository
from db.repositories.signal import SignalRepository
from settings.logging_config import get_logger

logger = get_logger(__name__)


class ConditionHandler:
    """
    Handles signal detection logic based on open interest (OI), price, and volume deltas.

    Attributes:
        client (BaseExchangeListener): Exchange data client set by external controller.
        symbols (list): The list of symbols to scan.
        threshold (float): OI change threshold to trigger a signal.
        threshold_period (int): Time range in minutes to evaluate signal criteria.
    """
    def __init__(self):
        self.client: BaseExchangeListener = None
        self.symbols = ""
        self.threshold = None
        self.threshold_period: int = None


    def set_client(self, client: BaseExchangeListener):
        """
        Injects the exchange listener client into the handler.

        Args:
            client (BaseExchangeListener): A data-fetching interface implementation.
        """
        self.client = client

    def delta_calculate(self, data_last: float, data_first: float) -> float | None:

        """
            Calculates relative change (delta) between two values.

            Args:
                data_last (float): Most recent value.
                data_first (float): Earlier value.

            Returns:
                float: Delta as a ratio. Returns None if `data_last` is 0.
            """
        if not data_last or not data_first:
            return None
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

    def get_time_now(self) -> int:
        return datetime.utcnow()


    async def is_signal(self,
                        exchange_name: str,
                        symbols: list,
                        threshold_period: int = DEFAULT_SETTINGS["period"],
                        threshold: float = DEFAULT_SETTINGS["threshold"]):

        self.symbols = symbols
        self.threshold_period = threshold_period
        self.threshold = threshold

        signal_coins = []
        history_repo: HistoryDataRepository = await get_history_repo()

        for symbol in symbols:

            coin_data = await history_repo.get_oi_by_period(exchange_name, symbol, self.get_time_now(), self.threshold_period)

            result = await self.process_coin_data(coin_data, exchange_name)
            if result:
                signal_coins.append(result)

        return signal_coins


    async def process_coin_data(self, coin: list[dict], exchange_name: str) -> dict | None:

        if not coin or not exchange_name or len(coin) < 2:
            return None

        signal = {}
        symbol = coin[0].get('symbol', 'unknown')

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

        start_time = coin[i].get('timestamp', None)
        end_time = coin[0].get('timestamp', None)

        if not start_time or not end_time:
            return None

        delta_time = end_time - start_time
        delta_minutes = int(delta_time.total_seconds() / 60)


        history_repo: HistoryDataRepository = await get_history_repo()
        ohlcv = await history_repo.get_ohlcv_by_period(exchange_name, symbol, end_time, start_time)

        if not ohlcv or len(ohlcv) < 2:
            return None

        delta_price = self.delta_calculate(ohlcv[0]['close'], ohlcv[i]['close'])
        delta_volume = self.delta_calculate(ohlcv[0]['volume'], ohlcv[i]['volume'])

        if delta_price is None or delta_volume is None:
            return None

        count_signal = await self.count_signals(exchange_name, symbol, start_time, delta_minutes, delta_oi)

        return {
            'exchange': exchange_name,
            'symbol': symbol.strip(),
            'timestamp': start_time,
            'datetime': end_time,
            'delta_oi_%': self.format_delta(delta_oi),
            'delta_price_%': self.format_delta(delta_price),
            'delta_volume_%': self.format_delta(delta_volume),
            'delta_time_minutes': delta_minutes,
            'count_signal_24h': count_signal,
            'threshold_period': self.threshold_period,
            'threshold': self.threshold
        }


    async def count_signals(self, exchange: str, symbol: str, start_time: int, delta_minutes: int, delta_oi: float) -> int:

        signal_repo: SignalRepository = await get_signal_repo()
        history_repo: HistoryDataRepository = await get_history_repo()

        await signal_repo.write_signal(exchange, symbol, start_time, delta_oi, delta_minutes)

        count_signal = await signal_repo.count_signals(exchange, symbol, delta_minutes, self.threshold)

        if count_signal > 1:
            return count_signal


        history_io = await history_repo.get_oi_by_period(exchange, symbol, self.get_time_now())
        if not history_io:
            return 0

        for i in range(len(history_io)):
            if len(history_io) >= self.threshold_period:
                for j in range(1, self.threshold_period):
                    delta_time = history_io[i]['timestamp'] - history_io[i + j]['timestamp']
                    delta_minutes = int(delta_time.total_seconds() / 60)
                    if delta_minutes >= self.threshold_period:
                        break

                    delta_oi = self.delta_calculate(history_io[i]['open_interest'], history_io[i + j]['open_interest'])
                    if delta_oi is None or delta_oi <= self.threshold:
                        continue

                    await signal_repo.write_signal(exchange, symbol, history_io[i + j]['timestamp'], delta_oi, delta_minutes)
                    break

        count_signal = await signal_repo.count_signals(exchange, symbol, delta_minutes, self.threshold)
        return count_signal



