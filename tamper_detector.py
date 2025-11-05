"""
Tamper Detection Logic
Analyzes sensor readings to detect various types of tampering events
"""

class TamperDetector:
    def __init__(self):
        # Thresholds for tamper detection
        self.voltage_normal_min = 220.0
        self.voltage_normal_max = 240.0
        self.current_min = 0.01  # Minimum expected current
        self.magnetic_normal_max = 25.0  # Normal magnetic field (Gauss)
        self.magnetic_tamper_threshold = 50.0  # Threshold for magnetic tampering
        
        # Historical data for trend analysis
        self.voltage_history = []
        self.current_history = []
        self.power_history = []
        
    def detect_tamper(self, voltage, current, magnetic_field, power):
        """
        Analyze sensor data and detect tampering events.
        Returns: (event_type, event_message)
        """
        event_type = "Normal"
        event_message = "Normal Operation"
        severity = "info"
        
        # Check for magnetic tampering (external magnet) - highest priority
        if magnetic_field > self.magnetic_tamper_threshold:
            event_type = "Magnetic Tamper"
            event_message = f"WARNING: Magnetic Interference Detected! Field: {magnetic_field:.2f} G"
            severity = "critical"
        
        # Check for reverse connection (negative current) - detect before bypass check
        elif current < -0.1:
            event_type = "Reverse Flow"
            event_message = f"WARNING: Reverse Power Flow Detected! Current: {current:.2f}A"
            severity = "warning"
        
        # Check for meter bypass (voltage present but no current)
        elif voltage >= self.voltage_normal_min and current < self.current_min:
            event_type = "Bypass Detected"
            event_message = f"WARNING: Possible Meter Bypass! Voltage: {voltage:.2f}V, Current: {current:.2f}A"
            severity = "critical"
        
        # Check for overload (high current)
        elif current > 7.0:
            event_type = "Overload Detected"
            event_message = f"WARNING: High Current Detected! Current: {current:.2f}A"
            severity = "warning"
        
        # Check for voltage anomaly
        elif voltage < self.voltage_normal_min or voltage > self.voltage_normal_max:
            event_type = "Voltage Anomaly"
            event_message = f"WARNING: Voltage Out of Range: {voltage:.2f}V"
            severity = "warning"
        
        # Check for power mismatch (voltage and current don't align with expected consumption)
        # This is a more advanced check using history
        elif len(self.power_history) > 5:
            avg_power = sum(self.power_history[-10:]) / min(len(self.power_history), 10)
            if abs(power - avg_power) > avg_power * 0.5 and power < avg_power * 0.3:
                event_type = "Power Mismatch"
                event_message = f"⚠️ Unexpected Power Drop Detected!"
                severity = "warning"
        
        # Update history (keep last 50 readings)
        self.voltage_history.append(voltage)
        self.current_history.append(current)
        self.power_history.append(power)
        
        if len(self.voltage_history) > 50:
            self.voltage_history.pop(0)
            self.current_history.pop(0)
            self.power_history.pop(0)
        
        return event_type, event_message, severity
    
    def get_statistics(self):
        """Get statistical analysis of recent readings"""
        if not self.voltage_history:
            return None
        
        return {
            'avg_voltage': sum(self.voltage_history) / len(self.voltage_history),
            'avg_current': sum(self.current_history) / len(self.current_history),
            'avg_power': sum(self.power_history) / len(self.power_history),
            'min_voltage': min(self.voltage_history),
            'max_voltage': max(self.voltage_history),
            'min_current': min(self.current_history),
            'max_current': max(self.current_history),
        }


