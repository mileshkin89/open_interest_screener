# start_collector.py

import subprocess
from pathlib import Path
from logging_config import get_logger

logger = get_logger(__name__)

def start_collector_process(exchange: str):
    script_path = Path(__file__).parent.parent / "data_collector" / "run_data_collector.py"
    cmd = ["poetry", "run", "python", str(script_path), exchange]

    try:
        with open(f"collector_{exchange}.log", "w") as log_file:
            subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True
            )

        # subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"Started data collector for {exchange}")
    except Exception as e:
        logger.error(f"Failed to start collector for {exchange}: {e}")