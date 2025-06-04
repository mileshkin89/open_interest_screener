import aiohttp
import asyncio
from datetime import datetime
from exchange_listeners.base_listener import BaseExchangeListener
from app_logic.default_settings import MIN_INTERVAL
from logging_config import get_logger

logger = get_logger(__name__)


class BinanceListener(BaseExchangeListener):
    BASE_URL = "https://fapi.binance.com"

    async def fetch_usdt_symbols(self) -> list[str]:
        """Get all USDT futures pairs from Binance"""
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
        """Fetch historical Open Interest data"""
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
        """Fetch historical OHLCV data between two timestamps"""
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
