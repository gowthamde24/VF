import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# --- CONFIGURATION ---
I2C_ADDR_ADS1115 = 0x48
PH_CHANNEL = 0  # A0 (Pin where pH probe is connected)

# Known Buffer Values (Check your bottles!)
BUFFER_1_PH = 7.00  # Neutral Buffer (sometimes 7.00)
BUFFER_2_PH = 4.00  # Acidic Buffer

# Temperature Compensation Configuration
USE_STATIC_TEMP = True
STATIC_TEMP_C = 25.0

# --- SETUP ---
print("Initializing Hardware...")
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c, address=I2C_ADDR_ADS1115)
    
    # Set gain to 1 for 3.3V sensors. 
    # This reads up to +/- 4.096V, giving you the highest possible resolution.
    ads.gain = 1 
    
    chan = AnalogIn(ads, PH_CHANNEL)
    print("-> ADS1115 Connected Successfully (Set for 3.3V Logic).")
except Exception as e:
    print(f"! Error initializing hardware: {e}")
    print("  (If on PC/Mac, this script will fail. Run on Pi only.)")
    exit()

def get_current_temperature():
    """Replace with actual sensor read if USE_STATIC_TEMP is False"""
    return STATIC_TEMP_C if USE_STATIC_TEMP else 25.0

def wait_for_stabilization(seconds=120):
    """Countdown timer to let the probe stabilize."""
    print(f"\n   Waiting {seconds} seconds for chemical stabilization...")
    print("   Do not move the probe.")
    try:
        for i in range(seconds, 0, -1):
            print(f"   Time Remaining: {i} seconds   ", end='\r')
            time.sleep(1)
        print("\n   Stabilization Complete. Reading voltage...")
    except KeyboardInterrupt:
        print("\n   ! Wait skipped by user (Readings may be inaccurate).")

def read_stable_voltage(samples=50):
    """Reads voltage over 5 seconds and averages it to remove noise."""
    total = 0
    for _ in range(samples):
        total += chan.voltage
        time.sleep(0.1)
    avg_voltage = total / samples
    return avg_voltage

# --- WIZARD ---
print("\n=========================================")
print("   pH PROBE CALIBRATION WIZARD (2-Point)  ")
print("=========================================")
print("You need: Buffer 6.86 (Neutral) & Buffer 4.01 (Acid)")
print("Note: Rinse probe with distilled water between steps.\n")

# --- STEP 1: NEUTRAL BUFFER ---
print(f"STEP 1: Calibrate to pH {BUFFER_1_PH}")
input(f"-> Dip probe into BUFFER 1 ({BUFFER_1_PH} pH). Press ENTER to start timer...")

wait_for_stabilization(120) 
volt_1 = read_stable_voltage()
print(f"   -> Recorded Voltage 1: {volt_1:.4f} V")
print("   -> Step 1 Complete.\n")

# --- STEP 2: ACID BUFFER ---
print(f"STEP 2: Calibrate to pH {BUFFER_2_PH}")
print("-> Remove probe, RINSE with distilled water, and WIPE gently.")
input(f"-> Dip probe into BUFFER 2 ({BUFFER_2_PH} pH). Press ENTER to start timer...")

wait_for_stabilization(120)
volt_2 = read_stable_voltage()
print(f"   -> Recorded Voltage 2: {volt_2:.4f} V")
print("   -> Step 2 Complete.\n")

# --- CALCULATION & RESULT ---
if abs(volt_1 - volt_2) < 0.05:
    print("\n!!! ERROR: Voltages are too similar. !!!")
    print("1. Did you switch buffers?")
    print("2. Is the probe connected to A0?")
    print("3. Is the protective cap removed?")
else:
    temp_c = get_current_temperature()
    
    # Empirical Calculation
    empirical_slope = (BUFFER_2_PH - BUFFER_1_PH) / (volt_2 - volt_1)
    intercept = BUFFER_1_PH - (empirical_slope * volt_1)
    
    # Theoretical Nernst Calculation for Reference
    nernst_slope_v_ph = (-0.1984 * (temp_c + 273.15)) / 1000.0
    theoretical_slope_ph_v = 1 / nernst_slope_v_ph

    print("=" * 40)
    print("       CALIBRATION SUCCESSFUL       ")
    print("=" * 40)
    print(f"Calibration Temp:        {temp_c:.1f} °C")
    print(f"Empirical Slope (m):     {empirical_slope:.4f}")
    print(f"Theoretical Nernst (m):  {theoretical_slope_ph_v:.4f}")
    print(f"Intercept (c):           {intercept:.4f}")
    print("-" * 40)
    print("ACTION: Open 'config.py' and update these lines:")
    print(f"PH_SLOPE = {empirical_slope:.4f}")
    print(f"PH_INTERCEPT = {intercept:.4f}")
    print("=" * 40)
    
    # Live Test
    print("\nStarting Live Verification Mode (Press Ctrl+C to exit)...")
    try:
        while True:
            v = chan.voltage
            ph = empirical_slope * v + intercept
            print(f"Live Reading: {v:.4f} V  =>  pH: {ph:.2f}   ", end="\r")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nCalibration finished.")