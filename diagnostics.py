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

def read_ec():
    print("\n--- EC Sensor (ADS1115) ---")
    if i2c and ADS:
        try:
            ads = ADS.ADS1115(i2c, address=config.I2C_ADDR_ADS1115)
            chan = AnalogIn(ads, config.CHAN_EC)
            v = chan.voltage
            
            # Simple conversion for testing (Calibration needed for precision)
            # Assuming 1V ~ 1.0 mS/cm as a rough baseline
            ec = v * 1.0 
            
            print(f"Raw Voltage: {v:.4f} V")
            print(f"Estimated:   {ec:.2f} mS/cm")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("[SIMULATION] Voltage: 1.200V | EC: 1.20 mS/cm")

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
        print("5. Read EC Sensor")
        print("6. Exit")
        
        choice = input("\nSelect Option: ")
        
        if choice == '1': test_single_relay()
        elif choice == '2': test_all_relays()
        elif choice == '3': read_bme280()
        elif choice == '4': read_ph()
        elif choice == '5': read_ec()
        elif choice == '6':
            GPIO.cleanup()
            print("Bye!")
            break

if __name__ == "__main__":
    try: main_menu()
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nExited.")