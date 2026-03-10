


# import time
# import json
# import threading
# import http.server
# import socketserver
# import os
# import csv
# from datetime import datetime
# import config

# # --- NATIVE RASPBERRY PI IMPORTS ---
# import RPi.GPIO as GPIO
# import board
# import busio
# import adafruit_ads1x15.ads1115 as ADS
# from adafruit_ads1x15.analog_in import AnalogIn
# from adafruit_bme280 import basic as adafruit_bme280

# # --- WEB SERVER LOGIC ---
# def start_web_server():
#     PORT = 8000
#     class QuietHandler(http.server.SimpleHTTPRequestHandler):
#         def log_message(self, format, *args): pass
            
#     try:
#         with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
#             print(f"-> Web Server Running: http://localhost:{PORT}")
#             httpd.serve_forever()
#     except OSError:
#         pass

# # --- SETUP ---
# print("System Booting (Robust Auto Mode - 50L Single-Ended Revision)...")

# GPIO.setmode(GPIO.BCM)
# GPIO.setwarnings(False)

# for name, pin in config.RELAYS.items():
#     GPIO.setup(pin, GPIO.OUT)
#     GPIO.output(pin, GPIO.HIGH) # HIGH is OFF for these relays

# # Setup Digital Water Level Sensor (LED ON = HIGH = FULL)
# GPIO.setup(config.WATER_LEVEL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# i2c = busio.I2C(board.SCL, board.SDA)

# bme280 = None
# try:
#     bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
#     print("-> Climate Sensor connected.")
# except Exception as e:
#     print(f"! Climate Sensor Error: {e}")

# ads, ph_chan, ec_chan = None, None, None
# try:
#     ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
    
#     # --- EMI FIX: Single-Ended Mode to prevent I2C bus crashes ---
#     ph_chan = AnalogIn(ads, config.CHAN_PH)
#     ec_chan = AnalogIn(ads, config.CHAN_EC)
#     print("-> Chemistry ADC connected (Single-Ended Mode).")
# except Exception as e:
#     print(f"! ADC Analog Error: {e}")

# threading.Thread(target=start_web_server, daemon=True).start()

# # --- STATE VARIABLES & COUNTERS ---
# system_start_time = time.time()
# last_water_time = time.time()
# last_dose_time = 0
# is_watering = False
# water_start_time = 0
# fan_active = False
# consecutive_ph_doses = 0
# consecutive_ec_doses = 0

# def evaluate_system_health(t, ph, ec, water_ok):
#     """Evaluates system health based on bounds defined in config.py"""
#     health_score = 100
#     status = "OPTIMAL"
#     prediction = "Rule-Based System Active"
#     safe_mode = False

#     # 1. Water Level Critical Fail-Safe
#     if not water_ok:
#         health_score = 20
#         status = "CRITICAL"
#         prediction = "FAIL-SAFE: LOW WATER. Pumps DISABLED."
#         safe_mode = True

#     # 2. Broken Sensor Fail-Safe
#     elif ph < config.PH_CRITICAL_LOW or ph > config.PH_CRITICAL_HIGH:
#         health_score = 10
#         status = "CRITICAL"
#         prediction = "FAIL-SAFE: pH Sensor Error. Chemical Pumps DISABLED."
#         safe_mode = True
#     elif ec <= config.EC_CRITICAL_LOW or ec > config.EC_CRITICAL_HIGH:
#         health_score = 10
#         status = "CRITICAL"
#         prediction = "FAIL-SAFE: EC Sensor Error. Nutrient Pumps DISABLED."
#         safe_mode = True
        
#     # 3. Thermal Fail-Safe
#     elif t > config.CRITICAL_TEMP_LIMIT:
#         health_score = 40
#         status = "WARNING"
#         prediction = f"FAIL-SAFE: Temp > {config.CRITICAL_TEMP_LIMIT}C. Overheating Risk."
#         safe_mode = True

#     # 4. Chemical Imbalance Warnings
#     elif ph < config.PH_WARN_LOW or ph > config.PH_WARN_HIGH:
#         health_score = 60
#         status = "WARNING"
#         prediction = "pH out of safe bounds."
#     elif ec < config.EC_WARN_LOW:
#         health_score = 70
#         status = "WARNING"
#         prediction = "Nutrients Low."

#     return safe_mode, {"health_score": health_score, "status": status, "prediction": prediction}


# def update_dashboard_file(temp, hum, ph, ec, water_lvl, light_s, fan_s, pump_s, safety_s, activity_s, sys_health):
#     data = {
#         "timestamp": datetime.now().strftime('%H:%M:%S'),
#         "temp": temp, "hum": hum, "ph": ph, "ec": ec, "water_level": water_lvl, 
#         "light_state": light_s, "fan_state": fan_s, "pump_state": pump_s,
#         "safety": safety_s, "activity": activity_s,
#         "ml": sys_health 
#     }
#     try:
#         with open("dashboard.json", "w") as f:
#             json.dump(data, f)
#     except: pass

# def log_data_to_csv(temp, hum, ph, ec, water_lvl, light_s, fan_s, pump_s, safety_s, activity_s, sys_health):
#     file_name = "system_log.csv"
#     file_exists = os.path.isfile(file_name)
#     pred = sys_health["prediction"]
    
#     try:
#         with open(file_name, mode='a', newline='') as file:
#             writer = csv.writer(file)
#             if not file_exists:
#                 writer.writerow(['Timestamp', 'Temp_C', 'Humidity_%', 'pH', 'EC', 'Water_Level_%', 'Light', 'Fans', 'Pump', 'Safety', 'Activity', 'System_Message'])
            
#             writer.writerow([
#                 datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                 temp, hum, ph, ec, water_lvl, light_s, fan_s, pump_s, safety_s, activity_s, pred
#             ])
#     except: pass

# def run_control_loop():
#     global last_water_time, last_dose_time, is_watering, water_start_time
#     global consecutive_ph_doses, consecutive_ec_doses, fan_active
    
#     # --- 1. READ SENSORS ---
#     t, h = (25.0, 50.0)
#     if bme280: 
#         try:
#             t = round(bme280.temperature, 1)
#             h = round(bme280.relative_humidity, 0)
#         except: pass
    
#     # Digital Water Level Logic
#     water_ok = (GPIO.input(config.WATER_LEVEL_PIN) == GPIO.HIGH)
#     water_level_pct = 100.0 if water_ok else 10.0

#     ph_val = 6.0 
#     if ph_chan:
#         # --- EMI FIX: Aggressive 100-Sample Oversampling ---
#         # Replaces hardware differential mode to prevent crashes
#         try:
#             ph_voltages = []
#             for _ in range(100):
#                 ph_voltages.append(ph_chan.voltage)
#                 time.sleep(0.005) # Small pause
            
#             # Sort the voltages and throw away the 20 highest and 20 lowest (Outlier Removal)
#             ph_voltages.sort()
#             stable_voltages = ph_voltages[20:-20] 
            
#             avg_v = sum(stable_voltages) / len(stable_voltages)
#             ph_val = round((config.PH_SLOPE * avg_v) + config.PH_INTERCEPT, 2)
#             time.sleep(config.ADC_SETTLING_TIME)
#         except: ph_val = -1.0

#     ec_val = 1.2 
#     if ec_chan:
#         # Oversampling Filter for EC Stability
#         try:
#             ec_voltages = []
#             for _ in range(10):
#                 ec_voltages.append(ec_chan.voltage)
#                 time.sleep(0.02)
                
#             avg_ec_v = sum(ec_voltages) / len(ec_voltages)
#             ec_val = round(avg_ec_v * config.EC_MULTIPLIER, 2)
#         except: ec_val = -1.0

#     now = datetime.now()
#     cur_time = time.time()

#     # --- 1.5 STABILIZATION PHASE ---
#     if cur_time - system_start_time < config.STABILIZATION_PERIOD:
#         remaining_time = int(config.STABILIZATION_PERIOD - (cur_time - system_start_time))
#         current_activity = f"Sensor Stabilization ({remaining_time}s)"
#         sys_health = {"health_score": 100, "status": "STARTUP", "prediction": "Waiting for sensors to stabilize..."}
        
#         update_dashboard_file(t, h, ph_val, ec_val, water_level_pct, "OFF", "OFF", "OFF", "STARTUP", current_activity, sys_health)
#         print(f"[{now.strftime('%H:%M:%S')}] {current_activity} | T:{t}°C pH:{ph_val} EC:{ec_val} W:{'OK' if water_ok else 'LOW'}      ", end='\r')
#         return

#     # --- 2. FAIL-SAFE EVALUATION ---
#     safe_mode, sys_health = evaluate_system_health(t, ph_val, ec_val, water_ok)
#     safety_str = "SAFE MODE" if safe_mode else "OK"
    
#     light_state, fan_state, pump_state = "OFF", "OFF", "OFF"
#     current_activity = "Monitoring"

#     # --- 3. LIGHTS ---
#     if config.LIGHT_START_HOUR <= now.hour < config.LIGHT_END_HOUR and t < config.CRITICAL_TEMP_LIMIT:
#         GPIO.output(config.RELAYS['light'], GPIO.LOW)
#         light_state = "ON"
#     else:
#         GPIO.output(config.RELAYS['light'], GPIO.HIGH)

#     # --- 4. FANS (With Hysteresis Deadband) ---
#     if t > (config.TARGET_TEMP + config.TEMP_TOLERANCE) or h > (config.TARGET_HUMIDITY + config.HUM_TOLERANCE):
#         fan_active = True
#     elif t <= config.TARGET_TEMP and h <= config.TARGET_HUMIDITY:
#         fan_active = False

#     if fan_active:
#         GPIO.output(config.RELAYS['fan_1'], GPIO.LOW)
#         GPIO.output(config.RELAYS['fan_2'], GPIO.LOW)
#         fan_state = "ON"
#         current_activity = "Cooling/Dehumidifying"
#     else:
#         GPIO.output(config.RELAYS['fan_1'], GPIO.HIGH)
#         GPIO.output(config.RELAYS['fan_2'], GPIO.HIGH)

#     # --- 5. WATER CYCLE (Safety Locked) ---
#     if water_ok:
#         if not is_watering and (cur_time - last_water_time > config.WATER_INTERVAL):
#             is_watering = True
#             water_start_time = cur_time
#             GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
#         elif is_watering and (cur_time - water_start_time > config.WATER_DURATION):
#             is_watering = False
#             last_water_time = cur_time
#             GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
#     else:
#         # Force Pump OFF if water is low
#         is_watering = False
#         GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
    
#     if is_watering: 
#         pump_state = "ON"
#         if not safe_mode: current_activity = "Irrigation"

#     # --- 6. FAIL-SAFE CHEMICAL DOSING ---
#     # Only allow dosing if Safe Mode is OFF AND Water is OK
#     if not safe_mode and water_ok and (cur_time - last_dose_time > config.DOSE_WAIT_TIME):
#         dosed = False
        
#         # pH Down
#         if ph_val > (config.TARGET_PH + config.PH_TOLERANCE):
#             if consecutive_ph_doses < config.MAX_CONSECUTIVE_DOSES:
#                 current_activity = "Dosing: pH Down (Mixing...)" 
#                 pump_state = "ON"
#                 update_dashboard_file(t, h, ph_val, ec_val, water_level_pct, light_state, fan_state, pump_state, safety_str, current_activity, sys_health)
                
#                 GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
#                 GPIO.output(config.RELAYS['ph_down'], GPIO.LOW)
#                 time.sleep(config.PH_DOWN_DURATION)
#                 GPIO.output(config.RELAYS['ph_down'], GPIO.HIGH)
                
#                 time.sleep(config.PUMP_MIX_TIME)
#                 if not is_watering: GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
#                 dosed = True
#                 consecutive_ph_doses += 1
#             else:
#                 current_activity = "FAIL-SAFE: pH Pump Locked."
                
#         # pH Up
#         elif ph_val < (config.TARGET_PH - config.PH_TOLERANCE):
#             if consecutive_ph_doses < config.MAX_CONSECUTIVE_DOSES:
#                 current_activity = "Dosing: pH Up (Mixing...)" 
#                 pump_state = "ON"
#                 update_dashboard_file(t, h, ph_val, ec_val, water_level_pct, light_state, fan_state, pump_state, safety_str, current_activity, sys_health)
                
#                 GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
#                 GPIO.output(config.RELAYS['ph_up'], GPIO.LOW)
#                 time.sleep(config.PH_UP_DURATION)
#                 GPIO.output(config.RELAYS['ph_up'], GPIO.HIGH)
                
#                 time.sleep(config.PUMP_MIX_TIME)
#                 if not is_watering: GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
#                 dosed = True
#                 consecutive_ph_doses += 1
#             else:
#                 current_activity = "FAIL-SAFE: pH Pump Locked."
#         else:
#             consecutive_ph_doses = 0 

#         # Nutrients
#         if not dosed and ec_val < (config.TARGET_EC - config.EC_TOLERANCE):
#             if consecutive_ec_doses < config.MAX_CONSECUTIVE_DOSES:
#                 current_activity = "Dosing: Nutrients (Mixing...)" 
#                 pump_state = "ON"
#                 update_dashboard_file(t, h, ph_val, ec_val, water_level_pct, light_state, fan_state, pump_state, safety_str, current_activity, sys_health)
                
#                 GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
#                 GPIO.output(config.RELAYS['nutrient_a'], GPIO.LOW)
#                 time.sleep(config.NUTRI_A_DURATION)
#                 GPIO.output(config.RELAYS['nutrient_a'], GPIO.HIGH)
#                 time.sleep(1)
#                 GPIO.output(config.RELAYS['nutrient_b'], GPIO.LOW)
#                 time.sleep(config.NUTRI_B_DURATION)
#                 GPIO.output(config.RELAYS['nutrient_b'], GPIO.HIGH)
                
#                 time.sleep(config.PUMP_MIX_TIME)
#                 if not is_watering: GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
#                 dosed = True
#                 consecutive_ec_doses += 1
#             else:
#                 current_activity = "FAIL-SAFE: EC Pump Locked."
#         else:
#             consecutive_ec_doses = 0 
            
#         if dosed: 
#             last_dose_time = cur_time

#     # --- 7. EXPORT & CONSOLE LOG ---
#     if safe_mode: current_activity = sys_health["prediction"]
#     update_dashboard_file(t, h, ph_val, ec_val, water_level_pct, light_state, fan_state, pump_state, safety_str, current_activity, sys_health)
#     log_data_to_csv(t, h, ph_val, ec_val, water_level_pct, light_state, fan_state, pump_state, safety_str, current_activity, sys_health)
    
#     print(f"[{now.strftime('%H:%M:%S')}] {current_activity: <25} | T:{t}°C pH:{ph_val} EC:{ec_val} (SF:{consecutive_ph_doses}) W:{'OK' if water_ok else 'LOW'}      ", end='\r')

# # --- MAIN EXECUTION ---
# try:
#     while True:
#         run_control_loop()
#         time.sleep(config.LOOP_DELAY)
# except KeyboardInterrupt:
#     print("\nShutting down... turning off all relays.")
#     GPIO.cleanup()


import time
import json
import threading
import http.server
import socketserver
import os
import csv
from datetime import datetime
import config

# --- NATIVE RASPBERRY PI IMPORTS ---
import RPi.GPIO as GPIO
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_bme280 import basic as adafruit_bme280

# --- WEB SERVER LOGIC ---
def start_web_server():
    PORT = 8000
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args): pass
            
    try:
        with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
            print(f"-> Web Server Running: http://localhost:{PORT}")
            httpd.serve_forever()
    except OSError:
        pass

# --- SETUP ---
print("System Booting (Robust Auto Mode - 50L Single-Ended | EC DISABLED)...")

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for name, pin in config.RELAYS.items():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH) # HIGH is OFF for these relays

# Setup Digital Water Level Sensor (LED ON = HIGH = FULL)
GPIO.setup(config.WATER_LEVEL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

i2c = busio.I2C(board.SCL, board.SDA)

bme280 = None
try:
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
    print("-> Climate Sensor connected.")
except Exception as e:
    print(f"! Climate Sensor Error: {e}")

ads, ph_chan = None, None
# ec_chan is completely disabled for now
try:
    ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
    
    # --- EMI FIX: Single-Ended Mode ---
    ph_chan = AnalogIn(ads, config.CHAN_PH)
    # ec_chan = AnalogIn(ads, config.CHAN_EC) # Disabled
    print("-> Chemistry ADC connected (pH Only - EC Disabled).")
except Exception as e:
    print(f"! ADC Analog Error: {e}")

threading.Thread(target=start_web_server, daemon=True).start()

# --- STATE VARIABLES & COUNTERS ---
system_start_time = time.time()
last_water_time = time.time()
last_dose_time = 0
is_watering = False
water_start_time = 0
fan_active = False
consecutive_ph_doses = 0

def evaluate_system_health(t, ph, water_ok):
    """Evaluates system health based on bounds defined in config.py. EC bypassed."""
    health_score = 100
    status = "OPTIMAL"
    prediction = "Rule-Based System Active"
    safe_mode = False

    # 1. Water Level Critical Fail-Safe
    if not water_ok:
        health_score = 20
        status = "CRITICAL"
        prediction = "FAIL-SAFE: LOW WATER. Pumps DISABLED."
        safe_mode = True

    # 2. Broken Sensor Fail-Safe (pH Only)
    elif ph < config.PH_CRITICAL_LOW or ph > config.PH_CRITICAL_HIGH:
        health_score = 10
        status = "CRITICAL"
        prediction = "FAIL-SAFE: pH Sensor Error. Chemical Pumps DISABLED."
        safe_mode = True
        
    # 3. Thermal Fail-Safe
    elif t > config.CRITICAL_TEMP_LIMIT:
        health_score = 40
        status = "WARNING"
        prediction = f"FAIL-SAFE: Temp > {config.CRITICAL_TEMP_LIMIT}C. Overheating Risk."
        safe_mode = True

    # 4. Chemical Imbalance Warnings (pH Only)
    elif ph < config.PH_WARN_LOW or ph > config.PH_WARN_HIGH:
        health_score = 60
        status = "WARNING"
        prediction = "pH out of safe bounds."

    return safe_mode, {"health_score": health_score, "status": status, "prediction": prediction}


def update_dashboard_file(temp, hum, ph, ec, water_lvl, light_s, fan_s, pump_s, safety_s, activity_s, sys_health):
    data = {
        "timestamp": datetime.now().strftime('%H:%M:%S'),
        "temp": temp, "hum": hum, "ph": ph, "ec": ec, "water_level": water_lvl, 
        "light_state": light_s, "fan_state": fan_s, "pump_state": pump_s,
        "safety": safety_s, "activity": activity_s,
        "ml": sys_health 
    }
    try:
        with open("dashboard.json", "w") as f:
            json.dump(data, f)
    except: pass

def log_data_to_csv(temp, hum, ph, ec, water_lvl, light_s, fan_s, pump_s, safety_s, activity_s, sys_health):
    file_name = "system_log.csv"
    file_exists = os.path.isfile(file_name)
    pred = sys_health["prediction"]
    
    try:
        with open(file_name, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Timestamp', 'Temp_C', 'Humidity_%', 'pH', 'EC', 'Water_Level_%', 'Light', 'Fans', 'Pump', 'Safety', 'Activity', 'System_Message'])
            
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                temp, hum, ph, ec, water_lvl, light_s, fan_s, pump_s, safety_s, activity_s, pred
            ])
    except: pass

def run_control_loop():
    global last_water_time, last_dose_time, is_watering, water_start_time
    global consecutive_ph_doses, fan_active
    
    # --- 1. READ SENSORS ---
    t, h = (25.0, 50.0)
    if bme280: 
        try:
            t = round(bme280.temperature, 1)
            h = round(bme280.relative_humidity, 0)
        except: pass
    
    # Digital Water Level Logic
    water_ok = (GPIO.input(config.WATER_LEVEL_PIN) == GPIO.HIGH)
    water_level_pct = 100.0 if water_ok else 10.0

    ph_val = 6.0 
    if ph_chan:
        # --- EMI FIX: Aggressive 100-Sample Oversampling ---
        try:
            ph_voltages = []
            for _ in range(100):
                ph_voltages.append(ph_chan.voltage)
                time.sleep(0.005) # Small pause
            
            # Sort the voltages and throw away the 20 highest and 20 lowest (Outlier Removal)
            ph_voltages.sort()
            stable_voltages = ph_voltages[20:-20] 
            
            avg_v = sum(stable_voltages) / len(stable_voltages)
            ph_val = round((config.PH_SLOPE * avg_v) + config.PH_INTERCEPT, 2)
            time.sleep(config.ADC_SETTLING_TIME)
        except: ph_val = -1.0

    # EC Disabled completely
    ec_val = 0.0

    now = datetime.now()
    cur_time = time.time()

    # --- 1.5 STABILIZATION PHASE ---
    if cur_time - system_start_time < config.STABILIZATION_PERIOD:
        remaining_time = int(config.STABILIZATION_PERIOD - (cur_time - system_start_time))
        current_activity = f"Sensor Stabilization ({remaining_time}s)"
        sys_health = {"health_score": 100, "status": "STARTUP", "prediction": "Waiting for sensors to stabilize..."}
        
        update_dashboard_file(t, h, ph_val, ec_val, water_level_pct, "OFF", "OFF", "OFF", "STARTUP", current_activity, sys_health)
        print(f"[{now.strftime('%H:%M:%S')}] {current_activity} | T:{t}°C pH:{ph_val} EC:DISABLED W:{'OK' if water_ok else 'LOW'}      ", end='\r')
        return

    # --- 2. FAIL-SAFE EVALUATION ---
    safe_mode, sys_health = evaluate_system_health(t, ph_val, water_ok)
    safety_str = "SAFE MODE" if safe_mode else "OK"
    
    light_state, fan_state, pump_state = "OFF", "OFF", "OFF"
    current_activity = "Monitoring"

    # --- 3. LIGHTS ---
    if config.LIGHT_START_HOUR <= now.hour < config.LIGHT_END_HOUR and t < config.CRITICAL_TEMP_LIMIT:
        GPIO.output(config.RELAYS['light'], GPIO.LOW)
        light_state = "ON"
    else:
        GPIO.output(config.RELAYS['light'], GPIO.HIGH)

    # --- 4. FANS (With Hysteresis Deadband) ---
    if t > (config.TARGET_TEMP + config.TEMP_TOLERANCE) or h > (config.TARGET_HUMIDITY + config.HUM_TOLERANCE):
        fan_active = True
    elif t <= config.TARGET_TEMP and h <= config.TARGET_HUMIDITY:
        fan_active = False

    if fan_active:
        GPIO.output(config.RELAYS['fan_1'], GPIO.LOW)
        GPIO.output(config.RELAYS['fan_2'], GPIO.LOW)
        fan_state = "ON"
        current_activity = "Cooling/Dehumidifying"
    else:
        GPIO.output(config.RELAYS['fan_1'], GPIO.HIGH)
        GPIO.output(config.RELAYS['fan_2'], GPIO.HIGH)

    # --- 5. WATER CYCLE (Safety Locked) ---
    if water_ok:
        if not is_watering and (cur_time - last_water_time > config.WATER_INTERVAL):
            is_watering = True
            water_start_time = cur_time
            GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
        elif is_watering and (cur_time - water_start_time > config.WATER_DURATION):
            is_watering = False
            last_water_time = cur_time
            GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
    else:
        # Force Pump OFF if water is low
        is_watering = False
        GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
    
    if is_watering: 
        pump_state = "ON"
        if not safe_mode: current_activity = "Irrigation"

    # --- 6. FAIL-SAFE CHEMICAL DOSING ---
    # Only allow dosing if Safe Mode is OFF AND Water is OK
    if not safe_mode and water_ok and (cur_time - last_dose_time > config.DOSE_WAIT_TIME):
        dosed = False
        
        # pH Down
        if ph_val > (config.TARGET_PH + config.PH_TOLERANCE):
            if consecutive_ph_doses < config.MAX_CONSECUTIVE_DOSES:
                current_activity = "Dosing: pH Down (Mixing...)" 
                pump_state = "ON"
                update_dashboard_file(t, h, ph_val, ec_val, water_level_pct, light_state, fan_state, pump_state, safety_str, current_activity, sys_health)
                
                GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
                GPIO.output(config.RELAYS['ph_down'], GPIO.LOW)
                time.sleep(config.PH_DOWN_DURATION)
                GPIO.output(config.RELAYS['ph_down'], GPIO.HIGH)
                
                time.sleep(config.PUMP_MIX_TIME)
                if not is_watering: GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
                dosed = True
                consecutive_ph_doses += 1
            else:
                current_activity = "FAIL-SAFE: pH Pump Locked."
                
        # pH Up
        elif ph_val < (config.TARGET_PH - config.PH_TOLERANCE):
            if consecutive_ph_doses < config.MAX_CONSECUTIVE_DOSES:
                current_activity = "Dosing: pH Up (Mixing...)" 
                pump_state = "ON"
                update_dashboard_file(t, h, ph_val, ec_val, water_level_pct, light_state, fan_state, pump_state, safety_str, current_activity, sys_health)
                
                GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
                GPIO.output(config.RELAYS['ph_up'], GPIO.LOW)
                time.sleep(config.PH_UP_DURATION)
                GPIO.output(config.RELAYS['ph_up'], GPIO.HIGH)
                
                time.sleep(config.PUMP_MIX_TIME)
                if not is_watering: GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
                dosed = True
                consecutive_ph_doses += 1
            else:
                current_activity = "FAIL-SAFE: pH Pump Locked."
        else:
            consecutive_ph_doses = 0 

        # Nutrients (DISABLED)
        # Nutrient dosing is skipped completely until EC is calibrated.
            
        if dosed: 
            last_dose_time = cur_time

    # --- 7. EXPORT & CONSOLE LOG ---
    if safe_mode: current_activity = sys_health["prediction"]
    update_dashboard_file(t, h, ph_val, ec_val, water_level_pct, light_state, fan_state, pump_state, safety_str, current_activity, sys_health)
    log_data_to_csv(t, h, ph_val, ec_val, water_level_pct, light_state, fan_state, pump_state, safety_str, current_activity, sys_health)
    
    # Terminal Output changed to show "EC:DISABLED"
    print(f"[{now.strftime('%H:%M:%S')}] {current_activity: <25} | T:{t}°C pH:{ph_val} EC:DISABLED (SF:{consecutive_ph_doses}) W:{'OK' if water_ok else 'LOW'}      ", end='\r')

# --- MAIN EXECUTION ---
try:
    while True:
        run_control_loop()
        time.sleep(config.LOOP_DELAY)
except KeyboardInterrupt:
    print("\nShutting down... turning off all relays.")
    GPIO.cleanup()