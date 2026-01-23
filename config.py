# GPIO Pin Mapping (BCM Mode)
RELAYS = {
    'water_pump': 5,    # Relay 1 (GPIO 5)
    'light': 6,         # Relay 2 (GPIO 6)
    'fan': 13,          # Relay 3 (GPIO 13)
    'ph_down': 19,      # Relay 4 (GPIO 19)
    'ph_up': 26,        # Relay 5 (GPIO 26)
    'nutrient_a': 16,   # Relay 6 (GPIO 16)
    'nutrient_b': 20,   # Relay 7 (GPIO 20)
    'spare': 21         # Relay 8 (GPIO 21)
}

# I2C Addresses
I2C_ADDR_BME280 = 0x76
I2C_ADDR_ADS1115 = 0x48
I2C_ADDR_LCD = 0x27

# Analog Channels (ADS1115)
CHAN_PH = 0    # Pin A0
CHAN_EC = 1    # Pin A1
CHAN_LEVEL = 2 # Pin A2

# Thresholds
TARGET_TEMP = 25.0      # °C
TEMP_LIMIT = 30.0       # Safety Cutoff
LIGHT_START_HOUR = 6    # 6 AM
LIGHT_END_HOUR = 20     # 8 PM

# Timers
WATER_DURATION = 300    # 5 Minutes ON
WATER_INTERVAL = 3600   # 1 Hour OFF
DOSE_DURATION = 1.5     # 1.5 Seconds dosing
DOSE_WAIT_TIME = 900    # 15 Minutes wait

# Chemistry
TARGET_PH = 6.0
PH_TOLERANCE = 0.5

# Safety
MIN_WATER_VOLTAGE = 1.5 # Tank Empty Limit