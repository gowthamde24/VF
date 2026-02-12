import time
import json
import os
import sys
import threading
import http.server
import socketserver
from datetime import datetime

# Local Modular Imports
import config
from ml_engine import AnomalyDetector

# --- PI 5 SYSTEM STABILITY ---
def reset_i2c():
    os.system("sudo modprobe -r i2c_bcm2835 && sudo modprobe i2c_bcm2835")
    time.sleep(1)

try:
    import RPi.GPIO as GPIO
    import board
    import busio
    from adafruit_bme280 import basic as adafruit_bme280
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except ImportError as e:
    print(f"!! Library Error: {e}. Ensure venv --system-site-packages is used.")
    sys.exit(1)

# Initialize Intelligence
ml_engine = AnomalyDetector()

# Global State for Dashboard
farm_data = {
    "temp": 0.0, "hum": 0.0, "ph": 7.0, "ec": 0.0, "level": 0.0,
    "relays": {}, "ml": {"health_score": 100, "status": "BOOTING", "prediction": "N/A"},
    "last_update": "N/A", "activity": "System Booting..."
}

def init_hw():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for name, pin in config.RELAYS.items():
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
        farm_data["relays"][name] = "OFF"
    
    try:
        return busio.I2C(board.SCL, board.SDA)
    except:
        reset_i2c()
        return busio.I2C(board.SCL, board.SDA)

def farm_state_update_relay(name, state):
    farm_data["relays"][name] = state

def run_automation():
    i2c = init_hw()
    bme = None
    ads = None
    last_dose_time = 0

    try: bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
    except: farm_data["activity"] = "BME280 Missing!"
    try: ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
    except: farm_data["activity"] = "ADS1115 Missing!"

    print("\n--- Vertical Farm OS Started ---")
    while True:
        try:
            # 1. READ SENSORS
            if bme:
                farm_data["temp"] = round(bme.temperature, 1)
                farm_data["hum"] = round(bme.relative_humidity, 0)
            if ads:
                v_ph = AnalogIn(ads, config.CHAN_PH).voltage
                farm_data["ph"] = round((config.PH_SLOPE * v_ph) + config.PH_INTERCEPT, 2)
                
                v_ec = AnalogIn(ads, config.CHAN_EC).voltage
                farm_data["ec"] = round(v_ec * 0.8, 2) # Simulated EC scale
                
                farm_data["level"] = round(AnalogIn(ads, config.CHAN_LEVEL).voltage, 2)

            # 2. ML ENGINE ANALYSIS
            farm_data["ml"] = ml_engine.analyze(farm_data)

            # 3. CONTROL LOGIC
            now = time.time()
            farm_data["activity"] = "Monitoring Sensors"

            # Fan Control (Temp)
            fan_val = GPIO.LOW if farm_data["temp"] > config.TARGET_TEMP else GPIO.HIGH
            GPIO.output(config.RELAYS['fan_1'], fan_val)
            GPIO.output(config.RELAYS['fan_2'], fan_val)
            farm_state_update_relay("fan_1", "ON" if fan_val == GPIO.LOW else "OFF")
            farm_state_update_relay("fan_2", "ON" if fan_val == GPIO.LOW else "OFF")
            
            if fan_val == GPIO.LOW: farm_data["activity"] = "Cooling Active"

            # pH Control (Pulsed Dosing)
            if now - last_dose_time > config.COOLDOWN_TIME:
                if farm_data["ph"] > config.TARGET_PH_MAX:
                    farm_data["activity"] = f"Dosing pH Down (pH {farm_data['ph']})"
                    GPIO.output(config.RELAYS['ph_down'], GPIO.LOW)
                    farm_state_update_relay("ph_down", "ON")
                    
                    # Force update dashboard immediately for visual feedback
                    with open("dashboard.json", "w") as f: json.dump(farm_data, f)
                    
                    time.sleep(config.PULSE_TIME)
                    GPIO.output(config.RELAYS['ph_down'], GPIO.HIGH)
                    farm_state_update_relay("ph_down", "OFF")
                    last_dose_time = time.time()

            # 4. EXPORT DATA
            farm_data["last_update"] = datetime.now().strftime("%H:%M:%S")
            farm_data["status"] = "Active"
            with open("dashboard.json", "w") as f:
                json.dump(farm_data, f)
            
            print(f"[{farm_data['last_update']}] T:{farm_data['temp']}C | pH:{farm_data['ph']} | Act:{farm_data['activity']}      ", end='\r')
            time.sleep(2)

        except Exception as e:
            print(f"\n[LOOP ERROR] {e}")
            time.sleep(2)

if __name__ == "__main__":
    # Start Dashboard Server on Port 8000
    PORT = 8000
    threading.Thread(target=lambda: socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler).serve_forever(), daemon=True).start()
    print(f"Web Dashboard: http://[YOUR_PI_IP]:{PORT}/stunning_dashboard.html")
    
    try:
        run_automation()
    finally:
        for pin in config.RELAYS.values(): GPIO.output(pin, GPIO.HIGH)
        GPIO.cleanup()