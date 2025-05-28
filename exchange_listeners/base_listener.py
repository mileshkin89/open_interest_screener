from abc import ABC, abstractmethod
import aiohttp

class BaseExchangeListener(ABC):

    @abstractmethod
    async def fetch_usdt_symbols(self) -> list[str]: pass

    @abstractmethod
    async def fetch_oi(self, symbol: str, interval: str, limit: int, session: aiohttp.ClientSession) -> list[dict]: pass

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, start_date: int, end_date: int, interval: str, session: aiohttp.ClientSession) -> list[dict]: pass


