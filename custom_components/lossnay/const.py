"""Constants for the Mitsubishi Lossnay ERV integration."""
from datetime import timedelta

DOMAIN = "lossnay"

SCAN_INTERVAL = timedelta(seconds=60)

MELVIEW_BASE_URL = "https://api.melview.net/api"
MELVIEW_LOGIN_URL = f"{MELVIEW_BASE_URL}/login.aspx"
MELVIEW_ROOMS_URL = f"{MELVIEW_BASE_URL}/rooms.aspx"
MELVIEW_UNIT_COMMAND_URL = f"{MELVIEW_BASE_URL}/unitcommand.aspx"

APP_VERSION = "4.3.1010"

CONF_UNIT_ID = "unitid"
CONF_UNIT_NAME = "unit_name"

# Fan speed: command -> (preset name, percentage midpoint)
FAN_SPEED_MAP = {
    2: ("low", 25),
    3: ("medium_low", 50),
    5: ("medium_high", 75),
    6: ("boost", 100),
}

# Preset name -> command value
FAN_PRESET_TO_CMD = {
    "low": 2,
    "medium_low": 3,
    "medium_high": 5,
    "boost": 6,
}

FAN_PRESETS = ["low", "medium_low", "medium_high", "boost"]

# Percentage thresholds -> fan speed command
# 1-25  -> low (FS2), 26-50 -> medium_low (FS3), 51-75 -> medium_high (FS5), 76-100 -> boost (FS6)
PERCENTAGE_TO_FAN_CMD = [
    (25, 2),
    (50, 3),
    (75, 5),
    (100, 6),
]

# Mode: setmode value -> HA HVAC mode
# MD1 = heat exchanger / heat recovery -> "heat"
# MD3 = auto                           -> "auto"
# MD7 = bypass (fresh air)             -> "fan_only"
MODE_TO_HVAC = {
    1: "heat",
    3: "auto",
    7: "fan_only",
}

HVAC_TO_MODE_CMD = {
    "heat": "MD1",
    "auto": "MD3",
    "fan_only": "MD7",
}

HVAC_MODES = ["heat", "auto", "fan_only", "off"]

# Power
CMD_POWER_ON = "PW1"
CMD_POWER_OFF = "PW0"

# Unit type string returned by rooms.aspx
ERV_TYPE = "ERV"
