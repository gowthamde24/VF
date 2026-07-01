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

# --- NEW: EC POWER PIN (MOVED TO 27 TO AVOID RELAY CONFLICT) ---
EC_POWER_PIN = 27 

# --- WEB SERVER LOGIC ---
def start_web_server():
    PORT = 8000
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args): pass
        
        # Tell the browser NEVER to cache the data
        def end_headers(self):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            super().end_headers()
            
    try:
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
            print(f"-> Web Server Running: http://localhost:{PORT}")
            httpd.serve_forever()
    except OSError:
        pass

# --- SETUP ---
print("System Booting (Robust Auto Mode - 50L | SOFTWARE ISOLATION ENABLED)...")

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for name, pin in config.RELAYS.items():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH) # HIGH is OFF for these Active-Low relays

# Setup Digital Water Level Sensor & EC Power Pin
# PUD_UP pulls the pin HIGH when the NPN NC sensor floats (detects water)
GPIO.setup(config.WATER_LEVEL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(EC_POWER_PIN, GPIO.OUT, initial=GPIO.LOW)

i2c = busio.I2C(board.SCL, board.SDA)

bme280 = None
try:
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
    print("-> Climate Sensor connected.")
except Exception as e:
    print(f"! Climate Sensor Error: {e}")

ads, ph_chan, ec_chan = None, None, None
try:
    ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
    # Set gain to 1 to maximize resolution for your 3.3V sensors
    ads.gain = 1
    ph_chan = AnalogIn(ads, config.CHAN_PH)
    ec_chan = AnalogIn(ads, config.CHAN_EC)
    print("-> Chemistry ADC connected (pH & EC initialized).")
except Exception as e:
    print(f"! ADC Analog Error: {e}")

threading.Thread(target=start_web_server, daemon=True).start()

# --- STATE VARIABLES & COUNTERS ---
system_start_time = time.time()
last_water_time = time.time() - 150 # Offset to prevent freeze on boot
last_dose_time = 0
is_watering = False
water_start_time = 0
fan_active = False
consecutive_ph_doses = 0
last_good_ph = 6.0 # Tracks the last stable pH reading

def evaluate_system_health(t, ph, ec, water_ok):
    health_score = 100
    status = "OPTIMAL"
    prediction = "Rule-Based System Active"
    safe_mode = False

    if not water_ok:
        health_score = 20
        status = "CRITICAL"
        prediction = "FAIL-SAFE: LOW WATER. Pumps DISABLED."
        safe_mode = True
    elif ph < config.PH_CRITICAL_LOW or ph > config.PH_CRITICAL_HIGH:
        health_score = 10
        status = "CRITICAL"
        prediction = "FAIL-SAFE: pH Sensor Error. Chemical Pumps DISABLED."
        safe_mode = True
    elif t > config.CRITICAL_TEMP_LIMIT:
        health_score = 40
        status = "WARNING"
        prediction = f"FAIL-SAFE: Temp > {config.CRITICAL_TEMP_LIMIT}C. Overheating Risk."
        safe_mode = True
    elif ph < (config.TARGET_PH - config.PH_TOLERANCE) or ph > (config.TARGET_PH + config.PH_TOLERANCE):
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
    global consecutive_ph_doses, fan_active, last_good_ph
    
    # --- 1. READ CLIMATE ---
    t, h = (25.0, 50.0)
    if bme280: 
        try:
            t = round(bme280.temperature, 1)
            h = round(bme280.relative_humidity, 0)
        except: pass
    
    # Logic updated for NPN Normally Closed (NC) sensor:
    # Water detected -> LED Red -> Sensor floats -> PUD_UP pulls to HIGH
    water_ok = (GPIO.input(config.WATER_LEVEL_PIN) == GPIO.HIGH)
    water_level_pct = 100.0 if water_ok else 10.0

    ph_val = last_good_ph 
    ec_val = 0.0

    cur_time = time.time()

    # --- 2. SOFTWARE GALVANIC ISOLATION SEQUENCE ---
    if ads and ph_chan and ec_chan:
        try:
            # Step A: Power EC, Read EC, Kill EC
            GPIO.output(EC_POWER_PIN, GPIO.HIGH)
            time.sleep(0.5) # Let EC sensor stabilize
            ec_v = ec_chan.voltage
            
            # --- EC CALIBRATION APPLIED HERE ---
            calculated_ec = ec_v * config.EC_MULTIPLIER
            ec_val = round(calculated_ec, 2)
            
            GPIO.output(EC_POWER_PIN, GPIO.LOW)
            time.sleep(0.5) # Let water stabilize
            
            # Step B: Read pH using ORMA (Outlier Removal)
            PH_SETTLING_TIME = 120 # Wait 60s after pump turns off for water to electrically settle
            
            if is_watering or (cur_time - last_water_time < PH_SETTLING_TIME):
                ph_val = last_good_ph # Freeze pH reading
            else:
                ph_voltages = []
                for _ in range(100):
                    ph_voltages.append(ph_chan.voltage)
                    time.sleep(0.005)
                
                ph_voltages.sort()
                stable_voltages = ph_voltages[20:-20] 
                avg_v = sum(stable_voltages) / len(stable_voltages)
                
                # --- PH CALIBRATION APPLIED HERE ---
                ph_val = round((config.PH_SLOPE * avg_v) + config.PH_INTERCEPT, 2)
                last_good_ph = ph_val
                
        except Exception as e:
            ph_val = last_good_ph 

    now = datetime.now()

    # --- 3. STABILIZATION PHASE ---
    if cur_time - system_start_time < config.STABILIZATION_PERIOD:
        remaining_time = int(config.STABILIZATION_PERIOD - (cur_time - system_start_time))
        current_activity = f"Sensor Stabilization ({remaining_time}s)"
        sys_health = {"health_score": 100, "status": "STARTUP", "prediction": "Waiting for sensors..."}
        
        update_dashboard_file(t, h, ph_val, ec_val, water_level_pct, "OFF", "OFF", "OFF", "STARTUP", current_activity, sys_health)
        print(f"[{now.strftime('%H:%M:%S')}] {current_activity} | T:{t}°C pH:{ph_val} EC:{ec_val} W:{'OK' if water_ok else 'LOW'}      ", end='\r')
        return

    # --- 4. FAIL-SAFE EVALUATION ---
    safe_mode, sys_health = evaluate_system_health(t, ph_val, ec_val, water_ok)
    safety_str = "SAFE MODE" if safe_mode else "OK"
    
    light_state, fan_state, pump_state = "OFF", "OFF", "OFF"
    current_activity = "Monitoring"

    # --- 5. LIGHTS ---
    if config.LIGHT_START_HOUR <= now.hour < config.LIGHT_END_HOUR and t < config.CRITICAL_TEMP_LIMIT:
        GPIO.output(config.RELAYS['light'], GPIO.LOW)
        light_state = "ON"
    else:
        GPIO.output(config.RELAYS['light'], GPIO.HIGH)

    # --- 6. FANS ---
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

    # --- 7. WATER CYCLE ---
    if water_ok:
        if not is_watering and (cur_time - last_water_time > config.WATER_INTERVAL):
            is_watering = True
            water_start_time = cur_time
            GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
        elif is_watering and (cur_time - water_start_time > config.WATER_DURATION):
            is_watering = False
            last_water_time = cur_time # This triggers the 60s cooldown for regular watering!
            GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
    else:
        if is_watering: last_water_time = cur_time # Safety catch
        is_watering = False
        GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
    
    if is_watering: 
        pump_state = "ON"
        if not safe_mode: current_activity = "Irrigation"

    # --- 8. CHEMICAL DOSING (pH Only for now) ---
    if not safe_mode and water_ok and (cur_time - last_dose_time > config.DOSE_WAIT_TIME):
        dosed = False
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
                if not is_watering: 
                    GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
                    last_water_time = time.time() # This triggers the 60s cooldown after mixing!
                dosed = True
                consecutive_ph_doses += 1
            else:
                current_activity = "FAIL-SAFE: pH Pump Locked."
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
                if not is_watering: 
                    GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
                    last_water_time = time.time() # This triggers the 60s cooldown after mixing!
                dosed = True
                consecutive_ph_doses += 1
            else:
                current_activity = "FAIL-SAFE: pH Pump Locked."
        else:
            consecutive_ph_doses = 0 
            
        if dosed: last_dose_time = cur_time

    # --- 9. EXPORT & CONSOLE LOG ---
    if safe_mode: current_activity = sys_health["prediction"]
    update_dashboard_file(t, h, ph_val, ec_val, water_level_pct, light_state, fan_state, pump_state, safety_str, current_activity, sys_health)
    log_data_to_csv(t, h, ph_val, ec_val, water_level_pct, light_state, fan_state, pump_state, safety_str, current_activity, sys_health)
    
    # Terminal output now prints actual calibrated EC value
    print(f"[{now.strftime('%H:%M:%S')}] {current_activity: <25} | T:{t}°C pH:{ph_val} EC:{ec_val} (SF:{consecutive_ph_doses}) W:{'OK' if water_ok else 'LOW'}      ", end='\r')

# --- MAIN EXECUTION ---
try:
    while True:
        run_control_loop()
        time.sleep(config.LOOP_DELAY)
except KeyboardInterrupt:
    print("\nShutting down... turning off all relays.")
    GPIO.cleanup()
