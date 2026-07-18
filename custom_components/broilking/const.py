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

# Cook timer. The firmware takes the timer as two bytes (hours, minutes) and
# never reports it back in GetCurrentTemperatures, so HA mirrors it locally.
MAX_TIMER_MINUTES = 23 * 60 + 59  # 23:59, same ceiling the iQue app offers
TIMER_STEP_MINUTES = 5

# Fired on the HA event bus whenever the cook timer is set or cleared, so
# automations can drive a timer helper / notification. Data: device_id,
# entity_id, minutes, ends_at (ISO 8601, null when cleared).
EVENT_TIMER_SET = "broilking_timer_set"
