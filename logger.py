import csv
import os
import pandas as pd
from datetime import datetime


class DataLogger:
    def __init__(self, filename="logs/tamper_log.csv"):
        self.filename = filename
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Initialize CSV with headers if it doesn't exist
        if not os.path.exists(filename):
            with open(filename, "w", newline="", encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Voltage (V)", "Current (A)", 
                    "Power (W)", "Magnetic Field (G)", "Event", "Event Type"
                ])

    def log(self, timestamp, voltage, current, power, magnetic_field, event, event_type="Normal"):
        """Log sensor data with tamper event information"""
        # Replace emoji characters with plain text to avoid encoding issues
        safe_event = event.replace("⚠️", "WARNING:").replace("🔴", "").replace("🟡", "").replace("🟢", "")
        with open(self.filename, "a", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, voltage, current, power, magnetic_field, safe_event, event_type
            ])
    
    def export_to_excel(self, output_file=None):
        """Export logged data to Excel format"""
        if output_file is None:
            output_file = self.filename.replace('.csv', '.xlsx')
        
        try:
            df = pd.read_csv(self.filename)
            df.to_excel(output_file, index=False, engine='openpyxl')
            return output_file
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return None
    
    def get_statistics(self):
        """Calculate statistics from logged data"""
        try:
            df = pd.read_csv(self.filename)
            if df.empty:
                return None
            
            tamper_events = len(df[df['Event Type'] != 'Normal']) if 'Event Type' in df.columns else 0
            normal_events = len(df[df['Event Type'] == 'Normal']) if 'Event Type' in df.columns else 0
            
            stats = {
                'total_readings': len(df),
                'avg_voltage': df['Voltage (V)'].mean() if 'Voltage (V)' in df.columns else 0,
                'avg_current': df['Current (A)'].mean() if 'Current (A)' in df.columns else 0,
                'avg_power': df['Power (W)'].mean() if 'Power (W)' in df.columns else 0,
                'max_magnetic_field': df['Magnetic Field (G)'].max() if 'Magnetic Field (G)' in df.columns else 0,
                'tamper_events': tamper_events,
                'normal_events': normal_events,
                'event_types': df['Event Type'].value_counts().to_dict() if 'Event Type' in df.columns else {}
            }
            return stats
        except Exception as e:
            print(f"Error calculating statistics: {e}")
            return None
