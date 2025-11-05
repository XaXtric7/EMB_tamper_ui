import socket
import time
import random
import argparse


def generate_reading(tamper_probability: float) -> tuple[float, float, float]:
    """Generate one reading (voltage, current, magnetic_field).

    Tamper scenarios (randomly triggered by tamper_probability):
    - Magnetic tamper: magnetic_field spike ~ 80-120 G
    - Bypass: voltage normal, current near 0 A
    - Overload: voltage normal, high current 8-15 A
    - Voltage anomaly: voltage 170-190 V or 255-270 V
    - Reverse flow: negative current (-1 to -3 A)
    """
    # Base normal values
    voltage = 230.0 + random.uniform(-2.0, 2.0)
    current = 1.2 + random.uniform(-0.6, 0.6)
    mag = 15.0 + random.uniform(-3.0, 3.0)

    if random.random() < tamper_probability:
        case = random.choice(["magnetic", "bypass", "overload", "voltage", "reverse"])
        if case == "magnetic":
            mag = random.uniform(80.0, 120.0)
        elif case == "bypass":
            current = random.uniform(0.0, 0.02)
        elif case == "overload":
            current = random.uniform(8.0, 15.0)
        elif case == "voltage":
            voltage = random.choice([random.uniform(170.0, 190.0), random.uniform(255.0, 270.0)])
        elif case == "reverse":
            current = -1.0 * random.uniform(1.0, 3.0)

    return round(voltage, 2), round(current, 2), round(mag, 2)


def run_server(host: str, port: int, interval_s: float, tamper_probability: float):
    """Simple TCP server that streams CSV readings to one client."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)
        print(f"Simulator listening on {host}:{port} (connect UI with port = socket://{host}:{port})")
        while True:
            conn, addr = s.accept()
            print(f"Client connected from {addr}")
            try:
                with conn:
                    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    while True:
                        v, c, m = generate_reading(tamper_probability)
                        line = f"{v},{c},{m}\n".encode()
                        conn.sendall(line)
                        time.sleep(interval_s)
            except Exception as e:
                print(f"Client disconnected: {e}")


def main():
    parser = argparse.ArgumentParser(description="Tamper UI data simulator (TCP)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the simulator on")
    parser.add_argument("--port", type=int, default=7000, help="Port to bind the simulator on")
    parser.add_argument("--interval", type=float, default=0.5, help="Seconds between samples")
    parser.add_argument("--tamper", type=float, default=0.25, help="Tamper event probability per sample (0-1)")
    args = parser.parse_args()

    run_server(args.host, args.port, args.interval, max(0.0, min(1.0, args.tamper)))


if __name__ == "__main__":
    main()


