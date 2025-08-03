"""
run_data_collector.py

This module defines a standalone data collector responsible for fetching and saving
Open Interest and OHLCV data for a specific exchange. It is intended to be launched
as a separate process via `start_collector.py`.

Features:
- Fetches symbol list from file (written by SymbolListHandler).
- Fetches Open Interest and OHLCV data at the end of every minute.
- Stores collected data in JSON files, timestamped per minute.
- Uses aiohttp for async I/O and multiprocessing-safe logging.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

from db.repo_factory import get_history_repo
from db.repositories.history_data import HistoryDataRepository
from exchange_listeners.listener_manager import ListenerManager
from app_logic.default_settings import SLEEP_DATA_COLLECTOR
from config import config
# import logging
from logging_config import get_logger

logger = get_logger(__name__)


# def configure_logger(exchange: str):
#     """
#     Configures a dedicated logger for a specific exchange.
#
#     The logger writes logs to a file named `collector_<exchange>.log`,
#     located in the logs directory defined in the config.
#
#     Args:
#         exchange (str): Name of the exchange (e.g., 'binance').
#
#     Returns:
#         logging.Logger: Configured logger instance for the exchange.
#     """
#     logs_dir = config.LOG_PATH.parent
#     logs_dir.mkdir(exist_ok=True)
#     print("logs_dir = ", logs_dir)
#
#     log_file = logs_dir / f"collector_{exchange}.log"
#     print("log_file = ", log_file)
#
#     logger = logging.getLogger(f"collector_{exchange}")
#     logger.setLevel(logging.INFO)
#
#     file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
#     formatter = logging.Formatter(
#         fmt='%(asctime)s - %(levelname)s - %(message)s',
#         datefmt='%Y-%m-%d %H:%M:%S'
#     )
#     file_handler.setFormatter(formatter)
#     logger.addHandler(file_handler)
#
#     logger.propagate = False
#
#     return logger


async def get_symbols_list(exchange: str):
    """
    Loads the list of tradable symbols for the given exchange from a local JSON file.

    The file is expected to be named `<exchange>_symbols.json` and located in the
    configured STORE_SYMBOLS_PATH directory.

    Args:
        exchange (str): Name of the exchange (e.g., 'binance').

    Returns:
        list[str]: A list of symbol strings, or None if the file doesn't exist.
    """
    file_name = f"{exchange}_symbols.json"
    symbols_file = config.STORE_SYMBOLS_PATH / file_name
    if symbols_file.exists():
        with symbols_file.open("r", encoding="utf-8") as f:
            symbols = json.load(f)
            if not symbols:
                logger.warning(f"No symbols found for {exchange}")
                symbols = []
            return symbols


async def fetch_data(symbols: list, callback) -> list:
    """
    Concurrently fetches data for all given symbols using the provided async callback.

    Args:
        symbols (list): List of symbol names (e.g., ['BTCUSDT', 'ETHUSDT']).
        callback (Callable): Asynchronous function used to fetch data per symbol.

    Returns:
        list[dict]: Filtered list of successfully fetched data (skipping exceptions).
    """
    _session = aiohttp.ClientSession()
    try:
        tasks = [
            callback(symbol.upper(), _session)
            for symbol in symbols
        ]
        coins = await asyncio.gather(*tasks, return_exceptions=True)
        return [coin for coin in coins if not isinstance(coin, Exception)]
    finally:
        await _session.close()


async def data_collect(exchange: str):
    """
    Main data collection loop for a specific exchange.

    At the 59th second of every minute:
    - Loads the symbol list for the exchange.
    - Fetches Open Interest data via WebSocket or REST.
    - Fetches OHLCV data.
    - Stores the combined results in a timestamped JSON file.

    Designed to run indefinitely as a background coroutine.

    Args:
        exchange (str): Exchange to collect data for (e.g., 'binance').
    """
    logger.info(f"Started data collector for {exchange}")
    manager = ListenerManager(enabled_exchanges=[exchange])
    listener = manager.get_listener(exchange)

    if not listener:
        logger.error(f"No listener for exchange {exchange}")
        return

    while True:
        now = datetime.now().second

        if now == 59:
            try:
                symbols = await get_symbols_list(exchange)

                history_repo: HistoryDataRepository = await get_history_repo()

                oi_data = await fetch_data(symbols, listener.fetch_oi)
                await history_repo.write_oi(oi_data, exchange)

                # await asyncio.sleep(1)
                ohlcv = await fetch_data(symbols, listener.fetch_ohlcv)
                await history_repo.write_ohlcv(ohlcv, exchange)
            except Exception as e:
                logger.error(f"Error collecting OI from {exchange}: {e}", exc_info=True)

            await asyncio.sleep(SLEEP_DATA_COLLECTOR)
        await asyncio.sleep(0.3)


def run_collector(exchange: str):
    """
    Entry point for launching the data collector for a given exchange.

    This function configures the logger and starts the main data collection loop
    using `asyncio.run`.

    Args:
        exchange (str): Exchange name (e.g., 'binance').
    """
    # global logger
    # logger = configure_logger(exchange)
    asyncio.run(data_collect(exchange))

