import aiohttp
from datetime import datetime


BINANCE_FUTURES_API = "https://fapi.binance.com"
AVAILABLE_INTERVAL = ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"]


class BinanceListener:

    async def fetch_usdt_symbols(self) -> list[str]:
        """Get all USDT futures pairs"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BINANCE_FUTURES_API}/fapi/v1/exchangeInfo") as resp:
                data = await resp.json()
                symbols = [
                    s["symbol"].upper()
                    for s in data["symbols"]
                    if s["contractType"] == "PERPETUAL" and s["quoteAsset"] == "USDT"
                ]
                return symbols


    async def fetch_oi(self, symbol: str, interval: str = "5m", limit: int = 5) -> list[dict]:
        url = f"{BINANCE_FUTURES_API}/futures/data/openInterestHist"
        symbol = symbol.upper()
        interval = interval.lower()
        limit = limit
        result = []

        params = {
            "symbol": symbol,
            "period": interval,
            "limit": limit
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()

                if not isinstance(data, list):
                    return [{"error": data}]

                for entry in data:
                    oi = entry.get('sumOpenInterest')
                    oi_v = entry.get('sumOpenInterestValue')
                    timestamp = entry.get('timestamp')
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    coin = {
                        "exchange": "Binance",
                        "symbol": symbol,
                        "datetime": dt,
                        "timestamp": timestamp,
                        "OpenInterest": oi,
                        "OpenInterestValue": oi_v
                    }

                    result.append(coin)
        return result


    async def fetch_ohlcv(self, symbol: str, interval: str , start_date: int, end_date: int) -> list[dict]:
        url = f"{BINANCE_FUTURES_API}/fapi/v1/klines"

        result = []

        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": int(start_date),
            "endTime": int(end_date)
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()

                if not isinstance(data, list):
                    return [{"error": data}]

                for candle in data:
                    result.append({
                        "timestamp": candle[0],
                        "close": float(candle[4]),
                        "volume": float(candle[5])
                    })

        return result

