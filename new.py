import time
import smbus2
import json
import threading
import http.server
import socketserver
import webbrowser
import os
import sys
from datetime import datetime
import config  # Import settings from config.py

# --- HARDWARE ABSTRACTION LAYER (HAL) ---

# 1. Mock GPIO
try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    class GPIO:
        BCM = "BCM"; OUT = "OUT"; HIGH = 1; LOW = 0
        def setmode(mode): pass
        def setup(pin, mode, initial=1): pass
        def output(pin, state): pass
        def cleanup(): pass

# 2. Resilient I2C Initialization
i2c = None
try:
    import board
    import busio
    # Small delay to let the bus settle after boot or previous crashes
    time.sleep(0.5)
    i2c = busio.I2C(board.SCL, board.SDA)
    print("-> I2C Bus Initialized.")
except Exception as e:
    print(f"! I2C Bus Error: {e}")

# 3. Sensor Libraries
try:
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    from adafruit_bme280 import basic as adafruit_bme280
except ImportError:
    print("! Missing Libraries: Run 'pip install adafruit-circuitpython-bme280 adafruit-circuitpython-ads1x15'")
    ADS = None

# --- SETUP ---
print("\n--- System Booting ---")

GPIO.setmode(GPIO.BCM)

# Setup Relays (Force OFF at startup)
for name, pin in config.RELAYS.items():
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)

# Setup Sensors with Retries
bme280 = None
ads = None
ph_chan = None
ec_chan = None
level_chan = None

if i2c:
    # Try BME280
    for attempt in range(3):
        try:
            bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
            print(f"-> BME280 Found at {hex(config.I2C_ADDR_BME280)}")
            break
        except Exception as e:
            print(f"   BME280 Attempt {attempt+1} failed: {e}")
            time.sleep(1)

    # Try ADS1115
    for attempt in range(3):
        try:
            ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
            ph_chan = AnalogIn(ads, config.CHAN_PH)
            ec_chan = AnalogIn(ads, config.CHAN_EC)
            level_chan = AnalogIn(ads, config.CHAN_LEVEL)
            print(f"-> ADS1115 Found at {hex(config.I2C_ADDR_ADS1115)}")
            break
        except Exception as e:
            print(f"   ADS1115 Attempt {attempt+1} failed: {e}")
            time.sleep(1)

# --- UTILITIES ---
def get_ec(voltage):
    if voltage < 0.1: return 0.0
    return round(voltage * 1.0, 2)

def update_dashboard_file(temp, hum, ph, ec, light_s, fan_s, pump_s, safety_s):
    data = {
        "timestamp": datetime.now().strftime('%H:%M:%S'),
        "temp": temp, "hum": hum, "ph": ph, "ec": ec, 
        "light_state": light_s, "fan_state": fan_s, 
        "pump_state": pump_s, "safety": safety_s
    }
    try:
        with open("dashboard.json", "w") as f:
            json.dump(data, f)
    except: pass

# --- CONTROL LOOP ---
last_water_time = 0
last_dose_time = 0

def run_control_loop():
    global last_water_time, last_dose_time
    
    # 1. READ
    t = round(bme280.temperature, 1) if bme280 else 25.0
    h = round(bme280.relative_humidity, 0) if bme280 else 50.0
    
    ph_val = 6.0
    if ph_chan:
        v = ph_chan.voltage
        slope = getattr(config, 'PH_SLOPE', -3.5)
        intercept = getattr(config, 'PH_INTERCEPT', 15.75)
        ph_val = round((slope * v) + intercept, 2)
        
    ec_val = get_ec(ec_chan.voltage) if ec_chan else 1.2

    # 2. LOGIC
    now = datetime.now()
    light_state = "ON" if config.LIGHT_START_HOUR <= now.hour < config.LIGHT_END_HOUR else "OFF"
    fan_state = "ON" if t > config.TARGET_TEMP else "OFF"
    
    # Apply to GPIO
    GPIO.output(config.RELAYS['light'], GPIO.LOW if light_state == "ON" else GPIO.HIGH)
    GPIO.output(config.RELAYS['fan_1'], GPIO.LOW if fan_state == "ON" else GPIO.HIGH)
    GPIO.output(config.RELAYS['fan_2'], GPIO.LOW if fan_state == "ON" else GPIO.HIGH)

    # 3. SYNC
    update_dashboard_file(t, h, ph_val, ec_val, light_state, fan_state, "OFF", "SAFE")
    print(f"[{now.strftime('%H:%M:%S')}] T:{t}°C | pH:{ph_val} | EC:{ec_val}")

# --- WEB SERVER ---
def start_web_server():
    PORT = 8000
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            httpd.serve_forever()
    except: pass

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Start web server in background
    threading.Thread(target=start_web_server, daemon=True).start()
    
    print("\nAutomation Loop Started. Open Browser to http://localhost:8000")
    try:
        while True:
            run_control_loop()
            time.sleep(2)
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nSystem Shutdown Cleanly.")