# import os
# import sys
# import time
# import subprocess
# import config

# # --- I2C RECOVERY ---
# def reset_i2c():
#     subprocess.run(["sudo", "modprobe", "-r", "i2c_bcm2835"], capture_output=True)
#     subprocess.run(["sudo", "modprobe", "i2c_bcm2835"], capture_output=True)
#     time.sleep(1)

# try:
#     import RPi.GPIO as GPIO
#     import board
#     import busio
#     from adafruit_bme280 import basic as adafruit_bme280
#     import adafruit_ads1x15.ads1115 as ADS
#     from adafruit_ads1x15.analog_in import AnalogIn
# except ImportError:
#     print("!! Missing libraries. Run pip install commands.")
#     sys.exit(1)

# # --- DYNAMIC PIN MAPPING (FROM CONFIG.PY) ---
# # We map your config string names to UI button numbers (1-8) and clean display names
# MAPPING = [
#     ("1", "water_pump", "Water Pump"),
#     ("2", "light",      "Light"),
#     ("3", "fan_1",      "Fan 1"),
#     ("4", "ph_down",    "pH Down"),
#     ("5", "ph_up",      "pH Up"),
#     ("6", "nutrient_a", "Nutrient A"),
#     ("7", "nutrient_b", "Nutrient B"),
#     ("8", "fan_2",      "Fan 2")
# ]

# RELAYS = {}
# for cmd_id, config_key, display_name in MAPPING:
#     if config_key in config.RELAYS:
#         RELAYS[cmd_id] = {
#             "name": display_name,
#             "pin": config.RELAYS[config_key],
#             "state": "OFF"
#         }

# def setup_gpio():
#     GPIO.setmode(GPIO.BCM)
#     GPIO.setwarnings(False)
#     for key in RELAYS:
#         # HIGH is OFF for active-low relay boards
#         GPIO.setup(RELAYS[key]["pin"], GPIO.OUT, initial=GPIO.HIGH)

# def draw_ui(i2c):
#     os.system('clear')
#     print("==================================================")
#     print("   VERTICAL FARM - SYSTEM DIAGNOSTICS (PI 4/5)    ")
#     print("==================================================")
    
#     # Read Sensors using config.py addresses
#     temp, hum = "N/A", "N/A"
#     v0, v1, v2 = "N/A", "N/A", "N/A"
    
#     try:
#         bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
#         temp, hum = f"{bme.temperature:.1f}C", f"{bme.relative_humidity:.1f}%"
#     except: pass

#     try:
#         ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
#         v0 = f"{AnalogIn(ads, config.CHAN_PH).voltage:.3f}V"
#         v1 = f"{AnalogIn(ads, config.CHAN_EC).voltage:.3f}V"
#         v2 = f"{AnalogIn(ads, config.CHAN_LEVEL).voltage:.3f}V"
#     except: pass

#     print(f" CLIMATE | Temp: {temp} | Hum: {hum}")
#     print(f" ANALOG  | pH (A{config.CHAN_PH}): {v0} | EC (A{config.CHAN_EC}): {v1} | Lvl (A{config.CHAN_LEVEL}): {v2}")
#     print("--------------------------------------------------")
#     print(" ID | Device       | GPIO | Status")
#     print("----|--------------|------|-----------------------")
#     for key in sorted(RELAYS.keys(), key=int):
#         data = RELAYS[key]
#         status = "[  ON  ]" if data["state"] == "ON" else "[  OFF ]"
#         print(f" {key: <2} | {data['name']: <12} | {data['pin']: <4} | {status}")
#     print("--------------------------------------------------")
#     print(" [1-8] Toggle | [A] All ON | [O] All OFF | [Q] Quit")
#     print("==================================================")

# def toggle(key, force=None):
#     pin = RELAYS[key]["pin"]
#     is_on = RELAYS[key]["state"] == "ON"
#     new_state = force if force is not None else not is_on
    
#     GPIO.output(pin, GPIO.LOW if new_state else GPIO.HIGH)
#     RELAYS[key]["state"] = "ON" if new_state else "OFF"

# if __name__ == "__main__":
#     if os.getuid() != 0:
#         print("!! Run with sudo (e.g., sudo env/bin/python diagnostics.py)")
#         sys.exit(1)

#     setup_gpio()
#     try:
#         i2c = busio.I2C(board.SCL, board.SDA)
#     except:
#         reset_i2c()
#         i2c = busio.I2C(board.SCL, board.SDA)

#     try:
#         while True:
#             draw_ui(i2c)
#             cmd = input("Command: ").upper()
#             if cmd in RELAYS:
#                 toggle(cmd)
#             elif cmd == "A":
#                 for k in RELAYS: toggle(k, True)
#             elif cmd == "O":
#                 for k in RELAYS: toggle(k, False)
#             elif cmd == "Q":
#                 break
#     finally:
#         for k in RELAYS: toggle(k, False)
#         GPIO.cleanup()
#         print("All relays shut off. Exiting.")

import os
import sys
import time
import subprocess
import RPi.GPIO as GPIO
import board
import busio
import config
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_bme280 import basic as adafruit_bme280

# --- I2C RECOVERY ---
def scan_i2c():
    """Scans the bus for device addresses and returns a string grid."""
    try:
        result = subprocess.run(["i2cdetect", "-y", "1"], capture_output=True, text=True)
        return result.stdout
    except:
        return "i2cdetect not available."

# --- DYNAMIC PIN MAPPING ---
MAPPING = [
    ("1", "water_pump", "Main Pump"),
    ("2", "light",      "Grow Lights"),
    ("3", "fan_1",      "Intake Fan"),
    ("4", "ph_down",    "pH Down (Acid)"),
    ("5", "ph_up",      "pH Up (Base)"),
    ("6", "nutrient_a", "Nutrient A"),
    ("7", "nutrient_b", "Nutrient B"),
    ("8", "fan_2",      "Exhaust Fan")
]

RELAYS = {}
for cmd_id, config_key, display_name in MAPPING:
    if config_key in config.RELAYS:
        RELAYS[cmd_id] = {
            "name": display_name,
            "pin": config.RELAYS[config_key],
            "state": "OFF"
        }

def setup_hardware():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    # Initialize Relays (HIGH = OFF)
    for key in RELAYS:
        GPIO.setup(RELAYS[key]["pin"], GPIO.OUT, initial=GPIO.HIGH)
    
    # Digital Level Sensor: LED ON = HIGH Logic
    GPIO.setup(config.WATER_LEVEL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def get_readings(i2c):
    res = {"temp": "OFFLINE", "hum": "N/A", "ph_v": "OFFLINE", "ec_v": "N/A", "water": "N/A"}
    
    # 1. BME280 Climate
    try:
        bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
        res["temp"] = f"{bme.temperature:.1f}C"
        res["hum"] = f"{bme.relative_humidity:.0f}%"
    except:
        res["temp"] = "NOT FOUND"

    # 2. ADS1115 Analog (Strictly Single-Ended A0/A1)
    try:
        ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
        # A2 and A3 are intentionally ignored to prevent bus crashes
        ph_chan = AnalogIn(ads, ADS.P0) 
        ec_chan = AnalogIn(ads, config.CHAN_EC)
        res["ph_v"] = f"{ph_chan.voltage:.3f}V"
        res["ec_v"] = f"{ec_chan.voltage:.3f}V"
    except:
        res["ph_v"] = "NOT FOUND"

    # 3. Digital Level
    try:
        is_full = (GPIO.input(config.WATER_LEVEL_PIN) == GPIO.HIGH)
        res["water"] = "FULL (LED ON)" if is_full else "EMPTY"
    except:
        res["water"] = "GPIO Error"
    
    return res

def draw_ui(readings):
    os.system('clear')
    print("==================================================")
    print("   GROW SMART OS - FULL SYSTEM DIAGNOSTICS")
    print("   (Stable Single-Ended Mode | A2/A3 Disabled)")
    print("==================================================")
    print(f" [CLIMATE]  Temp: {readings['temp']: <12} | Hum: {readings['hum']}")
    print(f" [ANALOG]   pH (A0): {readings['ph_v']: <9} | EC (A1): {readings['ec_v']}")
    print(f" [DIGITAL]  Water: {readings['water']}")
    print("--------------------------------------------------")
    print(" ID | ACTUATOR     | GPIO | STATUS")
    print("----|--------------|------|-----------------------")
    for key in sorted(RELAYS.keys(), key=int):
        data = RELAYS[key]
        status = "[  ON  ]" if data["state"] == "ON" else "[  OFF ]"
        print(f" {key: <2} | {data['name']: <12} | {data['pin']: <4} | {status}")
    print("--------------------------------------------------")
    print(" BUS SCAN:")
    print(scan_i2c().strip())
    print("--------------------------------------------------")
    print(" [1-8] Toggle Device | [A] All ON | [O] All OFF | [Q] Quit")
    print("==================================================")

def toggle(key, force=None):
    if key not in RELAYS: return
    pin = RELAYS[key]["pin"]
    is_on = (RELAYS[key]["state"] == "ON")
    new_state = force if force is not None else not is_on
    GPIO.output(pin, GPIO.LOW if new_state else GPIO.HIGH)
    RELAYS[key]["state"] = "ON" if new_state else "OFF"

if __name__ == "__main__":
    setup_hardware()
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
    except:
        print("!! I2C Initialization Failed. Check Wiring on Pins 3/5.")
        sys.exit(1)

    try:
        while True:
            data = get_readings(i2c)
            draw_ui(data)
            # Use a short timeout for input to keep sensors refreshing
            print("Command: ", end="", flush=True)
            import select
            rlist, _, _ = select.select([sys.stdin], [], [], 1.5)
            if rlist:
                cmd = sys.stdin.readline().strip().upper()
                if cmd in RELAYS: toggle(cmd)
                elif cmd == "A":
                    for k in RELAYS: toggle(k, True)
                elif cmd == "O":
                    for k in RELAYS: toggle(k, False)
                elif cmd == "Q": break
    except KeyboardInterrupt:
        pass
    finally:
        for k in RELAYS: toggle(k, False)
        GPIO.cleanup()
        print("\nSafety shutdown complete.")