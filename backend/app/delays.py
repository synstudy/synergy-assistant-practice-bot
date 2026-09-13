import os
import random

DEFAULT_MIN = 2.0
DEFAULT_MAX = 4.0


def _seconds(name, default):
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def reply_delay():
    low = _seconds("REPLY_DELAY_MIN", DEFAULT_MIN)
    high = _seconds("REPLY_DELAY_MAX", DEFAULT_MAX)

    low = max(low, 0.0)
    high = max(high, 0.0)
    if high == 0.0:
        return 0.0
    if low > high:
        low, high = high, low
    return random.uniform(low, high)
