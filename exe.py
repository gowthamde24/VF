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

# --- NEW: EC POWER PIN ---
EC_POWER_PIN = 27 # The GPIO pin powering the EC Sensor

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
    for key in RELAYS:
        GPIO.setup(RELAYS[key]["pin"], GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(config.WATER_LEVEL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    # Setup EC Power Pin
    GPIO.setup(EC_POWER_PIN, GPIO.OUT, initial=GPIO.LOW)

def get_readings(i2c):
    res = {"temp": "N/A", "hum": "N/A", "ph_v": "N/A", "ec_v": "N/A", "water": "N/A"}
    
    try:
        bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
        res["temp"] = f"{bme.temperature:.1f}C"
        res["hum"] = f"{bme.relative_humidity:.0f}%"
    except: res["temp"] = "BME ERROR"

    try:
        ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
        ph_chan = AnalogIn(ads, config.CHAN_PH) 
        ec_chan = AnalogIn(ads, config.CHAN_EC)
        
        # --- SOFTWARE GALVANIC ISOLATION SEQUENCE ---
        # 1. Power ON the EC Sensor
        GPIO.output(EC_POWER_PIN, GPIO.HIGH)
        time.sleep(0.5) # Wait half a second for EC sensor to boot and stabilize
        res["ec_v"] = f"{ec_chan.voltage:.4f}V"
        
        # 2. Power OFF the EC Sensor
        GPIO.output(EC_POWER_PIN, GPIO.LOW)
        time.sleep(0.5) # Wait half a second for electricity to dissipate from the water
        
        # 3. Read the pH Sensor (while EC is totally dead)
        res["ph_v"] = f"{ph_chan.voltage:.4f}V"
        
    except Exception as e:
        res["ph_v"] = "ADC ERROR"
        res["ec_v"] = "ADC ERROR"

    is_full = (GPIO.input(config.WATER_LEVEL_PIN) == GPIO.HIGH)
    res["water"] = "FULL (LED ON)" if is_full else "EMPTY"
    
    return res

def toggle(key, force=None):
    if key not in RELAYS: return
    pin = RELAYS[key]["pin"]
    new_state = force if force is not None else not (RELAYS[key]["state"] == "ON")
    GPIO.output(pin, GPIO.LOW if new_state else GPIO.HIGH)
    RELAYS[key]["state"] = "ON" if new_state else "OFF"

if __name__ == "__main__":
    setup_hardware()
    i2c = busio.I2C(board.SCL, board.SDA)
    
    try:
        while True:
            os.system('clear')
            data = get_readings(i2c)
            print("==================================================")
            print("   GROW SMART OS - MASTER DIAGNOSTICS")
            print("==================================================")
            print(f" [CLIMATE]  Temp: {data['temp']: <12} | Hum: {data['hum']}")
            print(f" [ANALOG]   pH (A0): {data['ph_v']: <9} | EC (A1): {data['ec_v']}")
            print(f" [DIGITAL]  Water: {data['water']}")
            print("--------------------------------------------------")
            print(" ID | ACTUATOR     | GPIO | STATUS")
            print("----|--------------|------|-----------------------")
            for key in sorted(RELAYS.keys(), key=int):
                d = RELAYS[key]
                print(f" {key: <2} | {d['name']: <12} | {d['pin']: <4} | {d['state']}")
            print("--------------------------------------------------")
            print(" [1-8] Toggle | [A] All ON | [O] All OFF | [Q] Quit")
            print("==================================================")
            
            # Simple non-blocking input
            import select
            r, _, _ = select.select([sys.stdin], [], [], 1.0)
            if r:
                cmd = sys.stdin.readline().strip().upper()
                if cmd in RELAYS: toggle(cmd)
                elif cmd == "A": [toggle(k, True) for k in RELAYS]
                elif cmd == "O": [toggle(k, False) for k in RELAYS]
                elif cmd == "Q": break
    finally:
        for k in RELAYS: toggle(k, False)
        GPIO.cleanup()