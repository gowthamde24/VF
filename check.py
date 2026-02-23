import RPi.GPIO as GPIO
import time
import sys

# Mapping of BCM Pin to Physical Pin Number for easy identification
GPIO_MAP = {
    2: 3, 3: 5, 4: 7, 17: 11, 27: 13, 22: 15, 10: 19, 9: 21, 11: 23, 
    0: 27, 5: 29, 6: 31, 13: 33, 19: 35, 26: 37, 14: 8, 15: 10, 18: 12, 
    23: 16, 24: 18, 25: 22, 8: 24, 7: 26, 1: 28, 12: 32, 16: 36, 20: 38, 21: 40
}

def scan_hardware():
    print("==================================================")
    print("      RASPBERRY PI 5 - FULL GPIO SCANNER          ")
    print("==================================================")
    print("Testing each pin. Watch for a BRIGHT RED LED and CLICK.")
    print("Press Ctrl+C to stop the scan at any time.\n")

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    results = {"WORKING": [], "FAILED": []}

    # Sort by physical pin number for easier tracking
    sorted_pins = sorted(GPIO_MAP.keys(), key=lambda x: GPIO_MAP[x])

    for bcm in sorted_pins:
        phys = GPIO_MAP[bcm]
        print(f"Testing Physical Pin {phys: >2} (BCM {bcm: <2})... ", end="", flush=True)
        
        try:
            # Step 1: Initialize
            GPIO.setup(bcm, GPIO.OUT, initial=GPIO.HIGH)
            
            # Step 2: Pulse LOW (Turns Relay ON)
            GPIO.output(bcm, GPIO.LOW)
            time.sleep(0.8)
            
            # Step 3: Pulse HIGH (Turns Relay OFF)
            GPIO.output(bcm, GPIO.HIGH)
            
            confirm = input("[Did it click/light up? y/n]: ").lower()
            if confirm == 'y':
                results["WORKING"].append(bcm)
            else:
                results["FAILED"].append(bcm)
                
        except Exception as e:
            print(f"\n[CRITICAL ERROR] Pin {bcm} is electrically dead or locked: {e}")
            results["FAILED"].append(bcm)

    # Final Report
    print("\n" + "="*50)
    print("                SCAN COMPLETE REPORT               ")
    print("="*50)
    print(f"✅ WORKING PINS: {results['WORKING']}")
    print(f"❌ FAILED PINS:  {results['FAILED']}")
    print("="*50)
    print("Tip: Avoid using FAILED pins in your config.py.")

if __name__ == "__main__":
    try:
        scan_hardware()
    finally:
        GPIO.cleanup()