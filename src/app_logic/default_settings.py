"""
default_settings.py

This module defines default configuration constants used across the application.
"""

DEFAULT_SETTINGS = {"period": 15, "threshold": 0.05}
"""
Default parameters for signal evaluation:
- period (int): Number of minutes over which Open Interest change is measured.
- threshold (float): Minimum relative Open Interest change (e.g., 0.05 = 5%) to trigger a signal.
"""
DEFAULT_EXCHANGES = ["binance", "bybit", "okx"]
"""
List of enabled exchanges by default. Used when the user has not manually selected exchanges.
"""

INACTIVITY_DAYS = 3
"""
Number of days of user inactivity before sending a confirmation request.
"""
WAITING_DAYS = 1
"""
Number of days to wait after sending a confirmation request.
If the user does not respond within this period, the scanner will be stopped.
"""

SLEEP_TIMER_SECOND = 300
"""
Default interval (in seconds) between scanner cycles or background checks (e.g., 5 minutes).
"""
MIN_INTERVAL = "5"
"""
Minimum timeframe (in minutes) used for Open Interest data requests to exchanges.
Used as a default granularity for analysis.
"""