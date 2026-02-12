# import time
# import sys
# import config  # Import your actual settings

# # --- HARDWARE ABSTRACTION (Mac/PC Compatibility) ---
# try:
#     import RPi.GPIO as GPIO
#     import board
#     import busio
#     import smbus2
# except (ImportError, RuntimeError, NotImplementedError):
#     print("! Hardware libraries not found. Running in SIMULATION MODE.")
    
#     # Mock GPIO Class
#     class GPIO:
#         BCM = "BCM"; OUT = "OUT"; HIGH = 1; LOW = 0
#         _pins = {}
#         @classmethod
#         def setmode(cls, mode): pass
#         @classmethod
#         def setup(cls, pin, mode): cls._pins[pin] = cls.HIGH
#         @classmethod
#         def output(cls, pin, state): 
#             cls._pins[pin] = state
#             print(f"  [MOCK] GPIO {pin} -> {'HIGH (OFF)' if state else 'LOW (ON)'}")
#         @classmethod
#         def input(cls, pin): return cls._pins.get(pin, cls.HIGH)
#         @classmethod
#         def cleanup(cls): pass
    
#     # Mock Board/Busio
#     class board: SCL = 1; SDA = 2
#     class busio:
#         class I2C:
#             def __init__(self, scl, sda): pass

# # Sensor Libraries (Try/Except)
# try:
#     import adafruit_ads1x15.ads1115 as ADS
#     from adafruit_ads1x15.analog_in import AnalogIn
#     from adafruit_bme280 import basic as adafruit_bme280
# except ImportError:
#     ADS = None
#     adafruit_bme280 = None

# # --- HARDWARE SETUP ---
# GPIO.setmode(GPIO.BCM)

# # Initialize I2C
# i2c = None
# try:
#     i2c = busio.I2C(board.SCL, board.SDA)
# except:
#     pass

# # Setup Relays from Config
# # Note: We do NOT reset them to HIGH here to preserve state if script restarts,
# # but for initial run, we ensure they are known.
# for name, pin in config.RELAYS.items():
#     GPIO.setup(pin, GPIO.OUT)
#     # We don't force them OFF here to allow inspecting current state,
#     # but initially they might be floating. 
#     # Usually safer to start OFF in a diagnostic tool unless we read state.
#     if GPIO.input(pin) not in [GPIO.LOW, GPIO.HIGH]:
#         GPIO.output(pin, GPIO.HIGH) 

# # --- TEST FUNCTIONS ---

# def test_single_relay():
#     while True:
#         print("\n--- Manual Relay Control (Toggle Mode) ---")
#         # Create a numbered list from config
#         relay_list = list(config.RELAYS.items()) 
        
#         # Display Status
#         print(f"{'#':<3} {'DEVICE NAME':<20} {'GPIO':<6} {'STATUS'}")
#         print("-" * 40)
#         for i, (name, pin) in enumerate(relay_list):
#             # Read current state (Active LOW logic: 0=ON, 1=OFF)
#             is_on = GPIO.input(pin) == GPIO.LOW 
#             status = " [ON] ✅" if is_on else " [OFF] ❌"
#             print(f"{i+1:<3} {name.upper():<20} {pin:<6} {status}")
#         print("-" * 40)
#         print(" Enter number to toggle state (1-8)")
#         print(" 9. Back to Main Menu")
        
#         choice = input("\nSelect > ")
#         if choice == '9': break
        
#         try:
#             idx = int(choice) - 1
#             if 0 <= idx < len(relay_list):
#                 name, pin = relay_list[idx]
                
#                 # Toggle Logic
#                 if GPIO.input(pin) == GPIO.LOW: # It's ON
#                     print(f"--> Turning OFF {name}...")
#                     GPIO.output(pin, GPIO.HIGH)
#                 else: # It's OFF
#                     print(f"--> Turning ON {name}...")
#                     GPIO.output(pin, GPIO.LOW)
#             else:
#                 print("Invalid number.")
#         except ValueError:
#             pass

# def test_all_relays():
#     print("\n--- Cycling ALL Relays (Sequence) ---")
#     print("This will turn each relay ON for 0.5s then OFF.")
#     for name, pin in config.RELAYS.items():
#         print(f"Testing {name} (GPIO {pin})...")
#         GPIO.output(pin, GPIO.LOW)  # ON
#         time.sleep(0.5)
#         GPIO.output(pin, GPIO.HIGH) # OFF
#         time.sleep(0.2)
#     print("Cycle Complete.")

# def read_bme280():
#     print("\n--- BME280 Environment ---")
#     if i2c and adafruit_bme280:
#         try:
#             bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
#             print(f"Temperature: {bme.temperature:.1f} °C")
#             print(f"Humidity:    {bme.relative_humidity:.1f} %")
#             print(f"Pressure:    {bme.pressure:.1f} hPa")
#         except Exception as e:
#             print(f"Error: {e}")
#     else:
#         print("[SIMULATION] Temp: 25.5°C | Hum: 60%")
#     input("Press Enter to continue...")

# def read_ph():
#     print("\n--- pH Sensor Reading (Continuous) ---")
#     print("Press CTRL+C to stop reading.\n")
#     if i2c and ADS:
#         try:
#             ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
#             chan = AnalogIn(ads, config.CHAN_PH)
            
#             slope = getattr(config, 'PH_SLOPE', -3.5)
#             intercept = getattr(config, 'PH_INTERCEPT', 15.75)
            
#             while True:
#                 v = chan.voltage
#                 ph = slope * v + intercept
#                 print(f"Raw: {v:.4f} V  =>  pH: {ph:.2f}   ", end='\r')
#                 time.sleep(0.5)
#         except KeyboardInterrupt:
#             print("\nStopped.")
#         except Exception as e:
#             print(f"\nError: {e}")
#     else:
#         print("[SIMULATION] Voltage: 2.500V | pH: 7.00")
#         input("Press Enter...")

# def read_ec():
#     print("\n--- EC Sensor Reading (Continuous) ---")
#     print("Press CTRL+C to stop reading.\n")
#     if i2c and ADS:
#         try:
#             ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
#             chan = AnalogIn(ads, config.CHAN_EC)
            
#             while True:
#                 v = chan.voltage
#                 ec = v * 1.0 # Basic estimation
#                 print(f"Raw: {v:.4f} V  =>  EC: {ec:.2f} mS/cm   ", end='\r')
#                 time.sleep(0.5)
#         except KeyboardInterrupt:
#             print("\nStopped.")
#         except Exception as e:
#             print(f"\nError: {e}")
#     else:
#         print("[SIMULATION] Voltage: 1.200V | EC: 1.20 mS/cm")
#         input("Press Enter...")

# # --- MAIN LOOP ---
# def main_menu():
#     while True:
#         print("\n==============================")
#         print("   VERTICAL FARM DIAGNOSTICS   ")
#         print("==============================")
#         print("1. Manual Relay Control (Toggle ON/OFF)")
#         print("2. Test All Relays (Sequence)")
#         print("3. Read Temperature/Humidity")
#         print("4. Read pH Sensor")
#         print("5. Read EC Sensor")
#         print("6. Exit")
        
#         choice = input("\nSelect Option: ")
        
#         if choice == '1': test_single_relay()
#         elif choice == '2': test_all_relays()
#         elif choice == '3': read_bme280()
#         elif choice == '4': read_ph()
#         elif choice == '5': read_ec()
#         elif choice == '6':
#             print("Turning off all relays before exit...")
#             for pin in config.RELAYS.values():
#                 GPIO.output(pin, GPIO.HIGH) # OFF
#             GPIO.cleanup()
#             print("Bye!")
#             break

# if __name__ == "__main__":
#     try: main_menu()
#     except KeyboardInterrupt:
#         GPIO.cleanup()
#         print("\nExited.")

import os
import sys
import time
import subprocess

# --- PI 5 HARDWARE RECOVERY ---
def reset_i2c_bus():
    """Forces the Pi 5 to release the I2C bus locks."""
    subprocess.run(["sudo", "modprobe", "-r", "i2c_bcm2835"], capture_output=True)
    subprocess.run(["sudo", "modprobe", "i2c_bcm2835"], capture_output=True)
    time.sleep(1)

# Global Hardware Imports
try:
    import RPi.GPIO as GPIO
    import board
    import busio
    from adafruit_bme280 import basic as adafruit_bme280
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except ImportError:
    print("!! Missing libraries. Run: ./venv/bin/pip install adafruit-circuitpython-bme280 adafruit-circuitpython-ads1x15 adafruit-blinka")
    sys.exit(1)

# --- PIN MAPPING (FROM YOUR CONFIG.PY) ---
RELAYS = {
    "1": {"name": "Water Pump",  "pin": 5,  "state": "OFF"},
    "2": {"name": "Light",       "pin": 6,  "state": "OFF"},
    "3": {"name": "Fan 1",       "pin": 13, "state": "OFF"},
    "4": {"name": "pH Down",     "pin": 19, "state": "OFF"},
    "5": {"name": "pH Up",       "pin": 26, "state": "OFF"},
    "6": {"name": "Nutrient A",  "pin": 16, "state": "OFF"},
    "7": {"name": "Nutrient B",  "pin": 20, "state": "OFF"},
    "8": {"name": "Fan 2",       "pin": 21, "state": "OFF"}
}

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for key in RELAYS:
        GPIO.setup(RELAYS[key]["pin"], GPIO.OUT, initial=GPIO.HIGH)

def get_sensor_data(i2c):
    results = {"temp": "N/A", "hum": "N/A", "voltages": ["N/A"]*3}
    
    # 1. BME280
    try:
        bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
        results["temp"] = f"{bme.temperature:.1f}C"
        results["hum"] = f"{bme.relative_humidity:.1f}%"
    except: pass

    # 2. ADS1115
    try:
        ads = ADS.ADS1115(i2c, address=0x48)
        # Using integers 0, 1, 2 to avoid AttributeError 'P0'
        for i in range(3):
            chan = AnalogIn(ads, i)
            results["voltages"][i] = f"{chan.voltage:.3f}V"
    except: pass
    
    return results

def draw_ui(sensors):
    os.system('clear')
    print("==================================================")
    print("      VERTICAL FARM - MASTER DIAGNOSTIC (PI 5)    ")
    print("==================================================")
    print(f" CLIMATE | Temp: {sensors['temp']} | Hum: {sensors['hum']}")
    print(f" ANALOG  | A0 (pH): {sensors['voltages'][0]} | A1 (EC): {sensors['voltages'][1]} | A2 (Lvl): {sensors['voltages'][2]}")
    print("--------------------------------------------------")
    print(" ID | Device       | GPIO | Status")
    print("----|--------------|------|-----------------------")
    for key in sorted(RELAYS.keys(), key=int):
        data = RELAYS[key]
        status = "[  ON  ]" if data["state"] == "ON" else "[  OFF ]"
        print(f" {key: <2} | {data['name']: <12} | {data['pin']: <4} | {status}")
    print("--------------------------------------------------")
    print(" [1-8] Toggle Device | [A] All ON | [O] All OFF")
    print(" [R] Refresh Sensors | [Q] Quit")
    print("==================================================")

def toggle(key, force_state=None):
    pin = RELAYS[key]["pin"]
    if force_state is not None:
        new_on = force_state
    else:
        new_on = RELAYS[key]["state"] == "OFF"
    
    GPIO.output(pin, GPIO.LOW if new_on else GPIO.HIGH)
    RELAYS[key]["state"] = "ON" if new_on else "OFF"

if __name__ == "__main__":
    if os.getuid() != 0:
        print("!! Run as: sudo ./venv/bin/python3 diagnostics.py")
        sys.exit(1)

    setup_gpio()
    i2c_bus = None
    try:
        i2c_bus = busio.I2C(board.SCL, board.SDA)
    except:
        reset_i2c_bus()
        i2c_bus = busio.I2C(board.SCL, board.SDA)

    try:
        while True:
            sensors = get_sensor_data(i2c_bus)
            draw_ui(sensors)
            cmd = input("Command: ").upper()
            
            if cmd in RELAYS:
                toggle(cmd)
            elif cmd == "A":
                for k in RELAYS: toggle(k, True)
            elif cmd == "O":
                for k in RELAYS: toggle(k, False)
            elif cmd == "R":
                continue
            elif cmd == "Q":
                break
    finally:
        for k in RELAYS: toggle(k, False)
        GPIO.cleanup()