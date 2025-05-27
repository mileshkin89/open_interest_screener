import aiohttp
from datetime import datetime
from exchange_listeners.base_listener import BaseExchangeListener


class BinanceListener(BaseExchangeListener):

    async def fetch_usdt_symbols(self) -> list[str]:
        """Get all USDT futures pairs"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://fapi.binance.com/fapi/v1/exchangeInfo") as resp:
                data = await resp.json()
                symbols = [
                    s["symbol"].upper()
                    for s in data["symbols"]
                    if s["contractType"] == "PERPETUAL" and s["quoteAsset"] == "USDT"
                ]
                return symbols


    async def fetch_oi(self, symbol: str, interval: str = "5", limit: int = 7) -> list[dict]:
        url = f"https://fapi.binance.com/futures/data/openInterestHist"
        symbol = symbol.upper()
        result = []

        params = {
            "symbol": symbol,
            "period": interval+"m",
            "limit": limit
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()

                if not isinstance(data, list):
                    return [{"error": data}]

                for entry in data:
                    oi = entry.get('sumOpenInterest')
                    timestamp = entry.get('timestamp')
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    coin = {
                        "exchange": "Binance",
                        "symbol": symbol,
                        "datetime": dt,
                        "timestamp": timestamp,
                        "open_interest": oi,
                    }
                    result.append(coin)
        return result


    async def fetch_ohlcv(self, symbol: str, start_date: int, end_date: int, interval: str = "5") -> list[dict]:
        url = "https://fapi.binance.com/fapi/v1/klines"

        params = {
            "symbol": symbol,
            "interval": interval+'m',
            "startTime": int(start_date),
            "endTime": int(end_date)
        }
        result = []

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

