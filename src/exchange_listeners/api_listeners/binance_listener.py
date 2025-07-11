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
from exchange_listeners.api_listeners.base_listener import BaseExchangeListener
from app_logic.default_settings import MIN_INTERVAL
from logging_config import get_logger

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


    async def fetch_oi(self, symbol: str, session: aiohttp.ClientSession = None) -> dict:
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

                dt = datetime.fromtimestamp(timestamp / 1000)
                result = {
                    "exchange": "Binance",
                    "symbol": symbol,
                    "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "timestamp": timestamp,
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
                return {
                    "symbol": symbol,
                    "timestamp": candle[0],
                    "datetime": datetime.fromtimestamp(candle[0] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
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

    # async def fetch_ohlcv(self, symbol: str, start_date: int, end_date: int,
    #                       interval: str = MIN_INTERVAL,
    #                       session: aiohttp.ClientSession = None) -> list[dict]:
    #     """
    #     Fetch historical OHLCV (Open, High, Low, Close, Volume) candle data.
    #
    #     Args:
    #         symbol (str): Trading pair symbol (e.g., "BTCUSDT").
    #         start_date (int): Start time in milliseconds since epoch.
    #         end_date (int): End time in milliseconds since epoch.
    #         interval (str): Time interval in minutes (e.g., "15").
    #         session (aiohttp.ClientSession, optional): Reusable HTTP session. Created if not provided.
    #
    #     Returns:
    #         list[dict]: A list of candle records with timestamp, close price, and volume.
    #     """
    #     url = f"{self.BASE_URL}/fapi/v1/klines"
    #     symbol = symbol.upper()
    #     result = []
    #     params = {
    #         "symbol": symbol,
    #         "interval": f"{interval}m",
    #         "startTime": int(start_date),
    #         "endTime": int(end_date)
    #     }
    #     close_session = False
    #
    #     if session is None:
    #         session = aiohttp.ClientSession()
    #         close_session = True
    #
    #     try:
    #         async with session.get(url, params=params, timeout=10) as resp:
    #             if resp.status != 200:
    #                 text = await resp.text()
    #                 logger.warning(f"OHLCV request failed for {symbol}: {resp.status}, {text}")
    #                 return []
    #
    #             data = await resp.json()
    #             if not isinstance(data, list):
    #                 logger.warning(f"OHLCV data not list for {symbol}: {data}")
    #                 return []
    #
    #             for candle in data:
    #                 if len(candle) < 6:
    #                     continue
    #                 result.append({
    #                     "timestamp": candle[0],
    #                     "close": float(candle[4]),
    #                     "volume": float(candle[5]),
    #                 })
    #
    #     except (aiohttp.ClientError, asyncio.TimeoutError) as e:
    #         logger.error(f"Network error fetching OHLCV for {symbol}: {e}")
    #     except Exception as e:
    #         logger.error(f"Unexpected error fetching OHLCV for {symbol}: {e}")
    #     finally:
    #         if close_session:
    #             await session.close()
    #
    #     return result
