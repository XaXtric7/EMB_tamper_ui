import socket
import time
import random
import argparse
import os

STATE_FILE = "power_state.txt"

def get_power_status():
    if not os.path.exists(STATE_FILE):
        return "ON"
    try:
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    except:
        return "ON"

def generate_reading(tamper_probability: float) -> tuple[float, float, float, str]:
    """
    Generate one reading (voltage, current, magnetic_field, tamper_status).
    """
    power_status = get_power_status()

    # Check remote power status
    if power_status == "OFF":
        return 0.0, 0.0, 0.0, "Power Cut"

    # Check if STABLE mode is enabled
    if power_status == "STABLE":
        voltage = 2.7 + random.uniform(0.0, 0.1)  # 2.7 - 2.8V
        current = 0.9 + random.uniform(0.0, 0.1)  # 0.9 - 1.0A
        mag = 15.0 + random.uniform(-1.0, 1.0)
        return round(voltage, 2), round(current, 2), round(mag, 2), "Normal (Stable)"

    voltage = 2.8 + random.uniform(-0.05, 0.05)  # stable 2.8V system
    current = 0.9 + random.uniform(0.0, 0.1)    # normal 0.9-1.0A current
    mag = 15.0 + random.uniform(-2.0, 2.0)      # background magnetic field
    tamper_type = "Normal"

    if random.random() < tamper_probability:
        case = random.choice(
            ["bypass", "voltage", "magnetic"])
        if case == "bypass":
            current = 0.0
            tamper_type = "Bypass Tamper"
        elif case == "voltage":
            voltage = random.uniform(1.8, 2.4)
            tamper_type = "Voltage Tamper"
        elif case == "magnetic":
            mag = random.uniform(60.0, 100.0)
            tamper_type = "Magnetic Tamper"

    # Also check live if voltage drops below 2.5V
    if voltage < 2.5:
        tamper_type = "Voltage Tamper"

    # Check if current is zero
    if current == 0.0:
        tamper_type = "Bypass Tamper"

    # Check if magnetic field is high
    if mag >= 50.0:
        tamper_type = "Magnetic Tamper"

    return round(voltage, 2), round(current, 2), round(mag, 2), tamper_type


def run_server(host: str, port: int, interval_s: float, tamper_probability: float):
    """Simple TCP server that streams CSV readings to one client."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)
        print(f"Simulator listening on {host}:{port}")
        while True:
            conn, addr = s.accept()
            print(f"Client connected from {addr}")
            try:
                with conn:
                    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    while True:
                        v, c, m, t = generate_reading(tamper_probability)
                        line = f"{v},{c},{m},{t}\n".encode()
                        conn.sendall(line)
                        time.sleep(interval_s)
            except Exception as e:
                print(f"Client disconnected: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Low-voltage Tamper Data Simulator (TCP)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Host to bind the simulator on")
    parser.add_argument("--port", type=int, default=7000,
                        help="Port to bind the simulator on")
    parser.add_argument("--interval", type=float,
                        default=0.5, help="Seconds between samples")
    parser.add_argument("--tamper", type=float, default=0.25,
                        help="Tamper event probability (0–1)")
    args = parser.parse_args()

    run_server(args.host, args.port, args.interval,
               max(0.0, min(1.0, args.tamper)))


if __name__ == "__main__":
    main()
