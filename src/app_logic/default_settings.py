"""
default_settings.py

This module defines default configuration constants used across the application.
"""

DEFAULT_SETTINGS = {"period": 15, "threshold": 0.05}
"""
dict: Default parameters for signal evaluation:
- period (int): Number of minutes over which Open Interest change is measured.
- threshold (float): Minimum relative Open Interest change (e.g., 0.05 = 5%) to trigger a signal.
"""
DEFAULT_EXCHANGES = ["binance", "bybit"]
"""
list: List of enabled exchanges by default. Used when the user has not manually selected exchanges.
"""
DEFAULT_TIME_ZONE = "UTC"
"""
str: Default time zone used if the user has not selected one explicitly.

Used to format signal timestamps and time-based messages.
"""


INACTIVITY_DAYS = 3
"""
int: Number of days of user inactivity before sending a confirmation request.
"""
WAITING_DAYS = 1
"""
int: Number of days to wait after sending a confirmation request.
If the user does not respond within this period, the scanner will be stopped.
"""


START_FETCH_SYMBOLS_SECOND = 49
"""
int: The second of each minute at which the symbol list update should begin.

Used to synchronize the update cycle precisely to a known second (e.g., 49),
so that symbol fetching aligns with minute-based scheduling.
"""
SLEEP_FETCH_SYMBOLS_SECOND = 56
"""
int: Number of seconds to sleep after updating all symbol lists.

Prevents the system from aggressively fetching symbols repeatedly.
Used to throttle update frequency between checks.
"""


SLEEP_TIMER_SECOND = 300
"""
int: Default interval (in seconds) between scanner cycles or background checks (e.g., 5 minutes).
"""
MIN_INTERVAL = "5"
"""
str: Minimum timeframe (in minutes) used for Open Interest data requests to exchanges.
Used as a default granularity for analysis.
"""

POPULAR_TIMEZONES_BY_OFFSET = {
    -12: ["Etc/GMT+12"],
    -11: ["Pacific/Midway", "Pacific/Niue"],
    -10: ["Pacific/Honolulu", "Pacific/Tahiti"],
    -9:  ["America/Anchorage", "Pacific/Gambier"],
    -8:  ["America/Los_Angeles", "America/Tijuana"],
    -7:  ["America/Denver", "America/Phoenix"],
    -6:  ["America/Chicago", "America/Mexico_City"],
    -5:  ["America/New_York", "America/Toronto", "America/Lima"],
    -4:  ["America/Santiago", "America/Caracas", "America/Halifax"],
    -3:  ["America/Sao_Paulo", "America/Argentina/Buenos_Aires"],
    -2:  ["America/Noronha"],
    -1:  ["Atlantic/Azores", "Atlantic/Cape_Verde"],
     0:  ["UTC", "Europe/London", "Africa/Abidjan"],
     1:  ["Europe/Berlin", "Europe/Paris", "Africa/Lagos"],
     2:  ["Europe/Kyiv", "Europe/Bucharest", "Africa/Johannesburg"],
     3:  ["Europe/Moscow", "Africa/Nairobi", "Asia/Riyadh"],
     4:  ["Asia/Dubai", "Asia/Baku", "Europe/Samara"],
     5:  ["Asia/Karachi", "Asia/Tashkent"],
     6:  ["Asia/Dhaka", "Asia/Almaty"],
     7:  ["Asia/Bangkok", "Asia/Jakarta"],
     8:  ["Asia/Shanghai", "Asia/Singapore", "Asia/Manila"],
     9:  ["Asia/Tokyo", "Asia/Seoul"],
    10:  ["Australia/Sydney", "Pacific/Port_Moresby"],
    11:  ["Pacific/Noumea", "Asia/Magadan"],
    12:  ["Pacific/Auckland", "Pacific/Fiji"],
    13:  ["Pacific/Tongatapu"],
    14:  ["Pacific/Kiritimati"]
}
"""
dict[int, list[str]]: A mapping of UTC offsets to popular time zone identifiers.

Used for user-friendly time zone selection during setup.
Allows users to choose their time zone from a curated list based on numeric offset.
"""