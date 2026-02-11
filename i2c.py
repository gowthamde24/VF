import smbus2
import sys

def inspect_i2c_bus(bus_number=1):
    """
    Scans the I2C bus and prints a register matrix for every detected device.
    Uses 0-based indexing to show exact memory offsets.
    """
    bus = smbus2.SMBus(bus_number)
    print(f"\n=== I2C BUS {bus_number} INSPECTOR (Pi 5) ===")
    print("Scanning addresses 0x03 to 0x77...\n")

    found_devices = 0

    for address in range(0x03, 0x78):
        try:
            # Quick write_quick to see if device exists
            bus.write_quick(address)
        except OSError:
            continue
        
        found_devices += 1
        print(f"Device Found at Address: {hex(address)}")
        print("Register Matrix (0-indexed):")
        print("      ", end="")
        for i in range(8): print(f"  +{i:01x} ", end="")
        print("\n" + "---" * 12)

        # We read the first 16 registers (0x00 to 0x0F)
        # This covers the most important parameters for BME280 and ADS1115
        for row in range(0, 16, 8):
            print(f"0x{row:01x}0 | ", end="")
            for col in range(8):
                reg = row + col
                try:
                    # Read single byte from register
                    val = bus.read_byte_data(address, reg)
                    print(f" 0x{val:02x}", end="")
                except OSError:
                    print("  ?? ", end="")
            print()
        print("-" * 36 + "\n")

    if found_devices == 0:
        print("No I2C devices detected. Check your wiring and GND.")
    else:
        print(f"Scan complete. {found_devices} device(s) found.")
    
    bus.close()

if __name__ == "__main__":
    try:
        inspect_i2c_bus()
    except PermissionError:
        print("Error: Permission denied. Please run with 'sudo'.")
    except KeyboardInterrupt:
        print("\nScan aborted by user.")