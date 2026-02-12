import time
import json
import os
import sys
import threading
import http.server
import socketserver
from datetime import datetime

# Import Hardware & Config
import config
from ml_engine import AnomalyDetector

try:
    import RPi.GPIO as GPIO
    import board
    import busio
    from adafruit_bme280 import basic as adafruit_bme280
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except ImportError:
    print("!! Error: Hardware libraries missing. Run in Virtual Environment.")
    sys.exit(1)

# --- PI 5 STABILITY PATCH ---
def reset_i2c():
    os.system("sudo modprobe -r i2c_bcm2835 && sudo modprobe i2c_bcm2835")
    time.sleep(1)

# --- GLOBAL STATE ---
farm_state = {
    "temp": 0.0, "hum": 0.0, "ph": 7.0, "ec": 0.0, "level": 0.0,
    "last_update": "", "safety": "INIT",
    "relays": {}, "ml": {"prediction": "Booting", "vitality": 0}
}

detector = AnomalyDetector()

def init_hardware():
    print("Initializing Vertical Farm OS...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Setup 8 Relays (Active Low)
    for name, pin in config.RELAYS.items():
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
        farm_state["relays"][name] = "OFF"
    
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
        ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
        print("[OK] All Sensors Online.")
        return bme, ads
    except Exception as e:
        print(f"[FAIL] I2C Bus Error: {e}")
        reset_i2c()
        return None, None

def automation_loop():
    bme, ads = init_hardware()
    last_water_time = 0
    last_dose_time = 0

    while True:
        try:
            # 1. READ SENSORS
            if bme:
                farm_state["temp"] = round(bme.temperature, 1)
                farm_state["hum"] = round(bme.relative_humidity, 0)
            
            if ads:
                # pH reading using config calibration
                v_ph = AnalogIn(ads, config.CHAN_PH).voltage
                farm_state["ph"] = round((config.PH_SLOPE * v_ph) + config.PH_INTERCEPT, 2)
                # Level and EC
                farm_state["level"] = round(AnalogIn(ads, config.CHAN_LEVEL).voltage, 2)
                farm_state["ec"] = round(AnalogIn(ads, config.CHAN_EC).voltage * 0.8, 2) # Simulated EC scale

            # 2. SAFETY CHECK
            if farm_state["level"] < config.MIN_WATER_VOLTAGE:
                farm_state["safety"] = "LOW WATER"
                GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
            else:
                farm_state["safety"] = "SAFE"

            # 3. ACTUATOR LOGIC
            now = datetime.now()
            
            # LIGHTS (6AM - 8PM)
            is_day = config.LIGHT_START_HOUR <= now.hour < config.LIGHT_END_HOUR
            GPIO.output(config.RELAYS['light'], GPIO.LOW if is_day else GPIO.HIGH)
            farm_state["relays"]["light"] = "ON" if is_day else "OFF"

            # FANS (Temp > 25C)
            is_hot = farm_state["temp"] > config.TARGET_TEMP
            GPIO.output(config.RELAYS['fan_1'], GPIO.LOW if is_hot else GPIO.HIGH)
            GPIO.output(config.RELAYS['fan_2'], GPIO.LOW if is_hot else GPIO.HIGH)
            farm_state["relays"]["fan_1"] = "ON" if is_hot else "OFF"
            farm_state["relays"]["fan_2"] = "ON" if is_hot else "OFF"

            # WATER CYCLE (15m On / 45m Off)
            time_since_water = time.time() - last_water_time
            if time_since_water > (config.WATER_DURATION + config.WATER_INTERVAL):
                print("\n[EVENT] Starting Water Cycle")
                GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
                farm_state["relays"]["water_pump"] = "ON"
                time.sleep(config.WATER_DURATION)
                GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
                farm_state["relays"]["water_pump"] = "OFF"
                last_water_time = time.time()

            # CHEMISTRY (pH Adjustment)
            if time.time() - last_dose_time > config.DOSE_WAIT_TIME:
                if farm_state["ph"] > (config.TARGET_PH + config.PH_TOLERANCE):
                    GPIO.output(config.RELAYS['ph_down'], GPIO.LOW)
                    time.sleep(config.DOSE_DURATION)
                    GPIO.output(config.RELAYS['ph_down'], GPIO.HIGH)
                    last_dose_time = time.time()
                elif farm_state["ph"] < (config.TARGET_PH - config.PH_TOLERANCE):
                    GPIO.output(config.RELAYS['ph_up'], GPIO.LOW)
                    time.sleep(config.DOSE_DURATION)
                    GPIO.output(config.RELAYS['ph_up'], GPIO.HIGH)
                    last_dose_time = time.time()

            # 4. ML ENGINE & LOGGING
            farm_state["ml"] = detector.analyze(farm_state)
            farm_state["last_update"] = now.strftime("%H:%M:%S")
            
            with open("dashboard.json", "w") as f:
                json.dump(farm_state, f)
            
            # Print status to SSH console
            print(f"[{farm_state['last_update']}] T:{farm_state['temp']} | pH:{farm_state['ph']} | Lvl:{farm_state['level']}V | ML:{farm_state['ml']['prediction']}      ", end='\r')
            time.sleep(2)

        except Exception as e:
            print(f"\n[LOOP ERROR] {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Start Dashboard Server
    PORT = 8000
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print(f"Web Dashboard online at http://[IP_ADDRESS]:{PORT}/stunning_dashboard.html")

    try:
        automation_loop()
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nShutdown Complete.")