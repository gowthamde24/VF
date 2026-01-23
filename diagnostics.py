import time
import board
import busio
import smbus2
import RPi.GPIO as GPIO

# Sensor Libraries
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_bme280 import basic as adafruit_bme280

# --- CONFIGURATION ---
RELAYS = {
    1: {'name': 'Nutrient Pump', 'pin': 5},
    2: {'name': 'pH Up Pump',    'pin': 6},
    3: {'name': 'pH Down Pump',  'pin': 13},
    4: {'name': 'Air Fan',       'pin': 19}
}

# --- HARDWARE SETUP ---
GPIO.setmode(GPIO.BCM)
for r in RELAYS.values():
    GPIO.setup(r['pin'], GPIO.OUT)
    GPIO.output(r['pin'], GPIO.HIGH) # Start OFF

# I2C Setup
i2c = busio.I2C(board.SCL, board.SDA)

# --- TEST FUNCTIONS ---

def test_single_relay():
    while True:
        print("\n--- Select Relay to Control ---")
        for key, val in RELAYS.items():
            state = "ON" if GPIO.input(val['pin']) == GPIO.LOW else "OFF"
            print(f" {key}: {val['name']} (GPIO {val['pin']}) - Currently: {state}")
        print(" 5: Back to Main Menu")
        
        try:
            selection = int(input("Enter Relay Number (1-4) or 5 to back: "))
            if selection == 5: break
            if selection in RELAYS:
                target = RELAYS[selection]
                action = input(f"Turn {target['name']} (1) ON or (0) OFF? ")
                if action == '1':
                    GPIO.output(target['pin'], GPIO.LOW) # ON
                    print(f"--> {target['name']} is now ON.")
                elif action == '0':
                    GPIO.output(target['pin'], GPIO.HIGH) # OFF
                    print(f"--> {target['name']} is now OFF.")
                else: print("Invalid action.")
            else: print("Invalid selection.")
        except ValueError: print("Please enter a number.")

def test_all_relays():
    print("\n--- Cycling ALL Relays ---")
    for key, val in RELAYS.items():
        print(f"--> Testing {val['name']}...")
        GPIO.output(val['pin'], GPIO.LOW) # ON
        time.sleep(1)
        GPIO.output(val['pin'], GPIO.HIGH) # OFF
        time.sleep(0.5)
    print("Cycle Complete.")

def read_bme280():
    print("\n--- Reading Environment (BME280) ---")
    try:
        bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
        print(f"Temperature: {bme.temperature:.1f} °C")
        print(f"Humidity:    {bme.relative_humidity:.1f} %")
    except Exception as e:
        print(f"Error reading BME280: {e}")

def read_ph():
    print("\n--- Reading pH (ADS1115 A0) ---")
    try:
        ads = ADS.ADS1115(i2c)
        chan = AnalogIn(ads, ADS.P0)
        print(f"Raw Voltage: {chan.voltage:.4f} V")
        print(f"Est. pH:     {7.0 + ((2.5 - chan.voltage) / 0.18):.2f}")
    except Exception as e:
        print(f"Error reading ADS1115: {e}")

# --- MAIN MENU LOOP ---
def main_menu():
    while True:
        print("\n==============================")
        print("   VERTICAL FARM DIAGNOSTICS   ")
        print("==============================")
        print("1. Control Specific Relay (Pump/Fan)")
        print("2. Cycle ALL Relays")
        print("3. Read Temperature/Humidity")
        print("4. Read pH Sensor")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ")
        
        if choice == '1': test_single_relay()
        elif choice == '2': test_all_relays()
        elif choice == '3': read_bme280()
        elif choice == '4': read_ph()
        elif choice == '5':
            GPIO.cleanup()
            print("Exiting...")
            break
        else: print("Invalid option, try again.")
        time.sleep(1)

if __name__ == "__main__":
    try: main_menu()
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nForced Exit.")