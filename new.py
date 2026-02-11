import time
import json
import threading
import http.server
import socketserver
import os
from datetime import datetime
import config  # Import settings from config.py

# --- HARDWARE ABSTRACTION LAYER (HAL) ---

# 1. GPIO Setup
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
except ImportError:
    class GPIO:
        BCM="BCM"; OUT="OUT"; HIGH=1; LOW=0
        def setmode(m): pass
        def setup(p, m, initial=1): pass
        def output(p, s): pass
        def cleanup(): pass

# 2. Resilient Pi 5 I2C Init
i2c = None
bme280 = None
ads = None
ph_chan = None
ec_chan = None
level_chan = None

def init_hardware():
    global i2c, bme280, ads, ph_chan, ec_chan, level_chan
    
    print("\n--- Initializing Hardware (Pi 5 Optimized) ---")
    
    try:
        import board
        import busio
        # Give the OS a moment to settle
        time.sleep(1)
        i2c = busio.I2C(board.SCL, board.SDA)
        print("-> I2C Bus opened.")
    except Exception as e:
        print(f"!! Fatal I2C Bus Error: {e}")
        return

    # Attempt BME280 (Address 0x76)
    try:
        from adafruit_bme280 import basic as adafruit_bme280
        # Multiple retries for Pi 5 timing issues
        for i in range(3):
            try:
                bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
                print(f"-> BME280 ready at {hex(config.I2C_ADDR_BME280)}")
                break
            except:
                time.sleep(0.5)
        if not bme280: print("! BME280 not responding.")
    except Exception as e:
        print(f"! BME280 Library error: {e}")

    # Attempt ADS1115 (Address 0x48)
    try:
        import adafruit_ads1x15.ads1115 as ADS
        from adafruit_ads1x15.analog_in import AnalogIn
        for i in range(3):
            try:
                ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
                ph_chan = AnalogIn(ads, config.CHAN_PH)
                ec_chan = AnalogIn(ads, config.CHAN_EC)
                level_chan = AnalogIn(ads, config.CHAN_LEVEL)
                print(f"-> ADS1115 ready at {hex(config.I2C_ADDR_ADS1115)}")
                break
            except:
                time.sleep(0.5)
        if not ads: print("! ADS1115 not responding.")
    except Exception as e:
        print(f"! ADS1115 Library error: {e}")

# --- SETUP RELAYS ---
def init_relays():
    for name, pin in config.RELAYS.items():
        # Using 'initial' parameter to prevent 'flicker' on start
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
    print("-> All Relays initialized to OFF.")

# --- DASHBOARD UPDATE ---
def update_dashboard(t, h, ph, ec, l_s, f_s, p_s, s_s):
    data = {
        "timestamp": datetime.now().strftime('%H:%M:%S'),
        "temp": t, "hum": h, "ph": ph, "ec": ec,
        "light_state": l_s, "fan_state": f_s, "pump_state": p_s, "safety": s_s
    }
    try:
        with open("dashboard.json", "w") as f:
            json.dump(data, f)
    except: pass

# --- MAIN LOOP ---
def run_loop():
    print("\nAutomation Loop Active. Monitoring sensors...")
    while True:
        try:
            # 1. Read Sensors (with Pi 5 Errno 11 protection)
            t = round(bme280.temperature, 1) if bme280 else 25.0
            h = round(bme280.relative_humidity, 0) if bme280 else 50.0
            
            ph_val = 6.0
            if ph_chan:
                v = ph_chan.voltage
                ph_val = round((config.PH_SLOPE * v) + config.PH_INTERCEPT, 2)
            
            ec_val = round(ec_chan.voltage * 1.0, 2) if ec_chan else 0.0

            # 2. Logic (Example: Fans based on Temp)
            fan_state = "OFF"
            if t > config.TARGET_TEMP:
                GPIO.output(config.RELAYS['fan_1'], GPIO.LOW)
                GPIO.output(config.RELAYS['fan_2'], GPIO.LOW)
                fan_state = "ON"
            else:
                GPIO.output(config.RELAYS['fan_1'], GPIO.HIGH)
                GPIO.output(config.RELAYS['fan_2'], GPIO.HIGH)

            # 3. Update Status
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Temp: {t}C | pH: {ph_val} | EC: {ec_val}", end='\r')
            update_dashboard(t, h, ph_val, ec_val, "OFF", fan_state, "OFF", "SAFE")
            
            time.sleep(2)
            
        except OSError as e:
            if e.errno == 11: # Resource temporarily unavailable
                time.sleep(1) # Just wait and retry
            else:
                print(f"\n! Loop Error: {e}")
        except KeyboardInterrupt:
            break

# --- START SERVER ---
def start_server():
    with socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    init_relays()
    init_hardware()
    
    # Start web server
    threading.Thread(target=start_server, daemon=True).start()
    
    try:
        run_loop()
    finally:
        GPIO.cleanup()
        print("\nShutdown complete.")