import serial
import time
import random


class SerialReader:
    def __init__(self, port="COM4", baudrate=9600, mock_mode=False):
        self.port = port
        self.baudrate = baudrate
        self.mock_mode = mock_mode
        self.ser = None

        if not mock_mode:
            try:
                if isinstance(port, str) and (port.startswith('socket://') or port.startswith('loop://')):
                    self.ser = serial.serial_for_url(port, timeout=1)
                else:
                    self.ser = serial.Serial(port, baudrate, timeout=1)
                print(f"Connected to {port} at {baudrate} baud")
            except Exception as e:
                print(f"Could not open serial port {port}: {e}")
                self.ser = None
                self.mock_mode = False  # remain in non-mock mode until user chooses mock

    def open_port(self):
        """Attempt to open the configured serial port."""
        if self.ser and self.ser.is_open:
            return True
        try:
            if isinstance(self.port, str) and (self.port.startswith('socket://') or self.port.startswith('loop://')):
                self.ser = serial.serial_for_url(self.port, timeout=1)
            else:
                self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except Exception as e:
            print(f"Failed to connect to {self.port}: {e}")
            self.ser = None
            return False

    def read_sensor_data(self):
        """
        Reads sensor data from serial port.
        Expected format: "voltage,current,magnetic_field,tamper_type"
        Example: "4.98,0.42,13.1,Normal"
        Returns: dict with voltage, current, magnetic_field, power, tamper_type
        """
        if self.mock_mode:
            return self._generate_mock_data()

        if self.ser and self.ser.in_waiting:
            try:
                line = self.ser.readline().decode().strip()
                if not line:
                    return None

                parts = line.split(',')
                if len(parts) >= 4:
                    voltage = float(parts[0])
                    current = float(parts[1])
                    magnetic_field = float(parts[2])
                    tamper_type = parts[3].strip()
                elif len(parts) == 3:  # fallback if tamper field missing
                    voltage, current, magnetic_field = map(float, parts)
                    tamper_type = "Normal"
                else:
                    return None

                # compute derived quantities
                power = round(voltage * current, 3)

                # double-check tamper based on thresholds
                if voltage < 2.5 and tamper_type == "Normal":
                    tamper_type = "Voltage Tamper"

                return {
                    "voltage": voltage,
                    "current": current,
                    "magnetic_field": magnetic_field,
                    "power": power,
                    "tamper_type": tamper_type,
                    "timestamp": time.time()
                }

            except Exception as e:
                print(f"Error parsing data: {e}")
                return None

        return None

    def _generate_mock_data(self):
        """Generate realistic low-voltage mock data for testing"""
        # Check remote states from JSON
        power_status = "ON"
        magnet_status = "ON"
        if os.path.exists("power_state.json"):
            try:
                with open("power_state.json", "r") as f:
                    states = json.load(f)
                    power_status = states.get("power", "ON")
                    magnet_status = states.get("magnet", "ON")
            except:
                pass

        # Default values
        voltage = 2.8 + random.uniform(-0.05, 0.05)
        current = 0.9 + random.uniform(0.0, 0.1)
        magnetic_field = 15.0 + random.uniform(-2.0, 2.0)
        tamper_type = "Normal"

        # Apply Power Status
        if power_status == "OFF":
            voltage = 0.0
            current = 0.0
            tamper_type = "Power Cut"
        elif power_status == "STABLE":
            voltage = 2.7 + random.uniform(0.0, 0.1)
            current = 0.9 + random.uniform(0.0, 0.1)
            tamper_type = "Normal (Stable)"

        # Apply Magnet Status independently
        if magnet_status == "OFF":
            magnetic_field = 0.0
            if tamper_type == "Normal":
                tamper_type = "Magnet Sensor Cut"

        # Random tamper events only if both are ON
        if power_status == "ON" and magnet_status == "ON":
            if random.random() < 0.25:
                event = random.choice(["bypass", "voltage", "magnetic"])
                if event == "bypass":
                    current = 0.0
                    tamper_type = "Bypass Tamper"
                elif event == "voltage":
                    voltage = random.uniform(1.8, 2.4)
                    tamper_type = "Voltage Tamper"
                elif event == "magnetic":
                    magnetic_field = random.uniform(60.0, 100.0)
                    tamper_type = "Magnetic Tamper"

        # Threshold checks
        if voltage < 2.5 and power_status != "OFF":
            tamper_type = "Voltage Tamper"
        if current == 0.0 and power_status != "OFF":
            tamper_type = "Bypass Tamper"
        if magnetic_field >= 50.0:
            tamper_type = "Magnetic Tamper"

        power = round(voltage * current, 3)

        return {
            "voltage": voltage,
            "current": current,
            "magnetic_field": magnetic_field,
            "power": power,
            "tamper_type": tamper_type,
            "timestamp": time.time()
        }

    def close(self):
        """Close serial connection"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port closed.")
