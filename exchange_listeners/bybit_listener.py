import aiohttp
import asyncio
from datetime import datetime
from exchange_listeners.base_listener import BaseExchangeListener
from app_logic.default_settings import MIN_INTERVAL
from logging_config import get_logger

logger = get_logger(__name__)


class BybitListener(BaseExchangeListener):
    BASE_URL = "https://api.bybit.com"

    async def fetch_usdt_symbols(self) -> list[str]:
        """Get all USDT perpetual pairs from Bybit"""
        url = f"{self.BASE_URL}/v5/market/instruments-info"
        params = {"category": "linear"}
        symbols = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.warning(f"Failed to fetch Bybit symbols: {resp.status}, {text}")
                        return []

                    data = await resp.json()
                    if not isinstance(data, dict) or data.get("retCode") != 0:
                        logger.warning(f"Invalid Bybit symbols response: {data}")
                        return []

                    for s in data["result"]["list"]:
                        if s["quoteCoin"] == "USDT" and s["contractType"] == "LinearPerpetual":
                            symbols.append(s["symbol"].upper())

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error fetching Bybit symbols: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching Bybit symbols: {e}")

        return symbols


    async def fetch_oi(self, symbol: str, interval: str = MIN_INTERVAL, limit: int = 7,
                       session: aiohttp.ClientSession = None) -> list[dict]:
        """Fetch historical open interest from Bybit"""
        url = f"{self.BASE_URL}/v5/market/open-interest"
        symbol = symbol.upper()
        result = []
        params = {
            "category": "linear",
            "symbol": symbol,
            "intervalTime": f"{interval}min",
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
                    logger.warning(f"OI request failed for {symbol}: {resp.status}, {text}")
                    return []

                data = await resp.json()
                if not isinstance(data, dict) or data.get("retCode") != 0:
                    logger.warning(f"Invalid OI data for {symbol}: {data}")
                    return []

                for entry in data["result"]["list"]:
                    timestamp = int(entry["timestamp"])
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    result.append({
                        "exchange": "Bybit",
                        "symbol": symbol,
                        "datetime": dt,
                        "timestamp": timestamp,
                        "open_interest": float(entry["openInterest"]),
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
        """Fetch OHLCV data from Bybit between two timestamps"""
        url = f"{self.BASE_URL}/v5/market/kline"
        symbol = symbol.upper()
        result = []
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": interval,
            "start": int(start_date),
            "end": int(end_date)
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
                if not isinstance(data, dict) or data.get("retCode") != 0:
                    logger.warning(f"Invalid OHLCV data for {symbol}: {data}")
                    return []

                for candle in data["result"]["list"]:
                    if len(candle) < 6:
                        continue
                    result.append({
                        "timestamp": int(candle[0]),
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
