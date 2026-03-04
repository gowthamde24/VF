# ==========================================
# GROW SMART OS - MAIN CONFIGURATION FILE
# ==========================================

# --- GPIO PIN MAPPING (BCM Mode) ---
RELAYS = {
    'water_pump': 23,   # Relay 1: Main recirculation pump
    'light': 5,         # Relay 2: LED Grow Lights
    'fan_1': 19,        # Relay 3: Intake/Cooling Fan
    'ph_down': 13,      # Relay 4: Peristaltic Pump (Acid)
    'ph_up': 26,        # Relay 5: Peristaltic Pump (Base)
    'nutrient_a': 16,   # Relay 6: Peristaltic Pump (FloraMicro)
    'nutrient_b': 20,   # Relay 7: Peristaltic Pump (FloraBloom)
    'fan_2': 24         # Relay 8: Exhaust Fan
}

# --- I2C ADDRESSES ---
I2C_ADDR_BME280 = 0x76  # Climate Sensor
I2C_ADDR_ADS1115 = 0x48 # Analog-to-Digital Converter

# --- ANALOG CHANNELS (ADS1115) ---
CHAN_PH = 0    
CHAN_EC = 1    
CHAN_LEVEL = 2

# --- SYSTEM TIMERS & DELAYS ---
STABILIZATION_PERIOD = 60   # Seconds to wait on boot before activating pumps/fail-safes
LOOP_DELAY = 2.0            # Seconds the main control loop sleeps between cycles
ADC_SETTLING_TIME = 0.05    # Seconds to pause between reading different analog sensors

# --- PUMP TIMERS (Seconds) ---
WATER_DURATION = 300        # 5 Minutes ON (Main Irrigation)
WATER_INTERVAL = 86100      # Time OFF between irrigation cycles
PH_DOWN_DURATION = 0.5      # Micro-dose duration (Diluted 10:1 recommended)
PH_UP_DURATION   = 0.5      # Micro-dose duration (Diluted 10:1 recommended)
NUTRI_A_DURATION = 2.0      # Micro-dose duration
NUTRI_B_DURATION = 2.0      # Micro-dose duration
PUMP_MIX_TIME = 150         # Seconds to actively run main pump after dosing to mix fluids
DOSE_WAIT_TIME = 900        # 15 Minutes total wait for chemical settling after ANY dose

# --- OPTIMAL TARGETS (Lettuce + Fenugreek Polyculture) ---
TARGET_TEMP = 23.0          # Turn fans on if air temp exceeds this
TARGET_HUMIDITY = 65.0      # Turn fans on if humidity exceeds this
LIGHT_START_HOUR = 6        # Hour to turn lights ON (24h format)
LIGHT_END_HOUR = 22         # Hour to turn lights OFF (24h format)
TARGET_PH = 6.2             # Polyculture Sweet Spot
PH_TOLERANCE = 0.5          # Wide Deadband (5.7 to 6.7) to prevent system oscillation
TARGET_EC = 1.35            # Polyculture Sweet Spot
EC_TOLERANCE = 0.2          # Allowed EC drift before dosing

# --- FAIL-SAFE & HARDWARE LIMITS ---
MAX_CONSECUTIVE_DOSES = 5   # Lockout pump if it doses X times without fixing the water
CRITICAL_TEMP_LIMIT = 32.0  # Instantly shut OFF lights if temp exceeds this
PH_CRITICAL_LOW = 3.0       # If pH reads below this, sensor is broken -> Lockout
PH_CRITICAL_HIGH = 10.0     # If pH reads above this, sensor is broken -> Lockout
EC_CRITICAL_LOW = 0.0       # If EC reads exactly 0, sensor is dry/broken -> Lockout
EC_CRITICAL_HIGH = 5.0      # If EC is this high, water is toxic/shorting -> Lockout

# --- DASHBOARD WARNING BOUNDS ---
PH_WARN_LOW = 5.5           # Triggers Yellow Warning on Dashboard
PH_WARN_HIGH = 6.8          # Triggers Yellow Warning on Dashboard
EC_WARN_LOW = 0.8           # Triggers Yellow Warning on Dashboard

# --- SENSOR CALIBRATION ---
PH_SLOPE = -5.7122
PH_INTERCEPT = 15.7309

# Water Level Calibration (Currently Disabled in Logic)
MIN_WATER_VOLTAGE = 0.2     # Voltage when tank is empty
MAX_WATER_VOLTAGE = 3.0     # Voltage when tank is 100% full