import time
import json
import threading
import http.server
import socketserver
import webbrowser
import os
from datetime import datetime
import config  # Import settings from config.py

# --- NATIVE RASPBERRY PI IMPORTS ---
# These will crash if run on a PC/Mac, but will work perfectly on the Pi
import RPi.GPIO as GPIO
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_bme280 import basic as adafruit_bme280
from ml_engine import AnomalyDetector

# --- WEB SERVER LOGIC ---
def start_web_server():
    """Starts a simple HTTP server in a background thread."""
    PORT = 8000
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args): pass
            
    try:
        if not os.path.exists("stunning_dashboard.html"):
            print("! Warning: stunning_dashboard.html not found.")
            
        with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
            print(f"-> Web Server Running: http://localhost:{PORT}")
            httpd.serve_forever()
    except OSError:
        print(f"! Port {PORT} is busy. Server might already be running.")

# --- SETUP ---
print("System Booting (Production Pi Mode)...")

# 1. Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for name, pin in config.RELAYS.items():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH) # ALL RELAYS OFF INITIALLY

# 2. Initialize I2C Bus
i2c = busio.I2C(board.SCL, board.SDA)

# 3. Initialize Sensors (With basic try/except to prevent total crash if a wire is loose)
bme280 = None
try:
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
    print("-> BME280 Climate Sensor connected.")
except Exception as e:
    print(f"! BME280 Temp Sensor Error: {e}")

ads, ph_chan, ec_chan, level_chan = None, None, None, None
try:
    ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
    ph_chan = AnalogIn(ads, config.CHAN_PH)
    ec_chan = AnalogIn(ads, config.CHAN_EC)
    level_chan = AnalogIn(ads, config.CHAN_LEVEL)
    print("-> ADS1115 ADC connected.")
except Exception as e:
    print(f"! ADS1115 Analog Error: {e}")

# 4. Initialize Machine Learning
detector = AnomalyDetector()
print("-> ML Anomaly Engine initialized.")

# --- AUTO-LAUNCH DASHBOARD ---
server_thread = threading.Thread(target=start_web_server, daemon=True)
server_thread.start()
time.sleep(1)
try:
    # This tries to open the browser automatically on the Pi's desktop
    webbrowser.open(f"http://localhost:8000/stunning_dashboard.html")
except:
    pass

# --- LOGIC VARIABLES ---
last_water_time = time.time()  # Start with current time so it doesn't water instantly on boot
last_dose_time = 0
is_watering = False            # Tracks if pump is currently running
water_start_time = 0           # Tracks when the pump turned on

def get_ec(voltage):
    # Basic calibration: voltage * K. (Assuming 1V ~= 1.0 mS/cm baseline)
    if voltage < 0.1: return 0.0
    return round(voltage * 1.0, 2)

def update_dashboard_file(temp, hum, ph, ec, light_s, fan_s, pump_s, safety_s, ml_data=None):
    data = {
        "timestamp": datetime.now().strftime('%H:%M:%S'),
        "temp": temp,
        "hum": hum,
        "ph": ph,
        "ec": ec, 
        "light_state": light_s,
        "fan_state": fan_s,
        "pump_state": pump_s,
        "safety": safety_s,
        "ml": ml_data if ml_data else {"health_score": 100, "status": "OK", "prediction": "Normal"}
    }
    try:
        with open("dashboard.json", "w") as f:
            json.dump(data, f)
    except: pass

def check_safety():
    if not level_chan: return True
    # If the tank is empty, the sensor reads < 0.5V
    if level_chan.voltage < config.MIN_WATER_VOLTAGE:
        GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH) # FORCE OFF
        return False
    return True

def run_control_loop():
    global last_water_time, last_dose_time, is_watering, water_start_time
    
    # 1. READ SENSORS
    t, h = (25.0, 50.0) # Defaults if sensor fails
    if bme280: 
        t = round(bme280.temperature, 1)
        h = round(bme280.relative_humidity, 0)
    
    ph_val = 6.0 # Default
    if ph_chan:
        v = ph_chan.voltage
        slope = getattr(config, 'PH_SLOPE', -5.7706) 
        intercept = getattr(config, 'PH_INTERCEPT', 15.8918)
        if v > 0.1: 
            ph_val = round((slope * v) + intercept, 2)

    ec_val = 1.2 # Default
    if ec_chan:
        ec_val = get_ec(ec_chan.voltage)

    # 2. SAFETY CHECK
    is_safe = check_safety()
    safety_str = "SAFE" if is_safe else "ALERT"
    
    # 3. ML ANALYSIS
    ml_data = detector.analyze({'temp': t, 'hum': h, 'ph': ph_val, 'ec': ec_val})

    if not is_safe:
        print("🚨 ALERT: Low Water! Pump Disabled.")
        is_watering = False # Reset watering state if emergency stop triggers
        update_dashboard_file(t, h, ph_val, ec_val, "OFF", "OFF", "DISABLED", safety_str, ml_data)
        return

    now = datetime.now()
    current_time = time.time()
    
    light_state = "OFF"
    fan_state = "OFF"
    pump_state = "OFF"

    # 4. LIGHTS (Cycle based on config)
    if config.LIGHT_START_HOUR <= now.hour < config.LIGHT_END_HOUR and t < config.TEMP_LIMIT:
        GPIO.output(config.RELAYS['light'], GPIO.LOW)
        light_state = "ON"
    else:
        GPIO.output(config.RELAYS['light'], GPIO.HIGH)

    # 5. FANS (Both Fans)
    if t > config.TARGET_TEMP:
        GPIO.output(config.RELAYS['fan_1'], GPIO.LOW)
        GPIO.output(config.RELAYS['fan_2'], GPIO.LOW)
        fan_state = "ON"
    else:
        GPIO.output(config.RELAYS['fan_1'], GPIO.HIGH)
        GPIO.output(config.RELAYS['fan_2'], GPIO.HIGH)

    # 6. WATER (Timer Cycle) - NON BLOCKING
    # Check if it's time to START watering
    if not is_watering and (current_time - last_water_time > config.WATER_INTERVAL):
        is_watering = True
        water_start_time = current_time
        GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
        
    # Check if it's time to STOP watering
    elif is_watering and (current_time - water_start_time > config.WATER_DURATION):
        is_watering = False
        last_water_time = current_time
        GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
        
    # Maintain state for dashboard
    if is_watering:
        pump_state = "ON"

    # 7. CHEMISTRY (pH & EC Dosing)
    if current_time - last_dose_time > config.DOSE_WAIT_TIME:
        dosed = False
        
        # pH Logic
        if ph_val > 1.0: # Prevent dosing if probe is returning weird 0.0 values
            if ph_val > (config.TARGET_PH + config.PH_TOLERANCE):
                GPIO.output(config.RELAYS['ph_down'], GPIO.LOW)
                time.sleep(config.DOSE_DURATION)
                GPIO.output(config.RELAYS['ph_down'], GPIO.HIGH)
                dosed = True
            elif ph_val < (config.TARGET_PH - config.PH_TOLERANCE):
                GPIO.output(config.RELAYS['ph_up'], GPIO.LOW)
                time.sleep(config.DOSE_DURATION)
                GPIO.output(config.RELAYS['ph_up'], GPIO.HIGH)
                dosed = True
        
        # EC Logic (Nutrients)
        if not dosed and ec_val < (config.TARGET_EC - config.EC_TOLERANCE):
            # Dose Nutrient A
            GPIO.output(config.RELAYS['nutrient_a'], GPIO.LOW)
            time.sleep(config.DOSE_DURATION)
            GPIO.output(config.RELAYS['nutrient_a'], GPIO.HIGH)
            
            time.sleep(0.5) # Short pause between A and B
            
            # Dose Nutrient B
            GPIO.output(config.RELAYS['nutrient_b'], GPIO.LOW)
            time.sleep(config.DOSE_DURATION)
            GPIO.output(config.RELAYS['nutrient_b'], GPIO.HIGH)
            dosed = True
            
        if dosed:
            last_dose_time = current_time

    # 8. UPDATE DASHBOARD & LOG
    update_dashboard_file(t, h, ph_val, ec_val, light_state, fan_state, pump_state, safety_str, ml_data)
    
    status = f"T:{t}°C | Hum:{h}% | pH:{ph_val} | EC:{ec_val}"
    if is_watering: status += " [WATERING]"
    print(f"[{now.strftime('%H:%M:%S')}] {status}") 

# --- EXECUTE ---
try:
    while True:
        run_control_loop()
        time.sleep(2)
except KeyboardInterrupt:
    print("\nShutting down... turning off all relays.")
    GPIO.cleanup()