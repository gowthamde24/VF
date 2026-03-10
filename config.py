# # ==========================================
# # GROW SMART OS - PI 4 / 50L REVISION
# # ==========================================

# # --- GPIO PIN MAPPING (BCM Mode for Pi 4) ---
# RELAYS = {
#     'water_pump': 5,    # Relay 1: Main recirculation pump
#     'light': 6,         # Relay 2: LED Grow Lights
#     'fan_1': 13,        # Relay 3: Intake/Cooling Fan
#     'ph_down': 19,      # Relay 4: Peristaltic Pump (Acid)
#     'ph_up': 26,        # Relay 5: Peristaltic Pump (Base)
#     'nutrient_a': 21,   # Relay 6: Peristaltic Pump (FloraMicro)
#     'nutrient_b': 20,   # Relay 7: Peristaltic Pump (FloraBloom)
#     'fan_2': 16         # Relay 8: Exhaust Fan
# }

# # --- I2C ADDRESSES ---
# I2C_ADDR_BME280 = 0x76  # Climate Sensor
# I2C_ADDR_ADS1115 = 0x48 # Analog-to-Digital Converter

# # --- DIFFERENTIAL ANALOG MAPPING ---
# # pH: Differential between A0 and A3 (Signal on A0, Ref on A3)
# # EC: Single-ended on A1
# CHAN_PH_POS = 0    
# CHAN_PH_NEG = 3    
# CHAN_EC = 1   
# CHAN_LEVEL = 2     

# # --- SYSTEM TIMERS & DELAYS ---
# STABILIZATION_PERIOD = 60   # Seconds to wait on boot before activating pumps/fail-safes
# LOOP_DELAY = 2.0            # Seconds the main control loop sleeps between cycles
# ADC_SETTLING_TIME = 0.05    # Seconds to pause between reading different analog sensors

# # --- 50L PUMP TIMERS (Seconds) ---
# WATER_DURATION = 300        # 5 Minutes ON (Main Irrigation)
# WATER_INTERVAL = 86100      # Time OFF between irrigation cycles

# # Values increased for 50L dilution
# PH_DOWN_DURATION = 1.0      # Acid pulse duration
# PH_UP_DURATION   = 1.0      # Base pulse duration
# NUTRI_A_DURATION = 1.0      # Part A pulse duration
# NUTRI_B_DURATION = 1.0      # Part B pulse duration

# PUMP_MIX_TIME = 180         # 3 minutes of active mixing after dosing
# DOSE_WAIT_TIME = 1500       # 25 minutes total wait for chemical settling after ANY dose in 50L

# # --- OPTIMAL TARGETS (Lettuce + Fenugreek Polyculture) ---
# TARGET_TEMP = 23.0          # The ideal cooled temperature (Lower Limit 'A')
# TEMP_TOLERANCE = 4.0        # Drift allowed before fans turn on (Upper Limit 'B' = 25.0C)
# TARGET_HUMIDITY = 60.0      # The ideal humidity 
# HUM_TOLERANCE = 10.0         # Drift allowed before fans turn on (Max = 65.0%)
# LIGHT_START_HOUR = 6        # Hour to turn lights ON (24h format)
# LIGHT_END_HOUR = 22         # Hour to turn lights OFF (24h format)

# TARGET_PH = 6.2             # Polyculture Sweet Spot
# PH_TOLERANCE = 0.7          # Safe range: 5.9 - 6.5
# TARGET_EC = 1.2            # Polyculture Sweet Spot
# EC_TOLERANCE = 0.5         # Safe range: 1.2 - 1.5

# # --- FAIL-SAFE & HARDWARE LIMITS ---
# MAX_CONSECUTIVE_DOSES = 5   # Lockout pump if it doses X times without fixing the water
# CRITICAL_TEMP_LIMIT = 32.0  # Instantly shut OFF lights if temp exceeds this
# PH_CRITICAL_LOW = 3.0       # If pH reads below this, sensor is broken -> Lockout
# PH_CRITICAL_HIGH = 10.0     # If pH reads above this, sensor is broken -> Lockout
# EC_CRITICAL_LOW = 0.0       # If EC reads exactly 0, sensor is dry/broken -> Lockout
# EC_CRITICAL_HIGH = 5.0      # If EC is this high, water is toxic/shorting -> Lockout

# # --- DASHBOARD WARNING BOUNDS ---
# PH_WARN_LOW = 5.0           # Triggers Yellow Warning on Dashboard
# PH_WARN_HIGH = 8.0          # Triggers Yellow Warning on Dashboard
# EC_WARN_LOW = 0.5           # Triggers Yellow Warning on Dashboard

# # --- SENSOR CALIBRATION ---
# PH_SLOPE = -5.7706          # Updated from research project calibration
# PH_INTERCEPT = 15.8918      # Updated from research project calibration
# EC_MULTIPLIER = 0.608         # Adjusted during calibration


# ==========================================
# GROW SMART OS - PI 4 / 50L REVISION
# ==========================================

# --- GPIO PIN MAPPING (BCM Mode for Pi 4) ---
RELAYS = {
    'water_pump': 5,    # Relay 1: Main recirculation pump
    'light': 6,         # Relay 2: LED Grow Lights
    'fan_1': 13,        # Relay 3: Intake/Cooling Fan
    'ph_down': 19,      # Relay 4: Peristaltic Pump (Acid)
    'ph_up': 26,        # Relay 5: Peristaltic Pump (Base)
    'nutrient_a': 21,   # Relay 6: Peristaltic Pump (FloraMicro)
    'nutrient_b': 20,   # Relay 7: Peristaltic Pump (FloraBloom)
    'fan_2': 16         # Relay 8: Exhaust Fan
}

# --- NEW: Digital Sensor Mapping ---
# Non-contact sensor on GPIO 17 (3.3V Power)
WATER_LEVEL_PIN = 17 

# --- I2C ADDRESSES ---
I2C_ADDR_BME280 = 0x76  
I2C_ADDR_ADS1115 = 0x48 

# --- DIFFERENTIAL ANALOG MAPPING ---
# pH: Differential between A0 and A3 (Signal on A0, Ref on A3)
# EC: Single-ended on A1
CHAN_PH_POS = 0    
CHAN_PH_NEG = 3    
CHAN_EC = 1   

# --- SYSTEM TIMERS & DELAYS ---
STABILIZATION_PERIOD = 60   
LOOP_DELAY = 2.0            
ADC_SETTLING_TIME = 0.05    

# --- 50L PUMP TIMERS (Seconds) ---
WATER_DURATION = 300        
WATER_INTERVAL = 86100      

PH_DOWN_DURATION = 1.0      
PH_UP_DURATION   = 1.0      
NUTRI_A_DURATION = 1.0      
NUTRI_B_DURATION = 1.0      

PUMP_MIX_TIME = 180         
DOSE_WAIT_TIME = 1500       

# --- OPTIMAL TARGETS (Lettuce + Fenugreek Polyculture) ---
TARGET_TEMP = 23.0          
TEMP_TOLERANCE = 4.0        
TARGET_HUMIDITY = 60.0      
HUM_TOLERANCE = 10.0         
LIGHT_START_HOUR = 6        
LIGHT_END_HOUR = 22         

TARGET_PH = 6.2             
PH_TOLERANCE = 0.7          
TARGET_EC = 1.2            
EC_TOLERANCE = 0.5         

# --- FAIL-SAFE & HARDWARE LIMITS ---
MAX_CONSECUTIVE_DOSES = 5   
CRITICAL_TEMP_LIMIT = 32.0  
PH_CRITICAL_LOW = 3.0       
PH_CRITICAL_HIGH = 10.0     
EC_CRITICAL_LOW = 0.0       
EC_CRITICAL_HIGH = 5.0      

# --- DASHBOARD WARNING BOUNDS ---
PH_WARN_LOW = 5.0           
PH_WARN_HIGH = 8.0          
EC_WARN_LOW = 0.5           

# --- SENSOR CALIBRATION ---
PH_SLOPE = -5.7706          
PH_INTERCEPT = 15.8918      
EC_MULTIPLIER = 0.608