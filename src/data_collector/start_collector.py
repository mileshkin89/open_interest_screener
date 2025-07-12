# start_collector.py

from multiprocessing import Process
from data_collector.run_data_collector import run_collector
from logging_config import get_logger

logger = get_logger(__name__)

def start_collector_process(exchange: str):
    try:
        proc = Process(target=run_collector, args=(exchange,), name=f"{exchange}_collector")
        proc.start()
        logger.info(f"Started data collector process for {exchange} (PID: {proc.pid})")
    except Exception as e:
        logger.error(f"Failed to start collector for {exchange}: {e}")
