from __future__ import annotations

from enum import Enum


# FIXME: perhaps change to `Unit`.
class ValueKind(str, Enum):
    BEAUFORT = 'BEAUFORT'
    BOOLEAN = 'BOOLEAN'
    CELSIUS = 'CELSIUS'
    DATETIME = 'DATETIME'
    ENUM = 'ENUM'
    HPA = 'HPA'  # hPa
    HUMIDITY = 'HUMIDITY'
    IMAGE_URL = 'IMAGE_URL'
    MPS = 'MPS'  # m/s
    OTHER = 'OTHER'
    TIMEDELTA = 'TIMEDELTA'
    WATT = 'WATT'
