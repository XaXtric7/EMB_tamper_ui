import socket
import time
import random
import argparse


def generate_reading(tamper_probability: float) -> tuple[float, float, float, str]:
    """
    Generate one reading (voltage, current, magnetic_field, tamper_status).

    Tamper scenarios:
    - Magnetic tamper: magnetic_field spike ~ 60–100 G
    - Bypass: current near 0 A
    - Overload: current high 2–5 A
    - Voltage tamper: voltage < 2.7 V
    - Reverse flow: negative current (-0.2 to -1.0 A)
    """
    voltage = 5.0 + random.uniform(-0.2, 0.2)  # stable 5V system
    current = 0.4 + random.uniform(-0.3, 0.3)  # normal load current (ACS712)
    mag = 15.0 + random.uniform(-5.0, 5.0)     # background magnetic field
    tamper_type = "Normal"

    if random.random() < tamper_probability:
        case = random.choice(
            ["magnetic", "bypass", "overload", "voltage", "reverse"])
        if case == "magnetic":
            mag = random.uniform(60.0, 100.0)
            tamper_type = "Magnetic Tamper"
        elif case == "bypass":
            current = random.uniform(0.0, 0.02)
            tamper_type = "Bypass Tamper"
        elif case == "overload":
            current = random.uniform(2.0, 5.0)
            tamper_type = "Overload Tamper"
        elif case == "voltage":
            voltage = random.uniform(1.8, 2.6)
            tamper_type = "Voltage Tamper"
        elif case == "reverse":
            current = -1.0 * random.uniform(0.2, 1.0)
            tamper_type = "Reverse Flow Tamper"

    # Also check live if voltage drops below 2.7V
    if voltage < 2.7:
        tamper_type = "Voltage Tamper"

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
