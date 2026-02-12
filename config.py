# --- RELAY PIN MAPPING (BCM) ---
# Verified against your last screenshot
RELAYS = {
    'water_pump': 5,
    'light':      6,
    'fan_1':      13,
    'ph_down':    19,
    'ph_up':      26,
    'nutrient_a': 16,
    'nutrient_b': 20,
    'fan_2':      21
}

# --- I2C ADDRESSES ---
I2C_ADDR_BME280 = 0x76
I2C_ADDR_ADS1115 = 0x48

# --- ANALOG CHANNELS (ADS1115) ---
CHAN_PH = 0
CHAN_EC = 1
CHAN_LEVEL = 2

# --- AUTOMATION TARGETS ---
TARGET_TEMP = 25.0
TARGET_PH_MIN = 5.5
TARGET_PH_MAX = 6.5
TARGET_EC = 1.2
EC_TOLERANCE = 0.2

# --- DOSING LOGIC ---
PULSE_TIME = 2        # Seconds to run pumps
COOLDOWN_TIME = 30    # Seconds to wait for mixing

# --- TIMERS (Seconds) ---
WATER_DURATION = 300    # 15 Minutes ON
WATER_INTERVAL = 86100   # 45 Minutes OFF
DOSE_DURATION = 1.5     # 1.5 Seconds dosing pulse
DOSE_WAIT_TIME = 900    # 15 Minutes wait for mixing

# --- CALIBRATION ---
# pH = (Slope * Voltage) + Intercept
PH_SLOPE = -5.7706
PH_INTERCEPT = 15.8918

# Safety
MIN_WATER_VOLTAGE = 1.5 # Tank Empty Limit