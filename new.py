import time
import json
import threading
import http.server
import socketserver
import os
import sys
from datetime import datetime
import config  # Import your settings

# --- Pi 5 STABILITY PATCH ---
def reset_i2c_bus():
    print("-> EMI Detected: Resetting I2C Bus Driver...")
    os.system("sudo modprobe -r i2c_bcm2835 && sudo modprobe i2c_bcm2835")
    time.sleep(1.5)

try:
    import RPi.GPIO as GPIO
    import board
    import busio
    from adafruit_bme280 import basic as adafruit_bme280
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except ImportError:
    print("! Missing libraries. Run: pip install adafruit-circuitpython-bme280 adafruit-circuitpython-ads1x15")

# --- GLOBAL HARDWARE OBJECTS ---
i2c = None
bme280 = None
ads = None
ph_chan = None

def init_hardware():
    global i2c, bme280, ads, ph_chan
    
    print("\n" + "="*50)
    print("  VERTICAL FARM SYSTEM - Pi 5 RESILIENT BOOT")
    print("  Target BME280 Addr: " + hex(config.I2C_ADDR_BME280))
    print("="*50)

    # 1. GPIO Reset
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for name, pin in config.RELAYS.items():
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH) 
    print("-> Relays: Initialized to OFF (Active Low)")

    # 2. I2C Init with Aggressive Retries
    for attempt in range(5):
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Test BME280 at the configured address (now 0x77)
            bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
            
            # Test ADS1115
            ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
            ph_chan = AnalogIn(ads, config.CHAN_PH)
            
            print(f"-> Hardware: Success! Found BME at {hex(config.I2C_ADDR_BME280)} and ADS at {hex(config.I2C_ADDR_ADS1115)}")
            return True
        except Exception as e:
            print(f"-> Attempt {attempt+1} at {hex(config.I2C_ADDR_BME280)} failed ({e}).")
            reset_i2c_bus()
    
    print(f"!! CRITICAL: Hardware handshake failed. Check if BME is actually at 0x76 or 0x77.")
    return False

# --- MAIN AUTOMATION LOOP ---
def main_loop():
    print("\n--- Automation Active ---")
    while True:
        try:
            # READ SENSORS
            t = round(bme280.temperature, 1) if bme280 else 25.0
            h = round(bme280.relative_humidity, 0) if bme280 else 50.0
            
            ph_v = ph_chan.voltage if ph_chan else 2.5
            ph_val = round((config.PH_SLOPE * ph_v) + config.PH_INTERCEPT, 2)
            
            fan_state = "OFF"
            if t > config.TARGET_TEMP:
                GPIO.output(config.RELAYS['fan_1'], GPIO.LOW)
                GPIO.output(config.RELAYS['fan_2'], GPIO.LOW)
                fan_state = "ON"
            else:
                GPIO.output(config.RELAYS['fan_1'], GPIO.HIGH)
                GPIO.output(config.RELAYS['fan_2'], GPIO.HIGH)

            ts = datetime.now().strftime('%H:%M:%S')
            print(f"[{ts}] T:{t}C | pH:{ph_val} | Fan:{fan_state}    ", end='\r')
            
            status_data = {
                "temp": t, "hum": h, "ph": ph_val, 
                "fan": fan_state, "time": ts, "status": "RUNNING"
            }
            with open("dashboard.json", "w") as f:
                json.dump(status_data, f)
            
            time.sleep(2)

        except OSError as e:
            if e.errno == 11: 
                time.sleep(0.1)
                continue 
            print(f"\n! Bus Communication Error: {e}")
            time.sleep(2)
        except Exception as e:
            print(f"\n! Unexpected Error: {e}")
            time.sleep(2)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    if init_hardware():
        threading.Thread(target=lambda: socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler).serve_forever(), daemon=True).start()
        main_loop()
    
    for pin in config.RELAYS.values():
        GPIO.output(pin, GPIO.HIGH)
    GPIO.cleanup()
    print("System Standby.")