"""
start_collector.py

This module is responsible for launching a data collection process for a specific exchange.
It uses Python's multiprocessing to run the collector in a fully isolated process,
ensuring that heavy I/O operations or blocking tasks do not interfere with the main application.

Typical usage:
    from start_collector import start_collector_process
    start_collector_process("binance")
"""

from multiprocessing import Process
from data_collector.run_data_collector import run_collector
from settings.logging_config import get_logger

logger = get_logger(__name__)

def start_collector_process(exchange: str):
    """
    Starts a separate data collection process for the given exchange.

    This function spawns a new OS-level process using the multiprocessing module.
    The process runs `run_collector` from `data_collector.run_data_collector`,
    which collects Open Interest and OHLCV data for all symbols on the specified exchange.

    Args:
        exchange (str): Name of the exchange (e.g., "binance", "bybit").

    Logs:
        - INFO when the collector starts successfully.
        - ERROR if the collector fails to start.
    """
    try:
        proc = Process(target=run_collector, args=(exchange,), name=f"{exchange}_collector")
        proc.start()
        logger.info(f"Started data collector process for {exchange} (PID: {proc.pid})")
    except Exception as e:
        logger.error(f"Failed to start collector for {exchange}: {e}")
