"""
Small formatting helpers shared across the dashboards.

The "no leading zero on the hour" trick (1:00 PM instead of 01:00 PM) is
written two different ways depending on OS: "%-I" on Linux/macOS, "%#I"
on Windows. Neither works on the other platform - using the wrong one
raises "ValueError: Invalid format string" the moment a dashboard tries
to draw a single appointment card, which can crash the whole render
loop and leave the page looking empty. format_time()/format_datetime()
below pick the right one automatically.
"""

import platform

# Computed once at import time rather than on every call.
_HOUR_CODE = "%#I" if platform.system() == "Windows" else "%-I"


def format_time(dt):
    """A datetime/time -> "1:05 PM" style string, cross-platform."""
    return dt.strftime(_HOUR_CODE + ":%M %p")


def format_datetime(dt, date_fmt="%A, %B %d"):
    """A datetime -> "Monday, January 05 at 1:05 PM" style string."""
    return dt.strftime(date_fmt) + " at " + format_time(dt)
