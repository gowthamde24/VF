import os
import sys
import time
import subprocess

def reset_i2c_bus():
    """Forces Pi 5 to release I2C locks."""
    subprocess.run(["sudo", "modprobe", "-r", "i2c_bcm2835"], capture_output=True)
    subprocess.run(["sudo", "modprobe", "i2c_bcm2835"], capture_output=True)
    time.sleep(1)

try:
    import board
    import busio
    from adafruit_bme280 import basic as adafruit_bme280
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except ImportError:
    print("!! Libraries missing. Run the pip install commands.")
    sys.exit(1)

def run():
    print("\n" + "="*45)
    print("  VERTICAL FARM - ADS1115 FIX DIAGNOSTIC")
    print("="*45)

    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # 1. Test BME280
        try:
            bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
            print(f"[OK] BME280: {bme.temperature:.1f}C")
        except: print("[FAIL] BME280 not found.")

        # 2. Test ADS1115
        try:
            ads = ADS.ADS1115(i2c, address=0x48)
            print("[OK] ADS1115 Online. Reading Voltages:")
            # Using 0, 1, 2 instead of ADS.P0 to avoid the AttributeError
            for i in range(3):
                chan = AnalogIn(ads, i)
                print(f"     -> Channel A{i}: {chan.voltage:.3f}V")
        except Exception as e:
            print(f"[FAIL] ADS1115 Error: {e}")

    except OSError as e:
        if e.errno == 11 or e.errno == 121:
            reset_i2c_bus()
            print("!! Bus Reset. Run the script again.")
    
if __name__ == "__main__":
    run()