"""
exchange_urls.py

Provides URL templates and link generation logic for supported cryptocurrency exchanges.
Used to generate direct links to trading pages for specific trading pairs (symbols) on each exchange.

Supported exchanges include:
- Binance
- Bybit

Functions:
    create_link(exchange: str, symbol: str) -> str:
        Returns a direct trading URL for the specified symbol on the given exchange.
"""
from src.app_logic.default_settings import DEFAULT_EXCHANGES
from src.logging_config import get_logger

logger = get_logger(__name__)

# Predefined URL templates for supported exchanges.
EXCHANGE_URLS = {
    "binance": "https://www.binance.com/en/futures/{symbol}?type=perpetual&interval=5m",
    "bybit": "https://www.bybit.com/trade/usdt/{symbol}?interval=5",
    #"OKX": "https://www.okx.com/trade-swap/{symbol}",
}
# https://www.binance.com/en/futures/BTCUSDT?type=perpetual&interval=5m
# https://www.bybit.com/trade/usdt/BTCUSDT?interval=5
# https://www.okx.com/trade-swap/BTC-USDT-SWAP


def create_link(exchange: str, symbol: str) -> str:
    """
    Generates a trading URL for the given exchange and symbol.

    Args:
        exchange (str): The exchange name (e.g., "binance", "bybit").
        symbol (str): The trading pair symbol (e.g., "BTCUSDT").

    Returns:
        str: A formatted trading URL if the exchange is supported,
             otherwise "#" is returned and a warning is logged.

    Notes:
        - Exchange names are case-insensitive.
        - Only exchanges listed in DEFAULT_EXCHANGES are considered valid.
    """
    exchange = exchange.lower()
    if exchange not in DEFAULT_EXCHANGES:
        logger.warning(f"Unknown exchange: {exchange} — no URL template found")
        return "#"
    elif exchange == "binance":
        rendered_symbol = symbol
    elif exchange == "bybit":
        rendered_symbol = symbol
    # elif exchange == "OKX":
    #     rendered_symbol = symbol.replace("USDT", "-USDT-SWAP")

    return EXCHANGE_URLS[exchange].format(symbol=rendered_symbol)
