import serial
import time
import random

class SerialReader:
    def __init__(self, port="COM3", baudrate=9600, mock_mode=False):
        self.port = port
        self.baudrate = baudrate
        self.mock_mode = mock_mode
        self.ser = None
        
        if not mock_mode:
            try:
                self.ser = serial.Serial(port, baudrate, timeout=1)
                print(f"✅ Connected to {port} at {baudrate} baud")
            except Exception as e:
                print(f"⚠️ Could not open serial port {port}. Running in mock mode:", e)
                self.mock_mode = True
                self.ser = None
    
    def read_sensor_data(self):
        """
        Reads sensor data from serial port.
        Expected format: "voltage,current,magnetic_field" (e.g., "230.5,1.2,18")
        Returns: dict with voltage, current, magnetic_field, power, or None if no data
        """
        if self.mock_mode:
            # Generate realistic mock data for demonstration
            return self._generate_mock_data()
        
        if self.ser and self.ser.in_waiting:
            try:
                line = self.ser.readline().decode().strip()
                if line:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        voltage = float(parts[0])
                        current = float(parts[1])
                        magnetic_field = float(parts[2])
                        power = voltage * current  # Calculate power
                        
                        return {
                            'voltage': voltage,
                            'current': current,
                            'magnetic_field': magnetic_field,
                            'power': power,
                            'timestamp': time.time()
                        }
            except Exception as e:
                print(f"Error parsing data: {e}")
                return None
        
        return None
    
    def _generate_mock_data(self):
        """Generate realistic mock sensor data for testing"""
        base_voltage = 230.0 + random.uniform(-2, 2)
        base_current = 0.8 + random.uniform(-0.2, 0.3)
        base_mag = 15 + random.uniform(-3, 3)
        
        # Occasionally simulate tamper events
        if random.random() < 0.05:  # 5% chance of tamper
            if random.random() < 0.5:
                # Magnetic tamper - high magnetic field
                base_mag = 80 + random.uniform(-10, 20)
            else:
                # Bypass - current drops to near zero but voltage stays
                base_current = 0.01 + random.uniform(-0.01, 0.02)
        
        return {
            'voltage': round(base_voltage, 2),
            'current': round(base_current, 2),
            'magnetic_field': round(base_mag, 2),
            'power': round(base_voltage * base_current, 2),
            'timestamp': time.time()
        }
    
    def close(self):
        """Close serial connection"""
        if self.ser and self.ser.is_open:
            self.ser.close()
