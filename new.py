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

# 2. Mock Board & Busio
try:
    import board
    import busio
    # Pi 5 specific: Ensure we are using the correct I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)
    IS_PC = False
except Exception as e:
    print(f"[SIMULATION] I2C Bus failed: {e}")
    i2c = None
    IS_PC = True

# 3. Sensor Libraries
try:
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    from adafruit_bme280 import basic as adafruit_bme280
except ImportError:
    print("! Sensor libraries (Blinka/ADS/BME) not installed.")
    ADS = None

# --- SETUP ---
print("--- System Booting ---")

GPIO.setmode(GPIO.BCM)

# Setup Relays
for name, pin in config.RELAYS.items():
    try:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
    except Exception as e:
        print(f"! Failed to setup Relay {name}: {e}")

# Setup Sensors
bme280 = None
ads = None
ph_chan = None
ec_chan = None
level_chan = None

if i2c:
    # Try to initialize BME280
    try:
        bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
        print(f"-> BME280 Detected at {hex(config.I2C_ADDR_BME280)}")
    except Exception as e:
        print(f"! BME280 Init Failed: {e}")

    # Try to initialize ADS1115
    try:
        ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
        ph_chan = AnalogIn(ads, config.CHAN_PH)
        ec_chan = AnalogIn(ads, config.CHAN_EC)
        level_chan = AnalogIn(ads, config.CHAN_LEVEL)
        print(f"-> ADS1115 Detected at {hex(config.I2C_ADDR_ADS1115)}")
    except Exception as e:
        print(f"! ADS1115 Init Failed: {e}")
else:
    print("! Skipping sensor init (I2C Bus not available)")

# --- LOGIC & DASHBOARD ---
# [Note: The rest of the script logic remains the same as your previous version]
# [I've condensed it here to focus on the fix, but keep your existing dosing/loop logic]

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

def run_control_loop():
    # Read values with fallbacks for simulation
    t = round(bme280.temperature, 1) if bme280 else 25.0
    h = round(bme280.relative_humidity, 0) if bme280 else 50.0
    
    ph_val = 6.0
    if ph_chan:
        v = ph_chan.voltage
        slope = getattr(config, 'PH_SLOPE', -3.5)
        intercept = getattr(config, 'PH_INTERCEPT', 15.75)
        ph_val = round((slope * v) + intercept, 2)
        
    ec_val = round(ec_chan.voltage * 1.0, 2) if ec_chan else 1.2
    
    # ... [Insert your existing logic for lights, fans, and pumps here] ...
    
    update_dashboard_file(t, h, ph_val, ec_val, "OFF", "OFF", "OFF", "SAFE")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] T:{t} pH:{ph_val} EC:{ec_val}")

# --- WEB SERVER & START ---
def start_web_server():
    try:
        with socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except: pass

threading.Thread(target=start_web_server, daemon=True).start()

try:
    while True:
        run_control_loop()
        time.sleep(2)
except KeyboardInterrupt:
    GPIO.cleanup()