# # import time
# # import smbus2
# # import json
# # import threading
# # import http.server
# # import socketserver
# # import webbrowser
# # import os
# # from datetime import datetime
# # import config  # Import settings from config.py

# # # --- HARDWARE ABSTRACTION LAYER (HAL) ---
# # # This block ensures the code runs on Mac/PC without crashing

# # # 1. Mock GPIO
# # try:
# #     import RPi.GPIO as GPIO
# # except (ImportError, RuntimeError):
# #     class GPIO:
# #         BCM = "BCM"; OUT = "OUT"; HIGH = 1; LOW = 0
# #         def setmode(mode): pass
# #         def setup(pin, mode): pass
# #         def output(pin, state): print(f"[MOCK] Pin {pin} -> {'HIGH' if state else 'LOW'}")
# #         def cleanup(): pass

# # # 2. Mock Board & Busio (Crucial for Mac)
# # try:
# #     import board
# #     import busio
# #     i2c = busio.I2C(board.SCL, board.SDA)
# # except (ImportError, NotImplementedError, AttributeError):
# #     print("[SIMULATION] Board/Busio not detected. Running in PC Mode.")
# #     board = None
# #     busio = None
# #     i2c = None

# # # 3. Sensor Libraries
# # try:
# #     import adafruit_ads1x15.ads1115 as ADS
# #     from adafruit_ads1x15.analog_in import AnalogIn
# #     from adafruit_bme280 import basic as adafruit_bme280
# # except (ImportError, NotImplementedError):
# #     print("[SIMULATION] Sensor libraries missing or incompatible.")
# #     ADS = None
# #     adafruit_bme280 = None

# # # Import ML Engine
# # try:
# #     from ml_engine import AnomalyDetector
# #     ML_AVAILABLE = True
# # except ImportError:
# #     print("! ML Engine not found. Running in basic mode.")
# #     ML_AVAILABLE = False

# # # --- WEB SERVER LOGIC ---
# # def start_web_server():
# #     """Starts a simple HTTP server in a background thread."""
# #     PORT = 8000
# #     class QuietHandler(http.server.SimpleHTTPRequestHandler):
# #         def log_message(self, format, *args): pass
            
# #     try:
# #         if not os.path.exists("stunning_dashboard.html"):
# #             print("! Warning: stunning_dashboard.html not found.")
            
# #         with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
# #             print(f"-> Web Server Running: http://localhost:{PORT}")
# #             httpd.serve_forever()
# #     except OSError:
# #         print(f"! Port {PORT} is busy. Server might already be running.")

# # # --- SETUP ---
# # print("System Booting...")

# # GPIO.setmode(GPIO.BCM)

# # # Setup Relays
# # for name, pin in config.RELAYS.items():
# #     GPIO.setup(pin, GPIO.OUT)
# #     GPIO.output(pin, GPIO.HIGH) # ALL OFF

# # # Setup Sensors
# # bme280 = None
# # ads = None
# # ph_chan = None
# # ec_chan = None
# # level_chan = None

# # if i2c:
# #     try:
# #         bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
# #     except: print("! Temp Sensor Missing")

# #     try:
# #         ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
# #         ph_chan = AnalogIn(ads, config.CHAN_PH)
# #         ec_chan = AnalogIn(ads, config.CHAN_EC)
# #         level_chan = AnalogIn(ads, config.CHAN_LEVEL)
# #     except: print("! ADS1115 Missing")

# # # Setup ML
# # detector = None
# # if ML_AVAILABLE:
# #     detector = AnomalyDetector()

# # # LCD Class
# # class I2C_LCD_driver:
# #     def __init__(self, address):
# #         if not i2c: return 
# #         try:
# #             self.bus = smbus2.SMBus(1)
# #             self.address = address
# #             self.lcd_write(0x03); self.lcd_write(0x03); self.lcd_write(0x03); self.lcd_write(0x02)
# #             self.lcd_write(0x20|0x08|0x04|0x00); self.lcd_write(0x08|0x04); self.lcd_write(0x01); self.lcd_write(0x04|0x02)
# #             time.sleep(0.2)
# #         except: pass 
# #     def lcd_write(self, cmd, mode=0):
# #         try: self.lcd_write_four_bits(mode|(cmd&0xF0)); self.lcd_write_four_bits(mode|((cmd<<4)&0xF0))
# #         except: pass
# #     def lcd_write_four_bits(self, data):
# #         try: self.bus.write_byte(self.address, data|0x08); self.bus.write_byte(self.address, data|0x08|0x04); self.bus.write_byte(self.address, data|0x08)
# #         except: pass
# #     def lcd_display_string(self, string, line):
# #         if not i2c: return
# #         if line==1: self.lcd_write(0x80)
# #         if line==2: self.lcd_write(0xC0)
# #         for char in string: self.lcd_write(ord(char), 1)
# #     def lcd_clear(self):
# #         if not i2c: return
# #         self.lcd_write(0x01); time.sleep(0.005)

# # lcd = None
# # try: lcd = I2C_LCD_driver(config.I2C_ADDR_LCD)
# # except: pass

# # # --- AUTO-LAUNCH DASHBOARD ---
# # server_thread = threading.Thread(target=start_web_server, daemon=True)
# # server_thread.start()
# # time.sleep(1)
# # webbrowser.open("http://localhost:8000/stunning_dashboard.html")

# # # --- LOGIC ---
# # last_water_time = 0
# # last_dose_time = 0

# # def get_ec(voltage):
# #     # Basic calibration: voltage * K. You must calibrate this with 1.41 mS fluid!
# #     # For now, we assume 1V ~= 1.0 mS/cm as a starting point.
# #     if voltage < 0.1: return 0.0
# #     return round(voltage * 1.0, 2)

# # def update_dashboard_file(temp, hum, ph, ec, light_s, fan_s, pump_s, safety_s):
# #     data = {
# #         "timestamp": datetime.now().strftime('%H:%M:%S'),
# #         "temp": temp,
# #         "hum": hum,
# #         "ph": ph,
# #         "ec": ec, 
# #         "light_state": light_s,
# #         "fan_state": fan_s,
# #         "pump_state": pump_s,
# #         "safety": safety_s
# #     }
# #     try:
# #         with open("dashboard.json", "w") as f:
# #             json.dump(data, f)
# #     except: pass

# # def check_safety():
# #     if not level_chan: return True
# #     if level_chan.voltage < config.MIN_WATER_VOLTAGE:
# #         GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
# #         return False
# #     return True

# # def run_control_loop():
# #     global last_water_time, last_dose_time
    
# #     # 1. READ SENSORS
# #     t, h = (25.0, 50.0) 
# #     if bme280: t, h = (round(bme280.temperature, 1), round(bme280.relative_humidity, 0))
    
# #     ph_val = 6.0
# #     if ph_chan:
# #         v = ph_chan.voltage
# #         # Use calibrated values from config
# #         slope = getattr(config, 'PH_SLOPE', -3.5) 
# #         intercept = getattr(config, 'PH_INTERCEPT', 15.75)
# #         if v > 0.1: ph_val = round((slope * v) + intercept, 2)

# #     ec_val = 1.2 # Default
# #     if ec_chan:
# #         ec_val = get_ec(ec_chan.voltage)

# #     # 2. SAFETY CHECK
# #     is_safe = check_safety()
# #     safety_str = "SAFE" if is_safe else "ALERT"
# #     if not is_safe:
# #         print("ALERT: Low Water!")
# #         if lcd: lcd.lcd_display_string("LOW WATER!", 1)
# #         update_dashboard_file(t, h, ph_val, ec_val, "OFF", "OFF", "DISABLED", safety_str)
# #         return

# #     now = datetime.now()
    
# #     light_state = "OFF"
# #     fan_state = "OFF"
# #     pump_state = "OFF"

# #     # 3. LIGHTS
# #     if config.LIGHT_START_HOUR <= now.hour < config.LIGHT_END_HOUR and t < config.TEMP_LIMIT:
# #         GPIO.output(config.RELAYS['light'], GPIO.LOW)
# #         light_state = "ON"
# #     else:
# #         GPIO.output(config.RELAYS['light'], GPIO.HIGH)

# #     # 4. FANS (Both Fans)
# #     if t > config.TARGET_TEMP:
# #         GPIO.output(config.RELAYS['fan_1'], GPIO.LOW)
# #         GPIO.output(config.RELAYS['fan_2'], GPIO.LOW)
# #         fan_state = "ON"
# #     else:
# #         GPIO.output(config.RELAYS['fan_1'], GPIO.HIGH)
# #         GPIO.output(config.RELAYS['fan_2'], GPIO.HIGH)

# #     # 5. WATER
# #     if time.time() - last_water_time > config.WATER_INTERVAL:
# #         pump_state = "ON"
# #         update_dashboard_file(t, h, ph_val, ec_val, light_state, fan_state, pump_state, safety_str)
# #         GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
# #         time.sleep(config.WATER_DURATION)
# #         GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
# #         last_water_time = time.time()
# #         pump_state = "OFF"

# #     # 6. CHEMISTRY (pH & EC Dosing)
# #     if time.time() - last_dose_time > config.DOSE_WAIT_TIME:
# #         # pH Logic
# #         if ph_val > 1.0:
# #             if ph_val > (config.TARGET_PH + config.PH_TOLERANCE):
# #                 GPIO.output(config.RELAYS['ph_down'], GPIO.LOW)
# #                 time.sleep(config.DOSE_DURATION)
# #                 GPIO.output(config.RELAYS['ph_down'], GPIO.HIGH)
# #                 last_dose_time = time.time()
# #             elif ph_val < (config.TARGET_PH - config.PH_TOLERANCE):
# #                 GPIO.output(config.RELAYS['ph_up'], GPIO.LOW)
# #                 time.sleep(config.DOSE_DURATION)
# #                 GPIO.output(config.RELAYS['ph_up'], GPIO.HIGH)
# #                 last_dose_time = time.time()
        
# #         # EC Logic (Nutrients)
# #         if time.time() - last_dose_time > config.DOSE_WAIT_TIME: # Re-check timer
# #              if ec_val < (config.TARGET_EC - config.EC_TOLERANCE):
# #                 # Add Nutrients A & B
# #                 GPIO.output(config.RELAYS['nutrient_a'], GPIO.LOW)
# #                 GPIO.output(config.RELAYS['nutrient_b'], GPIO.LOW)
# #                 time.sleep(config.DOSE_DURATION)
# #                 GPIO.output(config.RELAYS['nutrient_a'], GPIO.HIGH)
# #                 GPIO.output(config.RELAYS['nutrient_b'], GPIO.HIGH)
# #                 last_dose_time = time.time()

# #     # 7. UPDATE DASHBOARD & LOG
# #     update_dashboard_file(t, h, ph_val, ec_val, light_state, fan_state, pump_state, safety_str)
    
# #     status = f"T:{t} pH:{ph_val} EC:{ec_val}"
# #     print(f"[{now.strftime('%H:%M:%S')}] {status}") 
# #     if lcd:
# #         lcd.lcd_display_string(status, 1)
# #         lcd.lcd_display_string(f"H:{h}%", 2)

# # # --- MAIN LOOP ---
# # try:
# #     while True:
# #         run_control_loop()
# #         time.sleep(2)
# # except KeyboardInterrupt:
# #     GPIO.cleanup()
# #     if lcd: lcd.lcd_clear()



# import time
# import smbus2
# import json
# import threading
# import http.server
# import socketserver
# import webbrowser
# import os
# from datetime import datetime
# import config  # Import settings from config.py


# # --- HARDWARE ABSTRACTION LAYER (HAL) ---
# # This block ensures the code runs on Mac/PC without crashing


# # 1. Mock GPIO
# try:
#     import RPi.GPIO as GPIO
# except (ImportError, RuntimeError):
#     class GPIO:
#         BCM = "BCM"; OUT = "OUT"; HIGH = 1; LOW = 0
#         def setmode(mode): pass
#         def setup(pin, mode): pass
#         def output(pin, state): print(f"[MOCK] Pin {pin} -> {'HIGH' if state else 'LOW'}")
#         def cleanup(): pass


# # 2. Mock Board & Busio (Crucial for Mac)
# try:
#     import board
#     import busio
#     i2c = busio.I2C(board.SCL, board.SDA)
# except (ImportError, NotImplementedError, AttributeError) as e:
#     print("[SIMULATION] Board/Busio not detected. Running in PC Mode.")
#     board = None
#     busio = None
#     i2c = None


# # 3. Sensor Libraries
# try:
#     import adafruit_ads1x15.ads1115 as ADS
#     from adafruit_ads1x15.analog_in import AnalogIn
#     import adafruit_bme280  # ✅ FIX: correct import for Adafruit_BME280_I2C
# except (ImportError, NotImplementedError) as e:
#     print("[SIMULATION] Sensor libraries missing or incompatible.")
#     ADS = None
#     AnalogIn = None
#     adafruit_bme280 = None


# # Import ML Engine
# try:
#     from ml_engine import AnomalyDetector
#     ML_AVAILABLE = True
# except ImportError:
#     print("! ML Engine not found. Running in basic mode.")
#     ML_AVAILABLE = False


# # --- WEB SERVER LOGIC ---
# def start_web_server():
#     """Starts a simple HTTP server in a background thread."""
#     PORT = 8000
#     class QuietHandler(http.server.SimpleHTTPRequestHandler):
#         def log_message(self, format, *args): pass

#     try:
#         if not os.path.exists("stunning_dashboard.html"):
#             print("! Warning: stunning_dashboard.html not found.")

#         with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
#             print(f"-> Web Server Running: http://localhost:{PORT}")
#             httpd.serve_forever()
#     except OSError:
#         print(f"! Port {PORT} is busy. Server might already be running.")


# # --- SETUP ---
# print("System Booting...")

# GPIO.setmode(GPIO.BCM)

# # Setup Relays
# for name, pin in config.RELAYS.items():
#     GPIO.setup(pin, GPIO.OUT)
#     GPIO.output(pin, GPIO.HIGH)  # ALL OFF

# # Setup Sensors
# bme280 = None
# ads = None
# ph_chan = None
# ec_chan = None
# level_chan = None

# if i2c:
#     # BME280
#     if adafruit_bme280:
#         try:
#             bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
#         except Exception as e:
#             print(f"! Temp Sensor Missing / init failed: {e}")

#     # ADS1115
#     if ADS and AnalogIn:
#         try:
#             ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
#             ph_chan = AnalogIn(ads, config.CHAN_PH)
#             ec_chan = AnalogIn(ads, config.CHAN_EC)
#             level_chan = AnalogIn(ads, config.CHAN_LEVEL)
#         except Exception as e:
#             print(f"! ADS1115 Missing / init failed: {e}")

# # Setup ML
# detector = None
# if ML_AVAILABLE:
#     detector = AnomalyDetector()

# # LCD Class
# class I2C_LCD_driver:
#     def __init__(self, address):
#         if not i2c:
#             return
#         try:
#             self.bus = smbus2.SMBus(1)
#             self.address = address
#             self.lcd_write(0x03); self.lcd_write(0x03); self.lcd_write(0x03); self.lcd_write(0x02)
#             self.lcd_write(0x20|0x08|0x04|0x00); self.lcd_write(0x08|0x04); self.lcd_write(0x01); self.lcd_write(0x04|0x02)
#             time.sleep(0.2)
#         except Exception:
#             pass

#     def lcd_write(self, cmd, mode=0):
#         try:
#             self.lcd_write_four_bits(mode | (cmd & 0xF0))
#             self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))
#         except Exception:
#             pass

#     def lcd_write_four_bits(self, data):
#         try:
#             self.bus.write_byte(self.address, data | 0x08)
#             self.bus.write_byte(self.address, data | 0x08 | 0x04)
#             self.bus.write_byte(self.address, data | 0x08)
#         except Exception:
#             pass

#     def lcd_display_string(self, string, line):
#         if not i2c:
#             return
#         if line == 1:
#             self.lcd_write(0x80)
#         if line == 2:
#             self.lcd_write(0xC0)
#         for char in string:
#             self.lcd_write(ord(char), 1)

#     def lcd_clear(self):
#         if not i2c:
#             return
#         self.lcd_write(0x01)
#         time.sleep(0.005)

# lcd = None
# try:
#     lcd = I2C_LCD_driver(config.I2C_ADDR_LCD)
# except Exception:
#     pass


# # --- AUTO-LAUNCH DASHBOARD ---
# server_thread = threading.Thread(target=start_web_server, daemon=True)
# server_thread.start()
# time.sleep(1)
# webbrowser.open("http://localhost:8000/stunning_dashboard.html")


# # --- LOGIC ---
# last_water_time = 0
# last_dose_time = 0


# def get_ec(voltage):
#     if voltage < 0.1:
#         return 0.0
#     return round(voltage * 1.0, 2)


# def update_dashboard_file(temp, hum, ph, ec, light_s, fan_s, pump_s, safety_s):
#     data = {
#         "timestamp": datetime.now().strftime('%H:%M:%S'),
#         "temp": temp,
#         "hum": hum,
#         "ph": ph,
#         "ec": ec,
#         "light_state": light_s,
#         "fan_state": fan_s,
#         "pump_state": pump_s,
#         "safety": safety_s
#     }
#     try:
#         with open("dashboard.json", "w") as f:
#             json.dump(data, f)
#     except Exception:
#         pass


# def check_safety():
#     if not level_chan:
#         return True
#     if level_chan.voltage < config.MIN_WATER_VOLTAGE:
#         GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
#         return False
#     return True


# def run_control_loop():
#     global last_water_time, last_dose_time

#     # 1. READ SENSORS
#     t, h = (25.0, 50.0)
#     if bme280:
#         t, h = (round(bme280.temperature, 1), round(bme280.relative_humidity, 0))

#     ph_val = 6.0
#     if ph_chan:
#         v = ph_chan.voltage
#         slope = getattr(config, 'PH_SLOPE', -3.5)
#         intercept = getattr(config, 'PH_INTERCEPT', 15.75)
#         if v > 0.1:
#             ph_val = round((slope * v) + intercept, 2)

#     ec_val = 1.2
#     if ec_chan:
#         ec_val = get_ec(ec_chan.voltage)

#     # 2. SAFETY CHECK
#     is_safe = check_safety()
#     safety_str = "SAFE" if is_safe else "ALERT"
#     if not is_safe:
#         print("ALERT: Low Water!")
#         if lcd:
#             lcd.lcd_display_string("LOW WATER!", 1)
#         update_dashboard_file(t, h, ph_val, ec_val, "OFF", "OFF", "DISABLED", safety_str)
#         return

#     now = datetime.now()

#     light_state = "OFF"
#     fan_state = "OFF"
#     pump_state = "OFF"

#     # 3. LIGHTS
#     if config.LIGHT_START_HOUR <= now.hour < config.LIGHT_END_HOUR and t < config.TEMP_LIMIT:
#         GPIO.output(config.RELAYS['light'], GPIO.LOW)
#         light_state = "ON"
#     else:
#         GPIO.output(config.RELAYS['light'], GPIO.HIGH)

#     # 4. FANS (Both Fans)
#     if t > config.TARGET_TEMP:
#         GPIO.output(config.RELAYS['fan_1'], GPIO.LOW)
#         GPIO.output(config.RELAYS['fan_2'], GPIO.LOW)
#         fan_state = "ON"
#     else:
#         GPIO.output(config.RELAYS['fan_1'], GPIO.HIGH)
#         GPIO.output(config.RELAYS['fan_2'], GPIO.HIGH)

#     # 5. WATER
#     if time.time() - last_water_time > config.WATER_INTERVAL:
#         pump_state = "ON"
#         update_dashboard_file(t, h, ph_val, ec_val, light_state, fan_state, pump_state, safety_str)
#         GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
#         time.sleep(config.WATER_DURATION)
#         GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
#         last_water_time = time.time()
#         pump_state = "OFF"

#     # 6. CHEMISTRY (pH & EC Dosing)
#     if time.time() - last_dose_time > config.DOSE_WAIT_TIME:
#         # pH Logic
#         if ph_val > 1.0:
#             if ph_val > (config.TARGET_PH + config.PH_TOLERANCE):
#                 GPIO.output(config.RELAYS['ph_down'], GPIO.LOW)
#                 time.sleep(config.DOSE_DURATION)
#                 GPIO.output(config.RELAYS['ph_down'], GPIO.HIGH)
#                 last_dose_time = time.time()
#             elif ph_val < (config.TARGET_PH - config.PH_TOLERANCE):
#                 GPIO.output(config.RELAYS['ph_up'], GPIO.LOW)
#                 time.sleep(config.DOSE_DURATION)
#                 GPIO.output(config.RELAYS['ph_up'], GPIO.HIGH)
#                 last_dose_time = time.time()

#         # EC Logic (Nutrients)
#         if time.time() - last_dose_time > config.DOSE_WAIT_TIME:  # Re-check timer
#             if ec_val < (config.TARGET_EC - config.EC_TOLERANCE):
#                 GPIO.output(config.RELAYS['nutrient_a'], GPIO.LOW)
#                 GPIO.output(config.RELAYS['nutrient_b'], GPIO.LOW)
#                 time.sleep(config.DOSE_DURATION)
#                 GPIO.output(config.RELAYS['nutrient_a'], GPIO.HIGH)
#                 GPIO.output(config.RELAYS['nutrient_b'], GPIO.HIGH)
#                 last_dose_time = time.time()

#     # 7. UPDATE DASHBOARD & LOG
#     update_dashboard_file(t, h, ph_val, ec_val, light_state, fan_state, pump_state, safety_str)

#     status = f"T:{t} pH:{ph_val} EC:{ec_val}"
#     print(f"[{now.strftime('%H:%M:%S')}] {status}")
#     if lcd:
#         lcd.lcd_display_string(status, 1)
#         lcd.lcd_display_string(f"H:{h}%", 2)


# # --- MAIN LOOP ---
# try:
#     while True:
#         run_control_loop()
#         time.sleep(2)
# except KeyboardInterrupt:
#     GPIO.cleanup()
#     if lcd:
#         lcd.lcd_clear()

import time
import json
import os
import sys
import threading
import http.server
import socketserver
from datetime import datetime
import numpy as np

# --- PI 5 STABILITY PATCH ---
def reset_i2c():
    """Forces the Pi 5 to release I2C bus locks."""
    os.system("sudo modprobe -r i2c_bcm2835 && sudo modprobe i2c_bcm2835")
    time.sleep(1)

# --- IMPORTS ---
try:
    import RPi.GPIO as GPIO
    import board
    import busio
    from adafruit_bme280 import basic as adafruit_bme280
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    
    # Machine Learning Engine Integration
    from ml_engine import AnomalyDetector
except ImportError as e:
    print(f"!! Library Error: {e}. Ensure you ran the pip install commands.")
    sys.exit(1)

# --- PIN CONFIG (FROM YOUR PHOTO) ---
RELAYS = {
    'water_pump': 5, 'light': 6, 'fan_1': 13,
    'ph_down': 19, 'ph_up': 26, 'nutrient_a': 16,
    'nutrient_b': 20, 'fan_2': 21
}

# --- THRESHOLDS ---
TARGET_TEMP = 25.0
TARGET_PH = 6.0
PH_TOLERANCE = 0.5

# --- ML & DATA STORAGE ---
training_data = [] # Buffer for ML training
ML_TRAIN_THRESHOLD = 50 # Start AI after 50 samples

# Shared State for Dashboard
farm = {
    "timestamp": "", 
    "temp": 0.0, 
    "hum": 0.0, 
    "ph": 7.0, 
    "light_state": "OFF", 
    "fan_state": "OFF", 
    "pump_state": "OFF",
    "safety": "BOOTING",
    "ai_status": "COLLECTING DATA",
    "anomaly_flag": "NORMAL"
}

def init_hw():
    """Initializes GPIO and I2C Bus."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in RELAYS.values():
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
    
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        return i2c
    except Exception:
        reset_i2c()
        return busio.I2C(board.SCL, board.SDA)

def run_automation():
    global training_data
    i2c = init_hw()
    bme = None
    ads = None
    
    # Initialize ML Engine
    detector = AnomalyDetector()

    # Link Sensors
    try: 
        bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
        print("[OK] BME280 Connected.")
    except: print("!! BME280 Missing")
    
    try: 
        ads = ADS.ADS1115(i2c, address=0x48)
        print("[OK] ADS1115 Connected.")
    except: print("!! ADS1115 Missing")

    print("\n--- Automation & AI Monitoring Active ---")
    while True:
        try:
            # 1. READ SENSORS
            current_temp = 0.0
            current_hum = 0.0
            current_ph = 7.0

            if bme:
                current_temp = round(bme.temperature, 1)
                current_hum = round(bme.relative_humidity, 0)
                farm["temp"] = current_temp
                farm["hum"] = current_hum
            
            if ads:
                # Using 0 for channel A0 to avoid P0 attribute error
                ph_v = AnalogIn(ads, 0).voltage
                current_ph = round(((-3.8) * ph_v) + 15.5, 2)
                farm["ph"] = current_ph

            # 2. MACHINE LEARNING LOGIC
            # Append to training buffer
            training_data.append([current_temp, current_hum, current_ph])
            
            # Check if we need to train the model
            if not detector.trained and len(training_data) >= ML_TRAIN_THRESHOLD:
                detector.train(training_data)
                farm["ai_status"] = "MODEL TRAINED"
            
            # Perform Prediction if trained
            if detector.trained:
                prediction = detector.predict([current_temp, current_hum, current_ph])
                if prediction == -1:
                    farm["anomaly_flag"] = "ANOMALY DETECTED"
                    farm["ai_status"] = "WARNING: UNUSUAL PATTERN"
                else:
                    farm["anomaly_flag"] = "NORMAL"
                    farm["ai_status"] = "AI MONITORING ACTIVE"

            # 3. AUTOMATION LOGIC: FANS
            if farm["temp"] > TARGET_TEMP:
                GPIO.output(RELAYS['fan_1'], GPIO.LOW)
                GPIO.output(RELAYS['fan_2'], GPIO.LOW)
                farm["fan_state"] = "ON"
            else:
                GPIO.output(RELAYS['fan_1'], GPIO.HIGH)
                GPIO.output(RELAYS['fan_2'], GPIO.HIGH)
                farm["fan_state"] = "OFF"

            # 4. LOGIC: LIGHTS
            # Example logic: Lights stay ON while loop runs
            GPIO.output(RELAYS['light'], GPIO.LOW)
            farm["light_state"] = "ON"

            # 5. SAFETY & DASHBOARD UPDATES
            farm["timestamp"] = datetime.now().strftime("%H:%M:%S")
            farm["safety"] = "SAFE"
            
            with open("dashboard.json", "w") as f:
                json.dump(farm, f)

            # Print status to terminal
            ml_tag = f"[{farm['ai_status']}]"
            print(f"[{farm['timestamp']}] T:{farm['temp']}C | pH:{farm['ph']} | {ml_tag}      ", end='\r')
            
            time.sleep(2)

        except KeyboardInterrupt: 
            print("\nShutting down gracefully...")
            break
        except Exception as e:
            print(f"\nCycle Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    # Start Web Dashboard Server (Port 8000)
    threading.Thread(target=lambda: socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler).serve_forever(), daemon=True).start()
    
    try:
        run_automation()
    finally:
        # Emergency Shutdown: Turn everything OFF (HIGH)
        for pin in RELAYS.values(): 
            GPIO.output(pin, GPIO.HIGH)
        GPIO.cleanup()
        print("\nSystem Secured.")