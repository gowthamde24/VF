# import time
# import board
# import busio
# import smbus2
# import RPi.GPIO as GPIO

# # Sensor Libraries
# import adafruit_ads1x15.ads1115 as ADS
# from adafruit_ads1x15.analog_in import AnalogIn
# from adafruit_bme280 import basic as adafruit_bme280

# # --- CONFIGURATION ---
# RELAYS = {
#     1: {'name': 'Nutrient Pump', 'pin': 5},
#     2: {'name': 'pH Up Pump',    'pin': 6},
#     3: {'name': 'pH Down Pump',  'pin': 13},
#     4: {'name': 'Air Fan',       'pin': 19}
# }

# # --- HARDWARE SETUP ---
# GPIO.setmode(GPIO.BCM)
# for r in RELAYS.values():
#     GPIO.setup(r['pin'], GPIO.OUT)
#     GPIO.output(r['pin'], GPIO.HIGH) # Start OFF

# # I2C Setup
# i2c = busio.I2C(board.SCL, board.SDA)

# # --- TEST FUNCTIONS ---

# def test_single_relay():
#     while True:
#         print("\n--- Select Relay to Control ---")
#         for key, val in RELAYS.items():
#             state = "ON" if GPIO.input(val['pin']) == GPIO.LOW else "OFF"
#             print(f" {key}: {val['name']} (GPIO {val['pin']}) - Currently: {state}")
#         print(" 5: Back to Main Menu")
        
#         try:
#             selection = int(input("Enter Relay Number (1-4) or 5 to back: "))
#             if selection == 5: break
#             if selection in RELAYS:
#                 target = RELAYS[selection]
#                 action = input(f"Turn {target['name']} (1) ON or (0) OFF? ")
#                 if action == '1':
#                     GPIO.output(target['pin'], GPIO.LOW) # ON
#                     print(f"--> {target['name']} is now ON.")
#                 elif action == '0':
#                     GPIO.output(target['pin'], GPIO.HIGH) # OFF
#                     print(f"--> {target['name']} is now OFF.")
#                 else: print("Invalid action.")
#             else: print("Invalid selection.")
#         except ValueError: print("Please enter a number.")

# def test_all_relays():
#     print("\n--- Cycling ALL Relays ---")
#     for key, val in RELAYS.items():
#         print(f"--> Testing {val['name']}...")
#         GPIO.output(val['pin'], GPIO.LOW) # ON
#         time.sleep(1)
#         GPIO.output(val['pin'], GPIO.HIGH) # OFF
#         time.sleep(0.5)
#     print("Cycle Complete.")

# def read_bme280():
#     print("\n--- Reading Environment (BME280) ---")
#     try:
#         bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
#         print(f"Temperature: {bme.temperature:.1f} °C")
#         print(f"Humidity:    {bme.relative_humidity:.1f} %")
#     except Exception as e:
#         print(f"Error reading BME280: {e}")

# def read_ph():
#     print("\n--- Reading pH (ADS1115 A0) ---")
#     try:
#         ads = ADS.ADS1115(i2c)
#         chan = AnalogIn(ads, ADS.P0)
#         print(f"Raw Voltage: {chan.voltage:.4f} V")
#         print(f"Est. pH:     {7.0 + ((2.5 - chan.voltage) / 0.18):.2f}")
#     except Exception as e:
#         print(f"Error reading ADS1115: {e}")

# # --- MAIN MENU LOOP ---
# def main_menu():
#     while True:
#         print("\n==============================")
#         print("   VERTICAL FARM DIAGNOSTICS   ")
#         print("==============================")
#         print("1. Control Specific Relay (Pump/Fan)")
#         print("2. Cycle ALL Relays")
#         print("3. Read Temperature/Humidity")
#         print("4. Read pH Sensor")
#         print("5. Exit")
        
#         choice = input("\nSelect an option (1-5): ")
        
#         if choice == '1': test_single_relay()
#         elif choice == '2': test_all_relays()
#         elif choice == '3': read_bme280()
#         elif choice == '4': read_ph()
#         elif choice == '5':
#             GPIO.cleanup()
#             print("Exiting...")
#             break
#         else: print("Invalid option, try again.")
#         time.sleep(1)

# if __name__ == "__main__":
#     try: main_menu()
#     except KeyboardInterrupt:
#         GPIO.cleanup()
#         print("\nForced Exit.")


import time
import sys
import config  # Import your actual settings

# --- HARDWARE ABSTRACTION (Mac/PC Compatibility) ---
try:
    import RPi.GPIO as GPIO
    import board
    import busio
    import smbus2
except (ImportError, RuntimeError, NotImplementedError):
    print("! Hardware libraries not found. Running in SIMULATION MODE.")
    
    # Mock GPIO Class
    class GPIO:
        BCM = "BCM"; OUT = "OUT"; HIGH = 1; LOW = 0
        def setmode(mode): pass
        def setup(pin, mode): pass
        def output(pin, state): print(f"  [MOCK] GPIO {pin} -> {'HIGH' if state else 'LOW'}")
        def input(pin): return 0
        def cleanup(): pass
    
    # Mock Board/Busio
    class board: SCL = 1; SDA = 2
    class busio:
        class I2C:
            def __init__(self, scl, sda): pass

# Sensor Libraries (Try/Except)
try:
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    from adafruit_bme280 import basic as adafruit_bme280
except ImportError:
    ADS = None
    adafruit_bme280 = None

# --- HARDWARE SETUP ---
GPIO.setmode(GPIO.BCM)

# Initialize I2C
i2c = None
try:
    i2c = busio.I2C(board.SCL, board.SDA)
except:
    pass

# Setup Relays from Config
for name, pin in config.RELAYS.items():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH) # Start OFF

# --- TEST FUNCTIONS ---

def test_single_relay():
    while True:
        print("\n--- Relay Control Menu ---")
        # Create a numbered list from config
        relay_list = list(config.RELAYS.items()) # [('water_pump', 5), ('light', 6)...]
        
        for i, (name, pin) in enumerate(relay_list):
            state = "ON" if GPIO.input(pin) == GPIO.LOW else "OFF"
            print(f" {i+1}. {name.upper()} (GPIO {pin}) - [{state}]")
        print(" 9. Back")
        
        choice = input("Select Relay # to toggle: ")
        if choice == '9': break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(relay_list):
                name, pin = relay_list[idx]
                print(f"\n--> Toggling {name}...")
                GPIO.output(pin, GPIO.LOW)  # ON
                time.sleep(1)
                GPIO.output(pin, GPIO.HIGH) # OFF
                print("--> Done.")
            else:
                print("Invalid number.")
        except ValueError:
            pass

def test_all_relays():
    print("\n--- Cycling ALL Relays (Sequence) ---")
    for name, pin in config.RELAYS.items():
        print(f"Testing {name} (GPIO {pin})...")
        GPIO.output(pin, GPIO.LOW)  # ON
        time.sleep(0.5)
        GPIO.output(pin, GPIO.HIGH) # OFF
        time.sleep(0.2)
    print("Cycle Complete.")

def read_bme280():
    print("\n--- BME280 Environment ---")
    if i2c and adafruit_bme280:
        try:
            bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=config.I2C_ADDR_BME280)
            print(f"Temperature: {bme.temperature:.1f} °C")
            print(f"Humidity:    {bme.relative_humidity:.1f} %")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("[SIMULATION] Temp: 25.5°C | Hum: 60%")

def read_ph():
    print("\n--- pH Sensor (ADS1115) ---")
    if i2c and ADS:
        try:
            ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
            chan = AnalogIn(ads, config.CHAN_PH)
            v = chan.voltage
            
            # Use cal values if available
            slope = getattr(config, 'PH_SLOPE', -3.5)
            intercept = getattr(config, 'PH_INTERCEPT', 15.75)
            ph = slope * v + intercept
            
            print(f"Raw Voltage: {v:.4f} V")
            print(f"Calculated:  {ph:.2f} pH")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("[SIMULATION] Voltage: 2.500V | pH: 7.00")

# --- MAIN LOOP ---
def main_menu():
    while True:
        print("\n==============================")
        print("   VERTICAL FARM DIAGNOSTICS   ")
        print("==============================")
        print("1. Manual Relay Control")
        print("2. Test All Relays (Auto)")
        print("3. Read Temperature/Humidity")
        print("4. Read pH Sensor")
        print("5. Exit")
        
        choice = input("\nSelect Option: ")
        
        if choice == '1': test_single_relay()
        elif choice == '2': test_all_relays()
        elif choice == '3': read_bme280()
        elif choice == '4': read_ph()
        elif choice == '5':
            GPIO.cleanup()
            print("Bye!")
            break

if __name__ == "__main__":
    try: main_menu()
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nExited.")