"""Constants for the Broil King Smoker integration."""

DOMAIN = "broilking"

DEFAULT_SCAN_INTERVAL = 10  # seconds

# currentMode values reported by the firmware
MODES = {0: "Off", 1: "Smoke", 2: "Cook", 3: "High"}
MODE_IDS = {v: k for k, v in MODES.items()}

# Climate bounds in degrees C. The pellet firmware (iQue.java) accepts a grill
# setpoint of 180-600 F, i.e. ~82-316 C. The grill clamps to its own range too.
MIN_TEMP_C = 82   # 180 F
MAX_TEMP_C = 316  # 600 F
TEMP_STEP_C = 1.0

# Cook timer, carried as two bytes (hours, minutes). SetTimer caps hours at 99,
# but the control board only reports an hour byte back, so keep both ends within
# what it can echo.
MAX_TIMER_MINUTES = 99 * 60 + 59
TIMER_STEP_MINUTES = 5
