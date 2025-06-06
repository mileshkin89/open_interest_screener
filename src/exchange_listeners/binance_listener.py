"""
binance_listener.py

Provides an implementation of the BaseExchangeListener interface for Binance Futures.

This module allows asynchronous fetching of:
- All USDT-margined perpetual futures symbols
- Historical Open Interest (OI) data
- Historical OHLCV (candlestick) data

The class uses the official Binance Futures REST API and includes basic error handling and logging.
"""

import aiohttp
import asyncio
from datetime import datetime
from src.exchange_listeners.base_listener import BaseExchangeListener
from src.app_logic.default_settings import MIN_INTERVAL
from src.logging_config import get_logger

logger = get_logger(__name__)


class BinanceListener(BaseExchangeListener):
    """
    Exchange listener for Binance Futures that implements methods to retrieve market data.
    """
    BASE_URL = "https://fapi.binance.com"


    async def fetch_usdt_symbols(self) -> list[str]:
        """
        Retrieve all available USDT-margined perpetual futures trading pairs from Binance.

        Returns:
            list[str]: A list of symbol strings (e.g., ["BTCUSDT", "ETHUSDT"]).
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


    async def fetch_oi(self, symbol: str, interval: str = MIN_INTERVAL, limit: int = 7,
                       session: aiohttp.ClientSession = None) -> list[dict]:
        """
        Fetch historical Open Interest (OI) data for a specific trading pair.

        Args:
            symbol (str): Trading pair symbol (e.g., "BTCUSDT").
            interval (str): Time interval in minutes (e.g., "15").
            limit (int): Number of historical points to retrieve.
            session (aiohttp.ClientSession, optional): Reusable HTTP session. Created if not provided.

        Returns:
            list[dict]: A list of open interest records with timestamps and values.
        """
        url = f"{self.BASE_URL}/futures/data/openInterestHist"
        symbol = symbol.upper()
        result = []
        params = {
            "symbol": symbol,
            "period": f"{interval}m",
            "limit": limit
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
                    return []

                data = await resp.json()

                if not isinstance(data, list):
                    logger.warning(f"OI data not list for {symbol}: {data}")
                    return []

                for entry in data:
                    oi = entry.get("sumOpenInterest")
                    timestamp = entry.get("timestamp")
                    if oi is None or timestamp is None:
                        continue
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    result.append({
                        "exchange": "Binance",
                        "symbol": symbol,
                        "datetime": dt,
                        "timestamp": timestamp,
                        "open_interest": float(oi),
                    })

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error fetching OI for {symbol}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching OI for {symbol}: {e}")
        finally:
            if close_session:
                await session.close()

        return result


    async def fetch_ohlcv(self, symbol: str, start_date: int, end_date: int,
                          interval: str = MIN_INTERVAL,
                          session: aiohttp.ClientSession = None) -> list[dict]:
        """
        Fetch historical OHLCV (Open, High, Low, Close, Volume) candle data.

        Args:
            symbol (str): Trading pair symbol (e.g., "BTCUSDT").
            start_date (int): Start time in milliseconds since epoch.
            end_date (int): End time in milliseconds since epoch.
            interval (str): Time interval in minutes (e.g., "15").
            session (aiohttp.ClientSession, optional): Reusable HTTP session. Created if not provided.

        Returns:
            list[dict]: A list of candle records with timestamp, close price, and volume.
        """
        url = f"{self.BASE_URL}/fapi/v1/klines"
        symbol = symbol.upper()
        result = []
        params = {
            "symbol": symbol,
            "interval": f"{interval}m",
            "startTime": int(start_date),
            "endTime": int(end_date)
        }
        close_session = False

        if session is None:
            session = aiohttp.ClientSession()
            close_session = True

        try:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning(f"OHLCV request failed for {symbol}: {resp.status}, {text}")
                    return []

                data = await resp.json()
                if not isinstance(data, list):
                    logger.warning(f"OHLCV data not list for {symbol}: {data}")
                    return []

                for candle in data:
                    if len(candle) < 6:
                        continue
                    result.append({
                        "timestamp": candle[0],
                        "close": float(candle[4]),
                        "volume": float(candle[5]),
                    })

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error fetching OHLCV for {symbol}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching OHLCV for {symbol}: {e}")
        finally:
            if close_session:
                await session.close()

        return result
