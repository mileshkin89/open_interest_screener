# run_data_collector.py

import sys
import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path

from exchange_listeners.listener_manager import ListenerManager
from app_logic.default_settings import SLEEP_DATA_COLLECTOR
from config import config
import logging

sys.path.append(str(Path(__file__).resolve().parent.parent))

OI_STORAGE_DIR = config.STORE_SYMBOLS_PATH


def configure_logger(exchange: str):

    logs_dir = config.LOG_PATH.parent
    logs_dir.mkdir(exist_ok=True)
    print("logs_dir = ", logs_dir)

    log_file = logs_dir / f"collector_{exchange}.log"
    print("log_file = ", log_file)

    logger = logging.getLogger(f"collector_{exchange}")
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger


async def get_symbols_list(exchange: str):
    file_name = f"{exchange}_symbols.json"
    symbols_file = config.STORE_SYMBOLS_PATH / file_name
    if symbols_file.exists():
        with symbols_file.open("r", encoding="utf-8") as f:
            symbols = json.load(f)
            return symbols


async def save_data_to_file(data: list[dict], exchange: str):
    now = datetime.now()
    filename = f"{exchange}_data_{now.strftime('%Y%m%d_%H%M')}.json"
    path = Path(OI_STORAGE_DIR)
    path.mkdir(parents=True, exist_ok=True)
    with open(path / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(data)} records to {filename}")


async def fetch_data(symbols: list, callback) -> list:
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
    logger.info(f"Started data collector for {exchange}")
    manager = ListenerManager(enabled_exchanges=[exchange])
    listener = manager.get_listener(exchange)

    if not listener:
        logger.error(f"No listener for exchange {exchange}")
        return

    while True:
        now = datetime.now().second
        print(now)

        if now == 59:
            results = []
            try:
                symbols = await get_symbols_list(exchange)

                oi_data = await fetch_data(symbols, listener.fetch_oi)
                print(f"[data_collect] oi_data = {oi_data}")

                await asyncio.sleep(1)
                ohlcv = await fetch_data(symbols, listener.fetch_ohlcv)
                print(f"[data_collect] ohlcv = {ohlcv}")

                if oi_data and ohlcv:
                    results.extend(oi_data)
                    results.extend(ohlcv)

                await save_data_to_file(results, exchange)

            except Exception as e:
                logger.error(f"Error collecting OI from {exchange}: {e}", exc_info=True)

            await asyncio.sleep(SLEEP_DATA_COLLECTOR)
        await asyncio.sleep(0.3)


def run_collector(exchange: str):
    global logger
    logger = configure_logger(exchange)
    asyncio.run(data_collect(exchange))



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_data_collector.py <exchange>")
        sys.exit(1)

    run_collector(sys.argv[1].lower())


