# GPIO Pin Mapping (BCM Mode)
RELAYS = {
    'water_pump': 5,    # Relay 1
    'light': 6,         # Relay 2
    'fan_1': 13,        # Relay 3
    'ph_down': 19,      # Relay 4
    'ph_up': 26,        # Relay 5
    'nutrient_a': 16,   # Relay 6
    'nutrient_b': 20,   # Relay 7
    'fan_2': 21         # Relay 8
}

# I2C Addresses
I2C_ADDR_BME280 = 0x76
I2C_ADDR_ADS1115 = 0x48

# Analog Channels (ADS1115)
CHAN_PH = 0    
CHAN_EC = 1    
CHAN_LEVEL = 2 

# --- INDIVIDUAL PUMP DURATIONS (Seconds) ---
PH_DOWN_DURATION = 1.2     
PH_UP_DURATION   = 1.5     
NUTRI_A_DURATION = 3.0     
NUTRI_B_DURATION = 3.0     

# --- SYSTEM TIMERS ---
WATER_DURATION = 300       # 15 Minutes ON
WATER_INTERVAL = 861000      #  OFF
DOSE_WAIT_TIME = 900       # 15 Minutes wait for mixing after any dose

# --- TARGETS & CALIBRATION ---
TARGET_TEMP = 25.0
TEMP_LIMIT = 30.0
LIGHT_START_HOUR = 6    
LIGHT_END_HOUR = 22     
TARGET_PH = 6.0
PH_TOLERANCE = 0.5
TARGET_EC = 1.2         
EC_TOLERANCE = 0.2

PH_SLOPE = -5.7706
PH_INTERCEPT = 15.8918
MIN_WATER_VOLTAGE = 0.5