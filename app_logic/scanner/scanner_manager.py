"""
scanner_manager.py

Manages the lifecycle of signal scanners per Telegram user.

This module:
- Stores currently running scanner tasks per user.
- Starts a new scanner or restarts it with updated settings.
- Ensures that only one scanner per user is active at any time.

Functions:
    start_or_restart_scanner: Starts or restarts a scanner for a specific user.

Globals:
    running_scanners (dict): Tracks active scanners per user.
        - "task" (asyncio.Task): The currently running scanning coroutine.
        - "settings" (dict): The settings used for this scanner instance.

Requires:
    - ListenerManager: to create exchange listeners per run.
    - ConditionHandler: to evaluate open interest and volume change logic.
    - Scanner: the scanning engine which detects signals and sends notifications.
"""

import asyncio
from typing import Callable
from exchange_listeners.listener_manager import ListenerManager
from app_logic.condition_handler import ConditionHandler
from .scanner import Scanner
from logging_config import get_logger

logger = get_logger(__name__)

running_scanners = {}  # user_id: {"task": task, "settings": {...}}


async def start_or_restart_scanner(user_id: int, settings: dict, exchanges: list, notify_func: Callable):
    """
    Starts a new scanner or restarts it with updated settings for the given user.

    If a scanner with the same settings is already running, no action is taken.
    If settings differ, the previous scanner is gracefully cancelled and a new one is started.

    Args:
        user_id (int): The Telegram user ID requesting the scan.
        settings (dict): User-defined scanner settings (e.g. threshold, period).
        exchanges (list): List of enabled exchanges for the user (e.g., ["binance", "bybit"]).
        notify_func (Callable): Async function that handles signal notification to the user.

    Returns:
        str: One of:
            - "already_running": Scanner is already active with the same settings.
            - "started": Scanner has been successfully (re)started.
    """

    current = running_scanners.get(user_id)

    if current:
        if current["settings"] == settings:
            # The scanner is already running with the same settings.
            return "already_running"
        else:
            # Stop the previous one
            current["task"].cancel()
            try:
                await current["task"]
            except asyncio.CancelledError:
                pass

    try:
        manager = ListenerManager(enabled_exchanges=exchanges)
        cond = ConditionHandler()
        scanner_ = Scanner(manager=manager, handler=cond)
    except Exception as e:
        logger.critical(f"Error initializing fundamental clients: {e}", exc_info=True)

    # Launching a new
    task = asyncio.create_task(scanner_.run_scanner(user_id, notify_func, settings["period"], settings["threshold"]))
    logger.info(f"User {user_id} started screener successfully. Settings: {settings}")
    running_scanners[user_id] = {"task": task, "settings": settings}
    return "started"
