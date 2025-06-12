"""
okx_listener.py

Provides an implementation of the BaseExchangeListener interface for OKX Futures.

This module allows asynchronous fetching of:
- All USDT-margined perpetual futures symbols
- Historical Open Interest (OI) data
- Historical OHLCV (candlestick) data

The class uses the official OKX Futures REST API and includes basic error handling and logging.
"""

import aiohttp
import asyncio
from datetime import datetime
from src.exchange_listeners.base_listener import BaseExchangeListener
from src.app_logic.default_settings import MIN_INTERVAL
from src.logging_config import get_logger

logger = get_logger(__name__)


class OKXListener(BaseExchangeListener):
    """
    Exchange listener for OKX Futures that implements methods to retrieve market data.
    """
    BASE_URL = "https://www.okx.com"

    async def fetch_usdt_symbols(self) -> list[str]:
        """
           Retrieve all available USDT-margined perpetual futures trading pairs from OKX (instType = SWAP).

           Returns:
               list[str]: A list of symbol strings (e.g., ["BTCUSDT", "ETHUSDT"]).
        """
        url = f"{self.BASE_URL}/api/v5/public/instruments"
        symbols = []
        params = {
            "instType": "SWAP"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        #print("resp.status", resp.status)##############
                        #print("resp.text", text)
                        logger.warning(f"Failed to fetch OKX symbols: {resp.status}, {text}")
                        return []

                    data = await resp.json()
                    #print("data", data)  ################
                    if data.get("code") != "0":
                        logger.warning(f"Invalid OKX symbols response: {data}")
                        return []

                    print("data.get('data', [])" , data.get("data", []))
                    print()
                    for s in data.get("data", []):
                        if s["settleCcy"] == "USDT" and s["instType"] == "SWAP":
                            print("="*10)
                            print(s["instId"])
                            symbols.append(s["instId"])
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error fetching OKX symbols: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching OKX symbols: {e}")

        print()
        print("OKX len(symbols) = ", len(symbols))####################
        print("OKX symbols = ", symbols)
        return symbols


    async def fetch_oi(self, symbol: str, interval: str = MIN_INTERVAL, limit: int = 7,
                       session: aiohttp.ClientSession = None) -> list[dict]:
        """
        Fetch historical Open Interest (OI) data for a given trading pair from OKX.

        Args:
            symbol (str): Trading pair symbol (e.g., "BTCUSDT").
            interval (str): Time interval in minutes (e.g., "15").
            limit (int): Number of historical points to retrieve.
            session (aiohttp.ClientSession, optional): Reusable HTTP session. Created if not provided.

        Returns:
            list[dict]: A list of OI records with timestamps and values.
        """
        url = f"{self.BASE_URL}/api/v5/public/open-interest"
        symbol = symbol.upper()
        result = []
        params = {
            "instId": symbol,
            "bar": f"{interval}m",
            "limit": str(limit)
        }

        close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True

        try:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning(f"OKX. OI request failed for {symbol}: {resp.status}, {text}")
                    return []

                data = await resp.json()
                print("OKX data = ", data)#############

                if data.get("code") != "0":
                    logger.warning(f"OKX. Invalid OI data for {symbol}: {data}")
                    return []

                for entry in data["data"]:
                    timestamp = int(entry.get("ts"))
                    oi = float(entry.get("oi"))
                    if oi is None or timestamp is None:
                        continue
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    result.append({
                        "exchange": "OKX",
                        "symbol": symbol,
                        "datetime": dt,
                        "timestamp": timestamp,
                        "open_interest": oi,
                    })
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"OKX. Network error fetching OI for {symbol}: {e}")
        except Exception as e:
            logger.error(f"OKX. Unexpected error fetching OI for {symbol}: {e}")
        finally:
            if close_session:
                await session.close()

        print("OKX fetch_oi result = ", result)#######################
        return result


    async def fetch_ohlcv(self, symbol: str, start_date: int, end_date: int,
                          interval: str = MIN_INTERVAL,
                          session: aiohttp.ClientSession = None) -> list[dict]:
        """
        Fetch historical OHLCV (Open, High, Low, Close, Volume) candle data from OKX.

        Args:
            symbol (str): Trading pair symbol (e.g., "BTCUSDT").
            start_date (int): Start time in milliseconds since epoch.
            end_date (int): End time in milliseconds since epoch.
            interval (str): Time interval in OKX format (e.g., "15").
            session (aiohttp.ClientSession, optional): Reusable HTTP session. Created if not provided.

        Returns:
            list[dict]: A list of candle data records with timestamp, close price, and volume.
        """
        url = f"{self.BASE_URL}/api/v5/market/candles"
        symbol = symbol.upper()
        result = []
        params = {
            "instId": symbol,
            "bar": f"{interval}m",
            "after": str(start_date),
            "before": str(end_date)
        }

        close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True

        try:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning(f"OKX. OHLCV request failed for {symbol}: {resp.status}, {text}")
                    return []

                data = await resp.json()

                if data.get("code") != "0":
                    logger.warning(f"OKX. Invalid OHLCV data for {symbol}: {data}")
                    return []

                for candle in data["data"]:
                    result.append({
                        "timestamp": int(candle[0]),
                        "close": float(candle[4]),
                        "volume": float(candle[5]),
                    })

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"OKX. Network error fetching OHLCV for {symbol}: {e}")
        except Exception as e:
            logger.error(f"OKX. Unexpected error fetching OHLCV for {symbol}: {e}")
        finally:
            if close_session:
                await session.close()

        print("OKX fetch_ohlcv result = ", result)  #######################
        return result
