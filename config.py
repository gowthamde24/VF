
# ==========================================
# GROW SMART OS - PI 4 / 50L REVISION
# ==========================================

# --- GPIO PIN MAPPING (BCM Mode for Pi 4) ---
RELAYS = {
    'water_pump': 5,    # Relay 1: Main recirculation pump
    'light': 21,         # Relay 2: LED Grow Lights
    'fan_1': 16,        # Relay 3:Exhaust Fan
    'ph_down': 19,      # Relay 4: Peristaltic Pump (Acid)
    'ph_up': 13,        # Relay 5: Peristaltic Pump (Base)
    'nutrient_a': 26,   # Relay 6: Peristaltic Pump (FloraMicro)
    'nutrient_b': 6,   # Relay 7: Peristaltic Pump (FloraBloom)
    'fan_2': 20         # Relay 8: Intake Fan
}

# --- NEW: Digital Sensor Mapping ---
# Non-contact sensor on GPIO 17 (3.3V Power)
WATER_LEVEL_PIN = 22 

# --- I2C ADDRESSES ---
I2C_ADDR_BME280 = 0x76  
I2C_ADDR_ADS1115 = 0x48 

# --- ANALOG MAPPING (REVISED) ---
# A2 and A3 are unused to prevent I2C bus crashes
CHAN_PH = 0    
CHAN_EC = 2   

# --- SYSTEM TIMERS & DELAYS ---
STABILIZATION_PERIOD = 60   
LOOP_DELAY = 2.0            
ADC_SETTLING_TIME = 0.05    

# --- 50L PUMP TIMERS (Seconds) ---
WATER_DURATION = 600        
WATER_INTERVAL = 600      

PH_DOWN_DURATION = 0.5      
PH_UP_DURATION   = 0.5      

NUTRI_A_DURATION = 0.5      
NUTRI_B_DURATION = 0.5      

PUMP_MIX_TIME = 180         
DOSE_WAIT_TIME = 1500       

# --- OPTIMAL TARGETS ---
TARGET_TEMP = 24.0          
TEMP_TOLERANCE = 4.0        
TARGET_HUMIDITY = 40.0      
HUM_TOLERANCE = 10.0         
LIGHT_START_HOUR = 6        
LIGHT_END_HOUR = 24         

TARGET_PH = 6.0             
PH_TOLERANCE = 1.0         
TARGET_EC = 1.0           
EC_TOLERANCE = 0.5         

# --- FAIL-SAFE & HARDWARE LIMITS ---
MAX_CONSECUTIVE_DOSES = 5   
CRITICAL_TEMP_LIMIT = 32.0  
PH_CRITICAL_LOW = 3.0       
PH_CRITICAL_HIGH = 10.0     
EC_CRITICAL_LOW = 0.0       
EC_CRITICAL_HIGH = 5.0      

# --- SENSOR CALIBRATION ---
PH_SLOPE = 3.8967          
PH_INTERCEPT = -4.9505      
EC_MULTIPLIER = 0.608

