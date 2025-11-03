# ⚡ Electricity Tamper Detection System

A comprehensive hardware-software solution for detecting electricity theft and tampering by monitoring voltage, current, and magnetic field in electrical lines using ATmega328 and Python UI.

## 🎯 Features

- **Real-Time Monitoring**: Live visualization of voltage, current, power, and magnetic field
- **Advanced Tamper Detection**: Automatic detection of:
  - Magnetic interference (external magnets)
  - Meter bypass attempts
  - Voltage anomalies
  - Power flow irregularities
  - Reverse power flow
- **Beautiful Modern UI**: Dark-themed interface built with CustomTkinter
- **Live Graphs**: Real-time plotting of sensor data with matplotlib
- **Comprehensive Logging**: CSV and Excel export capabilities
- **Statistics Dashboard**: Detailed analysis and event breakdown
- **Event Logging**: Complete audit trail of all tamper events

## 🔧 Hardware Components

- ATmega328 microcontroller
- Current Transformer (CT) for AC current measurement
- Voltage Sensor Module (ZMPT101B)
- Hall Effect Sensor (A3144) for magnetic field detection
- Buck Converter (LM2596)
- USB-TTL Adapter for serial communication

## 📋 Software Requirements

- Python 3.8 or higher
- Required Python packages (see requirements.txt)

## 🚀 Installation

1. **Clone or download this repository**

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Serial Port**:
   - Edit `ui.py` line 71 to set your COM port:
     ```python
     self.reader = SerialReader(port="COM3", baudrate=9600, mock_mode=True)
     ```
   - Change `"COM3"` to your actual COM port (e.g., "COM4", "/dev/ttyUSB0" for Linux)
   - Set `mock_mode=False` when connecting to real hardware

## 💻 Usage

### Running the Application

```bash
python main.py
```

### Using Mock Data (for Testing)

By default, the application runs in mock mode, generating realistic sensor data with occasional tamper events. This is perfect for demonstrations without hardware.

### Connecting to Hardware

1. Ensure your ATmega328 is programmed to send data in the format:

   ```
   voltage,current,magnetic_field
   ```

   Example: `230.5,1.2,18`

2. Connect the USB-TTL adapter to your computer

3. Update the COM port in `ui.py` and set `mock_mode=False`

4. Run the application

### Application Features

#### Main Interface

- **Left Panel**: Real-time sensor readings with large, easy-to-read displays
- **Right Panel**: Tabbed graphs showing voltage, current, power, and magnetic field over time
- **Bottom Panel**: Event log and statistics dashboard

#### Controls

- **Start Monitoring**: Begin reading sensor data
- **Stop Monitoring**: Pause data collection
- **Export to Excel**: Export all logged data to Excel format

#### Event Detection

The system automatically detects:

- **Normal Operation**: All parameters within expected ranges
- **Magnetic Tamper**: Magnetic field exceeds threshold (>50G)
- **Bypass Detected**: Voltage present but current drops to near zero
- **Voltage Anomaly**: Voltage outside normal range (220-240V)
- **Power Mismatch**: Unexpected power consumption patterns
- **Reverse Flow**: Negative power flow detected

## 📊 Data Format

### Serial Data Format

The ATmega328 should send data in CSV format:

```
voltage,current,magnetic_field
```

Example: `230.5,1.23,18.5`

### Log File Format

Data is logged to `logs/tamper_log.csv` with columns:

- Timestamp
- Voltage (V)
- Current (A)
- Power (W)
- Magnetic Field (G)
- Event (Description)
- Event Type

## 🔍 Configuration

### Tamper Detection Thresholds

Edit `tamper_detector.py` to adjust detection thresholds:

```python
self.voltage_normal_min = 220.0    # Minimum normal voltage
self.voltage_normal_max = 240.0    # Maximum normal voltage
self.current_min = 0.01            # Minimum expected current
self.magnetic_normal_max = 25.0    # Normal magnetic field max
self.magnetic_tamper_threshold = 50.0  # Tamper detection threshold
```

## 📁 Project Structure

```
tamper_ui/
│
├── main.py              # Application entry point
├── ui.py                # Main UI application
├── serial_reader.py     # Serial communication handler
├── logger.py            # Data logging and export
├── tamper_detector.py   # Tamper detection logic
├── mock_data.py         # Mock data generator (legacy)
├── requirements.txt     # Python dependencies
├── logs/                # Log directory
│   └── tamper_log.csv   # Data log file
└── README.md            # This file
```

## 🎨 UI Features

- **Dark Theme**: Modern, eye-friendly dark interface
- **Color-Coded Alerts**:
  - Green: Normal operation
  - Orange: Warning events
  - Red: Critical tamper events
- **Real-Time Graphs**: Smooth, animated graphs updating every 500ms
- **Statistics Dashboard**: Comprehensive analysis of collected data
- **Event Log**: Searchable table with all sensor readings and events

## 🔬 Demonstration Mode

The application includes built-in mock data generation for demonstrations:

- Simulates realistic voltage (228-232V), current (0.6-1.1A), and magnetic field (12-18G)
- Randomly generates tamper events (5% probability):
  - Magnetic tamper: High magnetic field spikes
  - Bypass attempts: Current drops to near zero

## 📈 Statistics Provided

- Total readings count
- Average voltage, current, and power
- Maximum magnetic field detected
- Total tamper events
- Event type breakdown

## 🛠️ Troubleshooting

### Serial Port Not Found

- Check device manager (Windows) or `ls /dev/tty*` (Linux) for available ports
- Ensure USB-TTL adapter drivers are installed
- Try different COM ports

### No Data Appearing

- Verify baud rate matches ATmega328 settings (default: 9600)
- Check serial connection
- Enable mock mode for testing: `mock_mode=True`

### Graphs Not Updating

- Click "Start Monitoring" button
- Check that serial data is being received
- Verify data format matches expected CSV format

## 📝 Notes

- The application runs in mock mode by default for easy testing
- All data is automatically logged to CSV
- Excel export includes all columns from the log file
- Graphs maintain the last 100 data points for performance

## 🎯 Future Enhancements

- Database integration for long-term storage
- MQTT support for IoT connectivity
- Email/SMS alerts for tamper events
- Historical data analysis and trends
- Mobile app integration
- Cloud dashboard

## 📄 License

This project is designed for educational and demonstration purposes.

## 👨‍💻 Development

Built with:

- Python 3.8+
- CustomTkinter for modern UI
- Matplotlib for visualization
- Pandas for data handling
- PySerial for hardware communication

---

**Ready for Demonstration** ✨

The system is fully functional and ready to showcase your embedded systems and Python development skills!

