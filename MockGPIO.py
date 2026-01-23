

BCM = "BCM"
OUT = "OUT"
IN = "IN"
HIGH = 1
LOW = 0

def setmode(mode):
    print(f"[MOCK] GPIO Mode set to {mode}")

def setup(pin, mode):
    print(f"[MOCK] Setting up Pin {pin} as {mode}")

def output(pin, state):
    state_str = "HIGH" if state == 1 else "LOW"
    print(f"[MOCK] Writing {state_str} to Pin {pin}")

def input(pin):
    return 0

def cleanup():
    print("[MOCK] Cleaning up GPIO")