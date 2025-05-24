from abc import ABC, abstractmethod

class BaseExchangeListener(ABC):

    @abstractmethod
    async def fetch_usdt_symbols(self) -> list[str]: pass

    @abstractmethod
    async def fetch_oi(self, symbol: str, interval: str, limit: int) -> list[dict]: pass

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, interval: str, start_date: int, end_date: int) -> list[dict]: pass
