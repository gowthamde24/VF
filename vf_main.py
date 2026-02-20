


# import time
# import json
# import threading
# import http.server
# import socketserver
# import webbrowser
# import os
# from datetime import datetime
# import config  # Import settings from config.py

# # --- NATIVE RASPBERRY PI IMPORTS ---
# import RPi.GPIO as GPIO
# import board
# import busio
# import adafruit_ads1x15.ads1115 as ADS
# from adafruit_ads1x15.analog_in import AnalogIn
# from adafruit_bme280 import basic as adafruit_bme280
# from ml_engine import AnomalyDetector

# # --- WEB SERVER LOGIC ---
# def start_web_server():
#     """Starts a simple HTTP server in a background thread for the dashboard."""
#     PORT = 8000
#     class QuietHandler(http.server.SimpleHTTPRequestHandler):
#         def log_message(self, format, *args): pass # Mutes the server access logs
            
#     try:
#         with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
#             print(f"-> Web Server Running: http://localhost:{PORT}")
#             httpd.serve_forever()
#     except OSError:
#         pass # Port already in use, silently continue

# # --- SETUP ---
# print("System Booting (Production Mode)...")

# GPIO.setmode(GPIO.BCM)
# GPIO.setwarnings(False)

# # Initialize all relays from config
# for name, pin in config.RELAYS.items():
#     GPIO.setup(pin, GPIO.OUT)
#     GPIO.output(pin, GPIO.HIGH) # ALL RELAYS OFF

# # Initialize I2C
# i2c = busio.I2C(board.SCL, board.SDA)

# # Initialize Climate Sensor
# bme280 = None
# try:
#     bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
#     print("-> Climate Sensor connected.")
# except Exception as e:
#     print(f"! Climate Sensor Error: {e}")

# # Initialize ADC & Probes
# ads, ph_chan, ec_chan, level_chan = None, None, None, None
# try:
#     ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
#     ph_chan = AnalogIn(ads, config.CHAN_PH)
#     ec_chan = AnalogIn(ads, config.CHAN_EC)
#     level_chan = AnalogIn(ads, config.CHAN_LEVEL)
#     print("-> Chemistry ADC connected.")
# except Exception as e:
#     print(f"! ADC Analog Error: {e}")

# detector = AnomalyDetector()

# # Launch Dashboard Server
# threading.Thread(target=start_web_server, daemon=True).start()

# # --- LOGIC VARIABLES ---
# last_water_time = time.time()
# last_dose_time = 0
# is_watering = False
# water_start_time = 0

# def update_dashboard_file(temp, hum, ph, ec, light_s, fan_s, pump_s, safety_s, activity_s, ml_data=None):
#     """Writes the current state to dashboard.json for the UI to read."""
#     data = {
#         "timestamp": datetime.now().strftime('%H:%M:%S'),
#         "temp": temp, "hum": hum, "ph": ph, "ec": ec, 
#         "light_state": light_s, "fan_state": fan_s, "pump_state": pump_s,
#         "safety": safety_s, "activity": activity_s,
#         "ml": ml_data if ml_data else {"health_score": 100, "status": "OK", "prediction": "Initializing..."}
#     }
#     try:
#         with open("dashboard.json", "w") as f:
#             json.dump(data, f)
#     except: pass

# def run_control_loop():
#     global last_water_time, last_dose_time, is_watering, water_start_time
    
#     # --- 1. READ SENSORS ---
#     t, h = (25.0, 50.0) # Fallback values
#     if bme280: 
#         t = round(bme280.temperature, 1)
#         h = round(bme280.relative_humidity, 0)
    
#     ph_val = 6.0 
#     if ph_chan:
#         v = ph_chan.voltage
#         ph_val = round((config.PH_SLOPE * v) + config.PH_INTERCEPT, 2)

#     ec_val = 1.2 
#     if ec_chan:
#         ec_val = round(ec_chan.voltage * 1.0, 2)

#     # --- 2. SAFETY CHECK ---
#     is_safe = True
#     if level_chan and level_chan.voltage < config.MIN_WATER_VOLTAGE:
#         # EMERGENCY SHUTOFF
#         for pump in ['water_pump', 'ph_down', 'ph_up', 'nutrient_a', 'nutrient_b']:
#             GPIO.output(config.RELAYS[pump], GPIO.HIGH)
#         is_safe = False
    
#     safety_str = "SAFE" if is_safe else "ALERT"
#     ml_data = detector.analyze({'temp': t, 'hum': h, 'ph': ph_val, 'ec': ec_val})

#     if not is_safe:
#         current_activity = "CRITICAL: LOW WATER"
#         update_dashboard_file(t, h, ph_val, ec_val, "OFF", "OFF", "DISABLED", safety_str, current_activity, ml_data)
#         return

#     now = datetime.now()
#     cur_time = time.time()
    
#     light_state, fan_state, pump_state = "OFF", "OFF", "OFF"
#     current_activity = "Monitoring" # Default activity

#     # --- 3. LIGHTS (8-Hour Cycle) ---
#     if config.LIGHT_START_HOUR <= now.hour < config.LIGHT_END_HOUR:
#         GPIO.output(config.RELAYS['light'], GPIO.LOW)
#         light_state = "ON"
#     else:
#         GPIO.output(config.RELAYS['light'], GPIO.HIGH)

#     # --- 4. FANS ---
#     if t > config.TARGET_TEMP:
#         GPIO.output(config.RELAYS['fan_1'], GPIO.LOW)
#         GPIO.output(config.RELAYS['fan_2'], GPIO.LOW)
#         fan_state = "ON"
#         current_activity = "Cooling" # Triggers Fan Icon in UI
#     else:
#         GPIO.output(config.RELAYS['fan_1'], GPIO.HIGH)
#         GPIO.output(config.RELAYS['fan_2'], GPIO.HIGH)

#     # --- 5. WATER CYCLE (Non-Blocking) ---
#     if not is_watering and (cur_time - last_water_time > config.WATER_INTERVAL):
#         is_watering = True
#         water_start_time = cur_time
#         GPIO.output(config.RELAYS['water_pump'], GPIO.LOW)
#     elif is_watering and (cur_time - water_start_time > config.WATER_DURATION):
#         is_watering = False
#         last_water_time = cur_time
#         GPIO.output(config.RELAYS['water_pump'], GPIO.HIGH)
    
#     if is_watering: 
#         pump_state = "ON"
#         current_activity = "Irrigation" # Triggers Pump Icon in UI

#     # --- 6. INDIVIDUAL PUMP DOSING ---
#     # Prioritize dosing messages in the UI by checking them last
#     if cur_time - last_dose_time > config.DOSE_WAIT_TIME:
#         dosed = False
        
#         # pH Down
#         if ph_val > (config.TARGET_PH + config.PH_TOLERANCE):
#             current_activity = "Dosing: pH Down" # Triggers pH Down Icon in UI
#             update_dashboard_file(t, h, ph_val, ec_val, light_state, fan_state, pump_state, safety_str, current_activity, ml_data)
            
#             GPIO.output(config.RELAYS['ph_down'], GPIO.LOW)
#             time.sleep(config.PH_DOWN_DURATION)
#             GPIO.output(config.RELAYS['ph_down'], GPIO.HIGH)
#             dosed = True
        
#         # pH Up
#         elif ph_val < (config.TARGET_PH - config.PH_TOLERANCE):
#             current_activity = "Dosing: pH Up" # Triggers pH Up Icon in UI
#             update_dashboard_file(t, h, ph_val, ec_val, light_state, fan_state, pump_state, safety_str, current_activity, ml_data)
            
#             GPIO.output(config.RELAYS['ph_up'], GPIO.LOW)
#             time.sleep(config.PH_UP_DURATION)
#             GPIO.output(config.RELAYS['ph_up'], GPIO.HIGH)
#             dosed = True
        
#         # Nutrients (A then B)
#         elif not dosed and ec_val < (config.TARGET_EC - config.EC_TOLERANCE):
#             current_activity = "Dosing: Nutrients" # Triggers Nutrient Icon in UI
#             update_dashboard_file(t, h, ph_val, ec_val, light_state, fan_state, pump_state, safety_str, current_activity, ml_data)
            
#             GPIO.output(config.RELAYS['nutrient_a'], GPIO.LOW)
#             time.sleep(config.NUTRI_A_DURATION)
#             GPIO.output(config.RELAYS['nutrient_a'], GPIO.HIGH)
            
#             time.sleep(1) # Hardware safety pause
            
#             GPIO.output(config.RELAYS['nutrient_b'], GPIO.LOW)
#             time.sleep(config.NUTRI_B_DURATION)
#             GPIO.output(config.RELAYS['nutrient_b'], GPIO.HIGH)
#             dosed = True
            
#         if dosed: 
#             last_dose_time = cur_time

#     # --- 7. EXPORT & CONSOLE LOG ---
#     update_dashboard_file(t, h, ph_val, ec_val, light_state, fan_state, pump_state, safety_str, current_activity, ml_data)
#     print(f"[{now.strftime('%H:%M:%S')}] {current_activity} | T:{t}°C pH:{ph_val} EC:{ec_val}", end='\r')

# # --- MAIN EXECUTION ---
# try:
#     while True:
#         run_control_loop()
#         time.sleep(2)
# except KeyboardInterrupt:
#     print("\nShutting down... turning off all relays.")
#     GPIO.cleanup()


