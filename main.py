import time
import smbus2
import json
import threading
import http.server
import socketserver
import webbrowser
import os
from datetime import datetime
import config  # Import settings from config.py

# --- HARDWARE ABSTRACTION LAYER (HAL) ---
# This block ensures the code runs on Mac/PC without crashing

# 1. Mock GPIO
try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    class GPIO:
        BCM = "BCM"; OUT = "OUT"; HIGH = 1; LOW = 0
        def setmode(mode): pass
        def setup(pin, mode): pass
        def output(pin, state): print(f"[MOCK] Pin {pin} -> {'HIGH' if state else 'LOW'}")
        def cleanup(): pass

# 2. Mock Board & Busio (Crucial for Mac)
try:
    import board
    import busio
    i2c = busio.I2C(board.SCL, board.SDA)
except (ImportError, NotImplementedError, AttributeError):
    print("[SIMULATION] Board/Busio not detected. Running in PC Mode.")
    board = None
    busio = None
    i2c = None

# 3. Sensor Libraries
try:
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    from adafruit_bme280 import basic as adafruit_bme280
except (ImportError, NotImplementedError):
    print("[SIMULATION] Sensor libraries missing or incompatible.")
    ADS = None
    adafruit_bme280 = None

# Import ML Engine
try:
    from ml_engine import AnomalyDetector
    ML_AVAILABLE = True
except ImportError:
    print("! ML Engine not found. Running in basic mode.")
    ML_AVAILABLE = False

# --- WEB SERVER LOGIC ---
def start_web_server():
    """Starts a simple HTTP server in a background thread."""
    PORT = 8000
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args): pass
            
    try:
        if not os.path.exists("gow.html"):
            print("! Warning: stunning_dashboard.html not found.")
            
        with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
            print(f"-> Web Server Running: http://localhost:{PORT}")
            httpd.serve_forever()
    except OSError:
        print(f"! Port {PORT} is busy. Server might already be running.")

# --- SETUP ---
print("System Booting...")

GPIO.setmode(GPIO.BCM)

# Setup Relays
for name, pin in config.RELAYS.items():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH) # ALL OFF

# Setup Sensors
bme280 = None
ads = None
ph_chan = None
ec_chan = None
level_chan = None

if i2c:
    try:
        bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
    except: print("! Temp Sensor Missing")

    try:
        ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
        ph_chan = AnalogIn(ads, config.CHAN_PH)
        ec_chan = AnalogIn(ads, config.CHAN_EC)
        level_chan = AnalogIn(ads, config.CHAN_LEVEL)
    except: print("! ADS1115 Missing")

# Setup ML
detector = None
if ML_AVAILABLE:
    detector = AnomalyDetector()

# --- AUTO-LAUNCH DASHBOARD ---
server_thread = threading.Thread(target=start_web_server, daemon=True)
server_thread.start()
time.sleep(1)
webbrowser.open("http://localhost:8000/gow.html")

# --- LOGIC ---
last_water_time = 0
last_dose_time = 0

def get_ec(voltage):
    # Basic calibration: voltage * K. You must calibrate this with 1.41 mS fluid!
    # For now, we assume 1V ~= 1.0 mS/cm as a starting point.
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
    if level_chan.voltage < config.MIN_WATER_VOLTAGE:
        GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
        return False
    return True

def run_control_loop():
    global last_water_time, last_dose_time
    
    # 1. READ SENSORS
    t, h = (25.0, 50.0) 
    if bme280: t, h = (round(bme280.temperature, 1), round(bme280.relative_humidity, 0))
    
    ph_val = 6.0
    if ph_chan:
        v = ph_chan.voltage
        # Use calibrated values from config
        slope = getattr(config, 'PH_SLOPE', -3.5) 
        intercept = getattr(config, 'PH_INTERCEPT', 15.75)
        if v > 0.1: ph_val = round((slope * v) + intercept, 2)

    ec_val = 1.2 # Default
    if ec_chan:
        ec_val = get_ec(ec_chan.voltage)

    # 2. SAFETY CHECK
    is_safe = check_safety()
    safety_str = "SAFE" if is_safe else "ALERT"
    
    # 3. ML ANALYSIS
    ml_data = None
    if detector:
        ml_data = detector.analyze({'temp': t, 'hum': h, 'ph': ph_val, 'ec': ec_val})

    if not is_safe:
        print("ALERT: Low Water!")
        update_dashboard_file(t, h, ph_val, ec_val, "OFF", "OFF", "DISABLED", safety_str, ml_data)
        return

    now = datetime.now()
    
    light_state = "OFF"
    fan_state = "OFF"
    pump_state = "OFF"

    # 4. LIGHTS (8-Hour Cycle)
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

    # 6. WATER (Timer Cycle)
    if time.time() - last_water_time > (config.WATER_DURATION + config.WATER_INTERVAL):
        pump_state = "ON"
        update_dashboard_file(t, h, ph_val, ec_val, light_state, fan_state, pump_state, safety_str, ml_data)
        GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
        time.sleep(config.WATER_DURATION)
        GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
        last_water_time = time.time()
        pump_state = "OFF"

    # 7. CHEMISTRY (pH & EC Dosing)
    if time.time() - last_dose_time > config.DOSE_WAIT_TIME:
        # pH Logic
        if ph_val > 1.0:
            if ph_val > (config.TARGET_PH + config.PH_TOLERANCE):
                GPIO.output(config.RELAYS['ph_down'], GPIO.LOW)
                time.sleep(config.DOSE_DURATION)
                GPIO.output(config.RELAYS['ph_down'], GPIO.HIGH)
                last_dose_time = time.time()
            elif ph_val < (config.TARGET_PH - config.PH_TOLERANCE):
                GPIO.output(config.RELAYS['ph_up'], GPIO.LOW)
                time.sleep(config.DOSE_DURATION)
                GPIO.output(config.RELAYS['ph_up'], GPIO.HIGH)
                last_dose_time = time.time()
        
        # EC Logic (Nutrients)
        if time.time() - last_dose_time > config.DOSE_WAIT_TIME: # Re-check timer
             if ec_val < (config.TARGET_EC - config.EC_TOLERANCE):
                # Add Nutrients A & B
                GPIO.output(config.RELAYS['nutrient_a'], GPIO.LOW)
                GPIO.output(config.RELAYS['nutrient_b'], GPIO.LOW)
                time.sleep(config.DOSE_DURATION)
                GPIO.output(config.RELAYS['nutrient_a'], GPIO.HIGH)
                GPIO.output(config.RELAYS['nutrient_b'], GPIO.HIGH)
                last_dose_time = time.time()

    # 8. UPDATE DASHBOARD & LOG
    update_dashboard_file(t, h, ph_val, ec_val, light_state, fan_state, pump_state, safety_str, ml_data)
    
    status = f"T:{t} pH:{ph_val} EC:{ec_val}"
    print(f"[{now.strftime('%H:%M:%S')}] {status}") 

# --- MAIN LOOP ---
try:
    while True:
        run_control_loop()
        time.sleep(2)
except KeyboardInterrupt:
    GPIO.cleanup()