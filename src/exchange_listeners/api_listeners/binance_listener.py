"""
binance_listener.py

Implements the BaseExchangeListener interface for Binance USDT-Margined Perpetual Futures.

This module provides asynchronous methods to:
- Fetch all available USDT-margined perpetual futures symbols
- Fetch current Open Interest (OI) for a given symbol
- Fetch the latest 1-minute OHLCV (candlestick) data for a given symbol

Uses the official Binance Futures REST API.
Includes error handling, logging, and supports integration with aiohttp session pooling.
"""

import aiohttp
import asyncio
from datetime import datetime, timezone
from exchange_listeners.api_listeners.base_listener import BaseExchangeListener
from logging_config import get_logger

logger = get_logger(__name__)


class BinanceListener(BaseExchangeListener):
    """
    Exchange listener implementation for Binance Futures.

    Provides methods to fetch symbols, open interest, and OHLCV data using the Binance API.
    """
    BASE_URL = "https://fapi.binance.com"


    async def fetch_usdt_symbols(self) -> list[str]:
        """
        Fetches all available USDT-margined perpetual futures symbols from Binance.

        Returns:
            list[str]: A list of symbol strings (e.g., ["BTCUSDT", "ETHUSDT"]). Returns an empty list on failure.
        """
        url = f"{self.BASE_URL}/fapi/v1/exchangeInfo"
        symbols = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.warning(f"Failed to fetch symbols: {resp.status}, {text}")
                        return []

                    data = await resp.json()
                    for s in data.get("symbols", []):
                        if s.get("contractType") == "PERPETUAL" and s.get("quoteAsset") == "USDT":
                            symbols.append(s["symbol"].upper())

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error fetching USDT symbols: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching USDT symbols: {e}")

        return symbols


    async def fetch_oi(self, symbol: str, session: aiohttp.ClientSession = None) -> dict:
        """
        Fetches the current Open Interest (OI) for the specified symbol.

        Args:
            symbol (str): The trading pair symbol (e.g., "BTCUSDT").
            session (aiohttp.ClientSession, optional): Optional aiohttp session.
                                                       If not provided, a new session is created.

        Returns:
            dict: Dictionary containing:
                - exchange (str): "binance"
                - symbol (str)
                - datetime (str): Human-readable timestamp
                - timestamp (int): Epoch milliseconds
                - open_interest (float)
            Returns an empty dict if request fails or response is invalid.
        """
        url = f"{self.BASE_URL}/fapi/v1/openInterest"
        symbol = symbol.upper()
        result = []

        params = {
            "symbol": symbol,
        }

        close_session = False

        if session is None:
            session = aiohttp.ClientSession()
            close_session = True

        try:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning(f"OI request failed for {symbol}: {resp.status}, {text}")
                    return {}

                data = await resp.json()

                timestamp = data.get("time")
                oi = data.get("openInterest")

                if oi is None or timestamp is None:
                    logger.warning(f"OI data empty for {symbol}")
                    return {}

                dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                result = {
                    "exchange": "binance",
                    "symbol": symbol,
                    "timestamp": dt,
                    "open_interest": float(oi),
                }

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error fetching OI for {symbol}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching OI for {symbol}: {e}")
        finally:
            if close_session:
                await session.close()

        return result

    async def fetch_ohlcv(self, symbol: str, session: aiohttp.ClientSession) -> dict | None:
        """
        Fetches the most recent 1-minute OHLCV (candlestick) data for the given symbol.

        Args:
            symbol (str): The trading pair symbol (e.g., "BTCUSDT").
            session (aiohttp.ClientSession): Shared aiohttp session for efficient reuse.

        Returns:
            dict | None: Dictionary with keys:
                - exchange (str): "binance"
                - symbol (str)
                - timestamp (int): Open time (milliseconds)
                - open (float)
                - high (float)
                - low (float)
                - close (float)
                - volume (float)

            Returns None if request fails or data is malformed.
        """
        url = f"{self.BASE_URL}/fapi/v1/klines"
        symbol = symbol.upper()

        params = {
            "symbol": symbol,
            "interval": "1m",
            "limit": 1
        }

        try:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning(f"OHLCV request failed for {symbol}: {resp.status}, {text}")
                    return None

                data = await resp.json()
                if not data or not isinstance(data, list) or len(data[0]) < 6:
                    logger.warning(f"Invalid OHLCV response for {symbol}: {data}")
                    return None

                candle = data[0]

                timestamp = candle[0]
                dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)

                return {
                    "exchange": "binance",
                    "symbol": symbol,
                    "timestamp": dt,
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5]),
                }

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error fetching OHLCV for {symbol}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching OHLCV for {symbol}: {e}")

        return None
