# bot/scanner_manager.py

import asyncio
from scanner_init import scanner_


running_scanners = {}  # user_id: {"task": task, "settings": {...}}

async def start_or_restart_scanner(user_id: int, settings: dict, notify_func):

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

    # Launching a new
    task = asyncio.create_task(scanner_.run_scanner(notify_func, settings["period"], settings["threshold"]))
    running_scanners[user_id] = {"task": task, "settings": settings}
    return "started"
