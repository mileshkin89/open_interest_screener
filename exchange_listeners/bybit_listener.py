import aiohttp
from datetime import datetime
from exchange_listeners.base_listener import BaseExchangeListener


class BybitListener(BaseExchangeListener):

    async def fetch_usdt_symbols(self) -> list[str]:
        """Get all USDT perpetual pairs"""
        url = "https://api.bybit.com/v5/market/instruments-info"
        params = {"category": "linear"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()

                if not isinstance(data, dict) or data.get("retCode") != 0:
                    return [{"error": data}]

                symbols = [
                    s["symbol"].upper()
                    for s in data["result"]["list"]
                    if s["quoteCoin"] == "USDT" and s["contractType"] == "LinearPerpetual"
                ]
                return symbols

    async def fetch_oi(self, symbol: str, interval: str = "5", limit: int = 7) -> list[dict]:
        """Fetch historical open interest"""
        url = f"https://api.bybit.com/v5/market/open-interest"
        symbol = symbol.upper()
        result = []

        params = {
            "category": "linear",
            "symbol": symbol,
            "intervalTime": interval+"min",
            "limit": str(limit)
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()

                if not isinstance(data, dict) or data.get("retCode") != 0:
                    return [{"error": data}]

                for entry in data["result"]["list"]:
                    timestamp = int(entry['timestamp'])
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    coin = {
                        "exchange": "Bybit",
                        "symbol": symbol,
                        "datetime": dt,
                        "timestamp": timestamp,
                        "open_interest": float(entry['openInterest']),
                    }
                    result.append(coin)
        return result


    async def fetch_ohlcv(self, symbol: str,  start_date: int, end_date: int, interval: str = "5") -> list[dict]:
        """Fetch OHLCV data for given time range"""
        url = "https://api.bybit.com/v5/market/kline"

        params = {
            "category": "linear",
            "symbol": symbol.upper(),
            "interval": str(interval),
            "start": int(start_date),
            "end": int(end_date),
        }
        result = []

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()

                if not isinstance(data, dict) or data.get("retCode") != 0:
                    return [{"error": data}]

                for candle in data["result"]["list"]:
                    result.append({
                        "timestamp": int(candle[0]),
                        "close": float(candle[4]),
                        "volume": float(candle[5]),
                    })

        return result

