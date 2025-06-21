"""Logging configuration for the application.

This module provides a centralized logger setup that writes logs to both the console and a file.
Console logs show all messages starting from INFO level, while file logs store INFO and above.

The log file is stored in the directory defined by `config.LOG_PATH`.
"""

import logging
from config import config


def get_logger(name: str = __name__) -> logging.Logger:
    """Creates and configures a logger with both console and file handlers.

    The logger will:
    - Output INFO and higher messages to the console.
    - Save INFO and higher messages to a log file at `logs/app.log`.
    - Suppress verbose logs from `httpx` library.

    Args:
        name (str): The logger name, typically `__name__`.

    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        config.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(config.LOG_PATH, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        logger.setLevel(logging.INFO)

        logging.getLogger("httpx").setLevel(logging.WARNING)

    return logger