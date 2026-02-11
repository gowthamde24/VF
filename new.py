import time
import board
import busio
import sys

# 1. Attempt to open I2C Bus
print("--- I2C BUS CHECK ---")
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    print("[OK] I2C Bus opened successfully.")
except Exception as e:
    print(f"[FAIL] Could not open I2C bus: {e}")
    sys.exit(1)

# 2. Test BME280 (Climate)
print("\n--- BME280 TEST (0x76) ---")
try:
    from adafruit_bme280 import basic as adafruit_bme280
    bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
    print(f"[OK] BME280 Detected!")
    print(f"     Temp: {bme.temperature:.2f} C")
    print(f"     Hum:  {bme.relative_humidity:.2f} %")
except Exception as e:
    print(f"[FAIL] BME280 Error: {e}")

# 3. Test ADS1115 (Analog/pH)
print("\n--- ADS1115 TEST (0x48) ---")
try:
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    ads = ADS.ADS1115(i2c, address=0x48)
    chan = AnalogIn(ads, ADS.P0)
    print(f"[OK] ADS1115 Detected!")
    print(f"     A0 Voltage: {chan.voltage:.4f} V")
except Exception as e:
    print(f"[FAIL] ADS1115 Error: {e}")

print("\n--- Test Complete ---")