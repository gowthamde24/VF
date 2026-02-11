import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_bme280.advanced as adafruit_bme280

i2c = busio.I2C(board.SCL, board.SDA)

try:

# BME280 init (Address 0x76)
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
    print(f"BME280 found! Temp: {bme280.temperature:.2f} °C")
except Exception as e:
    print(f"BME280 ERROR: {e}")

# ADS1115 init (Address 0x48)
try:
    ads = ADS.ADS1115(i2c, address=0x48)
    chan = AnalogIn(ads, ADS.P0) # Liest Pin A0 gegen GND
    print(f"ADS1115 Found! Voltage A0: {chan.voltage:.3f} V")
except Exception as e:
    print(f"ADS1115 ERROR: {e}") 