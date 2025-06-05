"""
base_listener.py

Defines an abstract base class for exchange listeners used to fetch trading data such as symbols,
open interest (OI), and OHLCV (Open/High/Low/Close/Volume) data. Concrete implementations
should be created for each specific exchange (e.g., Binance, Bybit) by subclassing this interface.
"""

from abc import ABC, abstractmethod
import aiohttp

class BaseExchangeListener(ABC):
    """
    Abstract base class for exchange data listeners.

    Defines the required interface for fetching USDT trading pairs, open interest, and OHLCV data.
    Subclasses must implement all abstract methods using the exchange's API.
    """

    @abstractmethod
    async def fetch_usdt_symbols(self) -> list[str]:
        """
        Fetches all available USDT trading pairs from the exchange.

        Returns:
             list[str]: A list of symbol strings (e.g., ["BTCUSDT", "ETHUSDT"]).
        """
        pass


    @abstractmethod
    async def fetch_oi(self, symbol: str, interval: str, limit: int, session: aiohttp.ClientSession) -> list[dict]:
        """
        Fetches open interest data for a given symbol.

        Args:
            symbol (str): Trading symbol (e.g., "BTCUSDT").
            interval (str): Timeframe for the data (e.g., "5m", "15m").
            limit (int): Number of data points to retrieve.
            session (aiohttp.ClientSession): An aiohttp session for making HTTP requests.

        Returns:
            list[dict]: A list of dictionaries containing open interest data.
        """
        pass

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, start_date: int, end_date: int, interval: str, session: aiohttp.ClientSession) -> list[dict]:
        """
        Fetches OHLCV data for a given symbol and time range.

        Args:
            symbol (str): Trading symbol (e.g., "BTCUSDT").
            start_date (int): Start of the range in milliseconds since epoch.
            end_date (int): End of the range in milliseconds since epoch.
            interval (str): Timeframe for the candles (e.g., "15m").
            session (aiohttp.ClientSession): An aiohttp session for making HTTP requests.

        Returns:
            list[dict]: A list of dictionaries representing OHLCV candles.
        """
        pass


