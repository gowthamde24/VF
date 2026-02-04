# import time
# import board
# import busio
# import adafruit_ads1x15.ads1115 as ADS
# from adafruit_ads1x15.analog_in import AnalogIn

# # --- CONFIGURATION ---
# I2C_ADDR_ADS1115 = 0x48
# PH_CHANNEL = 0  # A0 (Pin where pH probe is connected)

# # Known Buffer Values (Check your bottles!)
# BUFFER_1_PH = 6.86  # Neutral Buffer (sometimes 7.00)
# BUFFER_2_PH = 4.01  # Acidic Buffer

# # --- SETUP ---
# print("Initializing Hardware...")
# try:
#     i2c = busio.I2C(board.SCL, board.SDA)
#     ads = ADS.ADS1115(i2c, address=I2C_ADDR_ADS1115)
#     chan = AnalogIn(ads, PH_CHANNEL)
#     print("-> ADS1115 Connected Successfully.")
# except Exception as e:
#     print(f"! Error initializing hardware: {e}")
#     print("  (If on PC/Mac, this script will fail. Run on Pi only.)")
#     exit()

# def wait_for_stabilization(seconds=120):
#     """Countdown timer to let the probe stabilize."""
#     print(f"\n   Waiting {seconds} seconds for chemical stabilization...")
#     print("   Do not move the probe.")
#     try:
#         for i in range(seconds, 0, -1):
#             # Print countdown on the same line
#             print(f"   Time Remaining: {i} seconds   ", end='\r')
#             time.sleep(1)
#         print("\n   Stabilization Complete. Reading voltage...")
#     except KeyboardInterrupt:
#         print("\n   ! Wait skipped by user (Readings may be inaccurate).")

# def read_stable_voltage(samples=50):
#     """Reads voltage over 5 seconds and averages it to remove noise."""
#     total = 0
#     for _ in range(samples):
#         total += chan.voltage
#         time.sleep(0.1)
#     avg_voltage = total / samples
#     return avg_voltage

# # --- WIZARD ---
# print("\n=========================================")
# print("   pH PROBE CALIBRATION WIZARD (2-Point)  ")
# print("=========================================")
# print("You need: Buffer 6.86 (Neutral) & Buffer 4.01 (Acid)")
# print("Note: Rinse probe with distilled water between steps.\n")

# # --- STEP 1: NEUTRAL BUFFER ---
# print(f"STEP 1: Calibrate to pH {BUFFER_1_PH}")
# input(f"-> Dip probe into BUFFER 1 ({BUFFER_1_PH} pH). Press ENTER to start timer...")

# # Wait 2 Minutes
# wait_for_stabilization(120) 

# # Take Reading
# volt_1 = read_stable_voltage()
# print(f"   -> Recorded Voltage 1: {volt_1:.4f} V")
# print("   -> Step 1 Complete.\n")

# # --- STEP 2: ACID BUFFER ---
# print(f"STEP 2: Calibrate to pH {BUFFER_2_PH}")
# print("-> Remove probe, RINSE with distilled water, and WIPE gently.")
# input(f"-> Dip probe into BUFFER 2 ({BUFFER_2_PH} pH). Press ENTER to start timer...")

# # Wait 2 Minutes
# wait_for_stabilization(120)

# # Take Reading
# volt_2 = read_stable_voltage()
# print(f"   -> Recorded Voltage 2: {volt_2:.4f} V")
# print("   -> Step 2 Complete.\n")

# # --- CALCULATION & RESULT ---
# # Formula: y = mx + c  (pH = slope * voltage + intercept)
# # slope (m) = (pH2 - pH1) / (V2 - V1)
# # intercept (c) = pH1 - (m * V1)

# if abs(volt_1 - volt_2) < 0.05:
#     print("\n!!! ERROR: Voltages are too similar. !!!")
#     print("1. Did you switch buffers?")
#     print("2. Is the probe connected to A0?")
#     print("3. Is the protective cap removed?")
# else:
#     slope = (BUFFER_2_PH - BUFFER_1_PH) / (volt_2 - volt_1)
#     intercept = BUFFER_1_PH - (slope * volt_1)

#     print("=" * 40)
#     print("       CALIBRATION SUCCESSFUL       ")
#     print("=" * 40)
#     print(f"Slope (m):     {slope:.4f}")
#     print(f"Intercept (c): {intercept:.4f}")
#     print("-" * 40)
#     print("ACTION: Open 'config.py' and update these lines:")
#     print(f"PH_SLOPE = {slope:.4f}")
#     print(f"PH_INTERCEPT = {intercept:.4f}")
#     print("=" * 40)
    
#     # Live Test
#     print("\nStarting Live Verification Mode (Press Ctrl+C to exit)...")
#     try:
#         while True:
#             v = chan.voltage
#             ph = slope * v + intercept
#             print(f"Live Reading: {v:.4f} V  =>  pH: {ph:.2f}   ", end="\r")
#             time.sleep(0.5)
#     except KeyboardInterrupt:
#         print("\nCalibration finished.")


import time
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# --- CONFIGURATION ---
I2C_ADDR_ADS1115 = 0x48
PH_CHANNEL = 0  # A0 (Pin where pH probe is connected)

# Known Buffer Values (Check your bottles!)
BUFFER_1_PH = 6.86  # Neutral Buffer (sometimes 7.00)
BUFFER_2_PH = 4.01  # Acidic Buffer

# --- SETUP ---
print("Initializing Hardware...")

# Mocking logic for PC/Mac compatibility
try:
    import board
    import busio
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c, address=I2C_ADDR_ADS1115)
    chan = AnalogIn(ads, PH_CHANNEL)
    print("-> ADS1115 Connected Successfully.")
except (NotImplementedError, ImportError, ValueError):
    print("! Hardware not found (Running on PC/Mac). Entering SIMULATION MODE.")
    print("! You cannot calibrate a real probe here. This is just a test.")
    
    # Create a fake channel class for simulation
    class MockChannel:
        def __init__(self):
            self.voltage = 2.500 # Default voltage
    chan = MockChannel()

def wait_for_stabilization(seconds=120):
    """Countdown timer to let the probe stabilize."""
    print(f"\n   Waiting {seconds} seconds for chemical stabilization...")
    print("   Do not move the probe.")
    try:
        for i in range(seconds, 0, -1):
            # Print countdown on the same line
            print(f"   Time Remaining: {i} seconds   ", end='\r')
            time.sleep(1)
        print("\n   Stabilization Complete. Reading voltage...")
    except KeyboardInterrupt:
        print("\n   ! Wait skipped by user (Readings may be inaccurate).")

def read_stable_voltage(samples=50):
    """Reads voltage over 5 seconds and averages it to remove noise."""
    total = 0
    for _ in range(samples):
        # Simulate voltage change if in Mock mode
        if isinstance(chan, MockChannel):
            import random
            chan.voltage += random.uniform(-0.01, 0.01) 
            
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

# Wait 2 Minutes
wait_for_stabilization(120) 

# Take Reading
volt_1 = read_stable_voltage()
print(f"   -> Recorded Voltage 1: {volt_1:.4f} V")
print("   -> Step 1 Complete.\n")

# --- STEP 2: ACID BUFFER ---
print(f"STEP 2: Calibrate to pH {BUFFER_2_PH}")
print("-> Remove probe, RINSE with distilled water, and WIPE gently.")
input(f"-> Dip probe into BUFFER 2 ({BUFFER_2_PH} pH). Press ENTER to start timer...")

# In simulation mode, artificially change the voltage for step 2 so calibration doesn't fail
if isinstance(chan, MockChannel):
    chan.voltage = 3.000 # Simulate a different reading for acid

# Wait 2 Minutes
wait_for_stabilization(120)

# Take Reading
volt_2 = read_stable_voltage()
print(f"   -> Recorded Voltage 2: {volt_2:.4f} V")
print("   -> Step 2 Complete.\n")

# --- CALCULATION & RESULT ---
# Formula: y = mx + c  (pH = slope * voltage + intercept)
# slope (m) = (pH2 - pH1) / (V2 - V1)
# intercept (c) = pH1 - (m * V1)

if abs(volt_1 - volt_2) < 0.05:
    print("\n!!! ERROR: Voltages are too similar. !!!")
    print("1. Did you switch buffers?")
    print("2. Is the probe connected to A0?")
    print("3. Is the protective cap removed?")
else:
    slope = (BUFFER_2_PH - BUFFER_1_PH) / (volt_2 - volt_1)
    intercept = BUFFER_1_PH - (slope * volt_1)

    print("=" * 40)
    print("       CALIBRATION SUCCESSFUL       ")
    print("=" * 40)
    print(f"Slope (m):     {slope:.4f}")
    print(f"Intercept (c): {intercept:.4f}")
    print("-" * 40)
    print("ACTION: Open 'config.py' and update these lines:")
    print(f"PH_SLOPE = {slope:.4f}")
    print(f"PH_INTERCEPT = {intercept:.4f}")
    print("=" * 40)
    
    # Live Test
    print("\nStarting Live Verification Mode (Press Ctrl+C to exit)...")
    try:
        while True:
            v = chan.voltage
            ph = slope * v + intercept
            print(f"Live Reading: {v:.4f} V  =>  pH: {ph:.2f}   ", end="\r")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nCalibration finished.")