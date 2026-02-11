import smbus2

def get_full_i2c_report(bus_number=1):
    bus = smbus2.SMBus(bus_number)
    report = {}

    for address in range(128):
        # Formatting key as '0xNN'
        key = f"0x{address:02x}"
        
        try:
            # Quick write/read to check for existence
            data = bus.read_byte(address)
            report[key] = f"{data} (0x{data:02x})"
        except OSError:
            report[key] = "No connection"
            
    bus.close()
    return report

# Generate the data
i2c_data = get_full_i2c_report()

# Print every single address in key : value format
for addr, status in i2c_data.items():
    print(f"{addr} : {status}") 