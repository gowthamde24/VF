import os
import sys
import time
import subprocess
import config

# --- I2C RECOVERY ---
def reset_i2c():
    subprocess.run(["sudo", "modprobe", "-r", "i2c_bcm2835"], capture_output=True)
    subprocess.run(["sudo", "modprobe", "i2c_bcm2835"], capture_output=True)
    time.sleep(1)

try:
    import RPi.GPIO as GPIO
    import board
    import busio
    from adafruit_bme280 import basic as adafruit_bme280
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except ImportError:
    print("!! Missing libraries. Run pip install commands.")
    sys.exit(1)

# --- DYNAMIC PIN MAPPING (FROM CONFIG.PY) ---
# We map your config string names to UI button numbers (1-8) and clean display names
MAPPING = [
    ("1", "water_pump", "Water Pump"),
    ("2", "light",      "Light"),
    ("3", "fan_1",      "Fan 1"),
    ("4", "ph_down",    "pH Down"),
    ("5", "ph_up",      "pH Up"),
    ("6", "nutrient_a", "Nutrient A"),
    ("7", "nutrient_b", "Nutrient B"),
    ("8", "fan_2",      "Fan 2")
]

RELAYS = {}
for cmd_id, config_key, display_name in MAPPING:
    if config_key in config.RELAYS:
        RELAYS[cmd_id] = {
            "name": display_name,
            "pin": config.RELAYS[config_key],
            "state": "OFF"
        }

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for key in RELAYS:
        # HIGH is OFF for active-low relay boards
        GPIO.setup(RELAYS[key]["pin"], GPIO.OUT, initial=GPIO.HIGH)

def draw_ui(i2c):
    os.system('clear')
    print("==================================================")
    print("   VERTICAL FARM - SYSTEM DIAGNOSTICS (PI 4/5)    ")
    print("==================================================")
    
    # Read Sensors using config.py addresses
    temp, hum = "N/A", "N/A"
    v0, v1, v2 = "N/A", "N/A", "N/A"
    
    try:
        bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
        temp, hum = f"{bme.temperature:.1f}C", f"{bme.relative_humidity:.1f}%"
    except: pass

    try:
        ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
        v0 = f"{AnalogIn(ads, config.CHAN_PH).voltage:.3f}V"
        v1 = f"{AnalogIn(ads, config.CHAN_EC).voltage:.3f}V"
        v2 = f"{AnalogIn(ads, config.CHAN_LEVEL).voltage:.3f}V"
    except: pass

    print(f" CLIMATE | Temp: {temp} | Hum: {hum}")
    print(f" ANALOG  | pH (A{config.CHAN_PH}): {v0} | EC (A{config.CHAN_EC}): {v1} | Lvl (A{config.CHAN_LEVEL}): {v2}")
    print("--------------------------------------------------")
    print(" ID | Device       | GPIO | Status")
    print("----|--------------|------|-----------------------")
    for key in sorted(RELAYS.keys(), key=int):
        data = RELAYS[key]
        status = "[  ON  ]" if data["state"] == "ON" else "[  OFF ]"
        print(f" {key: <2} | {data['name']: <12} | {data['pin']: <4} | {status}")
    print("--------------------------------------------------")
    print(" [1-8] Toggle | [A] All ON | [O] All OFF | [Q] Quit")
    print("==================================================")

def toggle(key, force=None):
    pin = RELAYS[key]["pin"]
    is_on = RELAYS[key]["state"] == "ON"
    new_state = force if force is not None else not is_on
    
    GPIO.output(pin, GPIO.LOW if new_state else GPIO.HIGH)
    RELAYS[key]["state"] = "ON" if new_state else "OFF"

if __name__ == "__main__":
    if os.getuid() != 0:
        print("!! Run with sudo (e.g., sudo env/bin/python diagnostics.py)")
        sys.exit(1)

    setup_gpio()
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
    except:
        reset_i2c()
        i2c = busio.I2C(board.SCL, board.SDA)

    try:
        while True:
            draw_ui(i2c)
            cmd = input("Command: ").upper()
            if cmd in RELAYS:
                toggle(cmd)
            elif cmd == "A":
                for k in RELAYS: toggle(k, True)
            elif cmd == "O":
                for k in RELAYS: toggle(k, False)
            elif cmd == "Q":
                break
    finally:
        for k in RELAYS: toggle(k, False)
        GPIO.cleanup()
        print("All relays shut off. Exiting.")