"""
Tamper Detection Logic
Analyzes low-voltage sensor readings to detect various types of tampering events
(for circuits using ACS712, A3144, LM7805, and a voltage divider)
"""


class TamperDetector:
    def __init__(self):
        # Thresholds tuned for ~5 V DC system
        self.voltage_normal_min = 4.7      # LM7805 output lower bound
        self.voltage_normal_max = 5.2      # Upper tolerance
        self.voltage_tamper_threshold = 2.7  # Critical low voltage

        self.current_min = 0.05            # Expected min load current (A)
        # High current limit (ACS712 5A module)
        self.overload_threshold = 2.0
        self.reverse_threshold = -0.1      # Reverse current detection

        self.magnetic_normal_max = 25.0    # Normal background field (Gauss)
        self.magnetic_tamper_threshold = 60.0  # External magnet interference

        # Historical data for trend analysis
        self.voltage_history = []
        self.current_history = []
        self.power_history = []

    def detect_tamper(self, voltage, current, magnetic_field, power):
        """
        Analyze sensor data and detect tampering events.
        Returns: (event_type, event_message, severity)
        """
        event_type = "Normal"
        event_message = "Normal Operation"
        severity = "info"

        # --- 1. Magnetic tamper (external magnet) ---
        if magnetic_field > self.magnetic_tamper_threshold:
            event_type = "Magnetic Tamper"
            event_message = f"⚠️ Magnetic Interference Detected! Field: {magnetic_field:.2f} G"
            severity = "critical"

        # --- 2. Reverse current flow ---
        elif current < self.reverse_threshold:
            event_type = "Reverse Flow"
            event_message = f"⚠️ Reverse Power Flow Detected! Current: {current:.2f} A"
            severity = "warning"

        # --- 3. Bypass (no current, but voltage present) ---
        elif voltage >= 4.5 and current < self.current_min:
            event_type = "Bypass Detected"
            event_message = f"⚠️ Possible Bypass! Voltage: {voltage:.2f} V, Current: {current:.2f} A"
            severity = "critical"

        # --- 4. Overload condition ---
        elif current > self.overload_threshold:
            event_type = "Overload Detected"
            event_message = f"⚠️ High Current Draw Detected! Current: {current:.2f} A"
            severity = "warning"

        # --- 5. Voltage tamper (below 2.7 V) ---
        elif voltage < self.voltage_tamper_threshold:
            event_type = "Voltage Tamper"
            event_message = f"⚠️ Critical Voltage Drop! Voltage: {voltage:.2f} V"
            severity = "critical"

        # --- 6. Voltage anomaly (minor deviation) ---
        elif voltage < self.voltage_normal_min or voltage > self.voltage_normal_max:
            event_type = "Voltage Anomaly"
            event_message = f"⚠️ Voltage Out of Normal Range: {voltage:.2f} V"
            severity = "warning"

        # --- 7. Power anomaly trend (historical deviation) ---
        elif len(self.power_history) > 5:
            avg_power = sum(
                self.power_history[-10:]) / min(len(self.power_history), 10)
            if avg_power > 0.1:  # avoid division by zero / noise
                if abs(power - avg_power) > avg_power * 0.5 and power < avg_power * 0.3:
                    event_type = "Power Mismatch"
                    event_message = f"⚠️ Unexpected Power Drop Detected!"
                    severity = "warning"

        # --- Update rolling history (keep last 50 readings) ---
        self.voltage_history.append(voltage)
        self.current_history.append(current)
        self.power_history.append(power)

        if len(self.voltage_history) > 50:
            self.voltage_history.pop(0)
            self.current_history.pop(0)
            self.power_history.pop(0)

        return event_type, event_message, severity

    def get_statistics(self):
        """Return average/min/max stats for recent readings."""
        if not self.voltage_history:
            return None

        return {
            "avg_voltage": sum(self.voltage_history) / len(self.voltage_history),
            "avg_current": sum(self.current_history) / len(self.current_history),
            "avg_power": sum(self.power_history) / len(self.power_history),
            "min_voltage": min(self.voltage_history),
            "max_voltage": max(self.voltage_history),
            "min_current": min(self.current_history),
            "max_current": max(self.current_history),
        }
