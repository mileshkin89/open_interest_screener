import aiohttp
from datetime import datetime

BYBIT_FUTURES_API = "https://api.bybit.com"
AVAILABLE_INTERVAL = ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"]


class BybitListener:

    async def fetch_usdt_symbols(self) -> list[str]:
        """Get all USDT perpetual pairs"""
        url = f"{BYBIT_FUTURES_API}/v5/market/instruments-info"
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

    async def fetch_oi(self, symbol: str, interval: str = "5m", limit: int = 5) -> list[dict]:
        """Fetch historical open interest"""
        url = f"{BYBIT_FUTURES_API}/v5/market/open-interest"
        symbol = symbol.upper()
        result = []

        params = {
            "category": "linear",
            "symbol": symbol,
            "intervalTime": interval,
            "limit": limit
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
                        "OpenInterest": float(entry['openInterest']),
                        "OpenInterestValue": float(entry['openInterestValue'])
                    }
                    print("coin = ",coin)
                    result.append(coin)

        return result

    async def fetch_ohlcv(self, symbol: str, interval: str, start_date: int, end_date: int) -> list[dict]:
        """Fetch OHLCV data for given time range"""
        url = f"{BYBIT_FUTURES_API}/v5/market/kline"

        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": interval,
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

        print("result = ",result)
        return result
