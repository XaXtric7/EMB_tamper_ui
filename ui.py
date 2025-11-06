import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
from datetime import datetime
import threading
import time
import os
import pandas as pd
from serial_reader import SerialReader
from logger import DataLogger
from tamper_detector import TamperDetector

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Custom color palette
COLORS = {
    "primary": "#1E88E5",
    "secondary": "#7B1FA2",
    "success": "#43A047",
    "warning": "#FFC107",
    "danger": "#E53935",
    "info": "#00ACC1",
    "background": "#121212",
    "card": "#1E1E1E",
    "text": "#FFFFFF",
    "text_secondary": "#B0B0B0",
    "border": "#333333",
    "chart_colors": ["#1E88E5", "#43A047", "#FFC107", "#E53935", "#7B1FA2"]
}


class TamperUI:
    def __init__(self, root=None):
        # Window setup
        self.root = root if root else ctk.CTk()
        self.root.title("⚡ Electricity Tamper Detection System")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)

        # Set theme mode
        self.theme_mode = "dark"
        ctk.set_appearance_mode(self.theme_mode)

        # Initialize components
        self.reader = SerialReader(port="COM4", baudrate=9600, mock_mode=False)
        self.logger = DataLogger("logs/tamper_log.csv")
        self.detector = TamperDetector()

        # Data containers
        self.data_points = 200  # Increased number of points for better visualization
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.power_data = []
        self.magnetic_data = []

        # Current values
        self.current_voltage = 0.0
        self.current_current = 0.0
        self.current_power = 0.0
        self.current_magnetic = 0.0
        self.current_event_type = "Normal"

        # Event history
        self.event_history = []

        # Statistics
        self.stats = {
            "voltage_min": float('inf'),
            "voltage_max": float('-inf'),
            "voltage_avg": 0.0,
            "current_min": float('inf'),
            "current_max": float('-inf'),
            "current_avg": 0.0,
            "power_min": float('inf'),
            "power_max": float('-inf'),
            "power_avg": 0.0,
            "magnetic_min": float('inf'),
            "magnetic_max": float('-inf'),
            "magnetic_avg": 0.0,
            "normal_events": 0,
            "tamper_events": 0,
            "total_readings": 0
        }

        # Dictionary to store statistics labels
        self.stats_labels = {}

        # Graph references
        self.figures = {}
        self.canvases = {}
        self.axes = {}

        # Thread control
        self.running = False
        self.update_thread = None

        # Current event message
        self.current_event = "Waiting for data..."

        # Animation references
        self.animations = []

        # Create UI
        self.create_ui()

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        if self.theme_mode == "dark":
            self.theme_mode = "light"
            ctk.set_appearance_mode("light")
        else:
            self.theme_mode = "dark"
            ctk.set_appearance_mode("dark")

    def update_ui(self):
        """Update UI elements based on new data"""
        try:
            # Update current readings display
            if hasattr(self, 'voltage_value') and self.voltage_data:
                self.voltage_value.configure(
                    text=f"{self.voltage_data[-1]:.2f} V")

            if hasattr(self, 'current_value') and self.current_data:
                self.current_value.configure(
                    text=f"{self.current_data[-1]:.2f} A")

            if hasattr(self, 'power_value') and self.power_data:
                self.power_value.configure(text=f"{self.power_data[-1]:.2f} W")

            if hasattr(self, 'magnetic_value') and self.magnetic_data:
                self.magnetic_value.configure(
                    text=f"{self.magnetic_data[-1]:.2f} μT")

            # Update statistics display
            self.update_stats_ui()

            # Update event log if available
            if hasattr(self, 'event_list') and hasattr(self, 'event_history'):
                # Keep UI in sync with the latest events
                pass

        except Exception as e:
            print(f"Error updating UI: {e}")

    def update_stats_ui(self):
        """Update statistics labels in the UI"""
        try:
            if hasattr(self, 'stats') and hasattr(self, 'stats_labels'):
                for key, value in self.stats.items():
                    if key in self.stats_labels:
                        label, unit = self.stats_labels[key]
                        label.configure(text=f"{value:.2f} {unit}")
        except Exception as e:
            print(f"Error updating statistics UI: {e}")

    def add_event_to_log(self, event):
        """Add a new event to the event log"""
        try:
            if not hasattr(self, 'event_history'):
                self.event_history = []

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            event_with_time = f"{timestamp} - {event}"
            self.event_history.append(event_with_time)

            # Update event list if it exists
            if hasattr(self, 'event_list'):
                self.event_list.insert("", "end", values=(timestamp, event))
        except Exception as e:
            print(f"Error adding event to log: {e}")

    def update_graphs(self):
        """Update all graph plots with new data"""
        try:
            if hasattr(self, 'axes') and self.axes:
                # Update voltage/current graph
                if 'voltage_current' in self.axes:
                    ax = self.axes['voltage_current']
                    ax.clear()
                    ax.plot(self.voltage_data, 'b-', label='Voltage (V)')
                    ax.plot(self.current_data, 'r-', label='Current (A)')
                    ax.set_title('Voltage and Current')
                    ax.set_ylabel('Value')
                    ax.legend(loc='upper right')
                    ax.grid(True, linestyle='--', alpha=0.7)

                # Update power graph
                if 'power' in self.axes:
                    ax = self.axes['power']
                    ax.clear()
                    ax.plot(self.power_data, 'g-', label='Power (W)')
                    ax.set_title('Power Consumption')
                    ax.set_ylabel('Watts')
                    ax.legend(loc='upper right')
                    ax.grid(True, linestyle='--', alpha=0.7)

                # Update magnetic field graph
                if 'magnetic' in self.axes:
                    ax = self.axes['magnetic']
                    ax.clear()
                    ax.plot(self.magnetic_data, 'm-',
                            label='Magnetic Field (μT)')

                    # Add threshold line if detector has magnetic_tamper_threshold
                    if hasattr(self, 'detector') and hasattr(self.detector, 'magnetic_tamper_threshold'):
                        ax.axhline(y=self.detector.magnetic_tamper_threshold, color='r', linestyle='--',
                                   label=f'Threshold ({self.detector.magnetic_tamper_threshold})')

                    ax.set_title('Magnetic Field')
                    ax.set_ylabel('μT')
                    ax.legend(loc='upper right')
                    ax.grid(True, linestyle='--', alpha=0.7)

                # Redraw all canvases
                if hasattr(self, 'canvases'):
                    for canvas in self.canvases.values():
                        canvas.draw()
        except Exception as e:
            print(f"Error updating graphs: {e}")

    def show_settings(self):
        """Show settings dialog for COM port and threshold configuration"""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)

        # COM Port settings
        com_frame = ctk.CTkFrame(settings_window)
        com_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(com_frame, text="COM Port:").pack(side="left", padx=10)
        com_entry = ctk.CTkEntry(com_frame, width=100)
        com_entry.pack(side="left", padx=10)
        com_entry.insert(0, self.reader.port if hasattr(
            self.reader, 'port') else "COM1")

        # Threshold settings
        threshold_frame = ctk.CTkFrame(settings_window)
        threshold_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(threshold_frame, text="Magnetic Threshold:").pack(
            side="left", padx=10)
        threshold_entry = ctk.CTkEntry(threshold_frame, width=100)
        threshold_entry.pack(side="left", padx=10)
        threshold_entry.insert(0, str(self.detector.magnetic_tamper_threshold if hasattr(
            self.detector, 'magnetic_tamper_threshold') else 50.0))

        # Save button
        save_btn = ctk.CTkButton(
            settings_window,
            text="Save Settings",
            command=lambda: self.save_settings(
                com_entry.get(), float(threshold_entry.get()), settings_window)
        )
        save_btn.pack(pady=20)

    def save_settings(self, com_port, threshold, window=None):
        """Save settings and close the settings window"""
        if hasattr(self.reader, 'port'):
            self.reader.port = com_port

        if hasattr(self.detector, 'magnetic_tamper_threshold'):
            self.detector.magnetic_tamper_threshold = threshold

        if window:
            window.destroy()

        # Attempt to reconnect using the new settings
        if not self.reader.mock_mode:
            connected = self.reader.open_port()
            if connected:
                self.status_indicator.configure(text_color="#4CAF50")
                self.status_label.configure(
                    text=f"Connected {self.reader.port}")
            else:
                self.status_indicator.configure(text_color="gray")
                self.status_label.configure(text="Disconnected")

    def refresh_data(self):
        """Manually refresh data from sensors"""
        data = self.reader.read_sensor_data()
        if data:
            self.update_readings(data)

    def create_ui(self):
        """Create the complete UI layout with modern dashboard design"""
        # Header Frame with gradient effect
        header = ctk.CTkFrame(self.root, height=80,
                              corner_radius=0, fg_color=COLORS["card"])
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="⚡ Electricity Tamper Detection System",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text"]
        )
        title.pack(side="left", padx=20, pady=20)

        # Header controls
        header_controls = ctk.CTkFrame(header, fg_color="transparent")
        header_controls.pack(side="right", padx=20, pady=20)

        # Removed theme toggle and start/stop buttons

        # Settings button (to configure COM/threshold)
        self.settings_btn = ctk.CTkButton(
            header_controls,
            text="⚙️ Settings",
            command=self.show_settings,
            width=90,
            height=30,
            fg_color=COLORS["secondary"],
            hover_color="#6A1B9A"
        )
        self.settings_btn.pack(side="left", padx=(0, 10))

        # Status indicator with improved styling
        self.status_frame = ctk.CTkFrame(
            header_controls, fg_color="transparent")
        self.status_frame.pack(side="left", padx=5)

        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=20),
            text_color="gray"
        )
        self.status_indicator.pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Disconnected",
            font=ctk.CTkFont(size=16)
        )
        self.status_label.pack(side="left", padx=5)

        # Main container with modern grid layout
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Single large panel for graphs
        graphs_panel = ctk.CTkFrame(
            main_container, fg_color=COLORS["card"], corner_radius=15)
        graphs_panel.pack(fill="both", expand=True)

        self.create_right_panel(graphs_panel)

        # Bottom Panel - Event Log & Statistics with card-like appearance
        bottom_container = ctk.CTkFrame(self.root, fg_color="transparent")
        bottom_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Bottom panel contains only the Event Log
        bottom_log = ctk.CTkFrame(
            bottom_container, fg_color=COLORS["card"], corner_radius=15)
        bottom_log.pack(fill="both", expand=True)

        self.create_event_log_panel(bottom_log)

        # Auto-start monitoring so UI works without unused buttons
        try:
            self.start_monitoring()
        except Exception:
            pass

    def create_left_panel(self, parent):
        """Create left panel with current readings and controls"""
        # Title with icon
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(fill="x", pady=(20, 10), padx=20)

        title = ctk.CTkLabel(
            title_frame,
            text="Real-Time Sensor Readings",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text"]
        )
        title.pack(side="left")

        # Refresh button
        refresh_btn = ctk.CTkButton(
            title_frame,
            text="↻",
            width=30,
            height=30,
            command=self.refresh_data,
            fg_color=COLORS["primary"],
            hover_color="#1976D2"
        )
        refresh_btn.pack(side="right")

        # Voltage reading with improved styling
        self.create_reading_card(
            parent, "Voltage", "0.0", "V", "voltage_label", COLORS["primary"])

        # Current reading
        self.create_reading_card(
            parent, "Current", "0.0", "A", "current_label", COLORS["success"])

        # Power reading
        self.create_reading_card(
            parent, "Power", "0.0", "W", "power_label", COLORS["warning"])

        # Magnetic Field reading
        self.create_reading_card(
            parent, "Magnetic Field", "0.0", "G", "magnetic_label", COLORS["secondary"])

        # Event Status Card with improved styling
        event_card = ctk.CTkFrame(
            parent, corner_radius=15, fg_color=COLORS["card"], border_width=1, border_color=COLORS["border"])
        event_card.pack(fill="x", padx=20, pady=10)

        event_title = ctk.CTkLabel(
            event_card,
            text="Tamper Status",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        )
        event_title.pack(pady=(15, 5))

        self.event_status_label = ctk.CTkLabel(
            event_card,
            text="Normal Operation",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["success"]
        )
        self.event_status_label.pack(pady=(0, 15))

        # Control Buttons with improved styling
        controls_frame = ctk.CTkFrame(parent, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=10)

        # Button row 1
        btn_row1 = ctk.CTkFrame(controls_frame, fg_color="transparent")
        btn_row1.pack(fill="x", pady=5)

        self.start_btn = ctk.CTkButton(
            btn_row1,
            text="▶ Start Monitoring",
            command=self.start_monitoring,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color=COLORS["success"],
            hover_color="#388E3C"
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.stop_btn = ctk.CTkButton(
            btn_row1,
            text="⏹ Stop",
            command=self.stop_monitoring,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color=COLORS["danger"],
            hover_color="#C62828",
            state="disabled"
        )
        self.stop_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Button row 2
        btn_row2 = ctk.CTkFrame(controls_frame, fg_color="transparent")
        btn_row2.pack(fill="x", pady=5)

        self.export_btn = ctk.CTkButton(
            btn_row2,
            text="📊 Export to Excel",
            command=self.export_to_excel,
            font=ctk.CTkFont(size=14),
            height=35,
            fg_color=COLORS["primary"],
            hover_color="#1976D2"
        )
        self.export_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.settings_btn = ctk.CTkButton(
            btn_row2,
            text="⚙️ Settings",
            command=self.show_settings,
            font=ctk.CTkFont(size=14),
            height=35,
            fg_color=COLORS["secondary"],
            hover_color="#6A1B9A"
        )
        self.settings_btn.pack(side="right", fill="x",
                               expand=True, padx=(5, 0))

    def create_reading_card(self, parent, label, value, unit, attr_name, accent_color=None):
        """Create a sensor reading card with improved styling"""
        card = ctk.CTkFrame(parent, corner_radius=15,
                            fg_color=COLORS["card"], border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", padx=20, pady=8)

        # Header with icon and label
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))

        label_widget = ctk.CTkLabel(
            header,
            text=label,
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        )
        label_widget.pack(side="left")

        # Value display with large font
        value_frame = ctk.CTkFrame(card, fg_color="transparent")
        value_frame.pack(fill="x", padx=15, pady=(0, 15))

        value_label = ctk.CTkLabel(
            value_frame,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=accent_color if accent_color else COLORS["text"]
        )
        value_label.pack(side="left")
        setattr(self, attr_name, value_label)

        unit_label = ctk.CTkLabel(
            value_frame,
            text=unit,
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        )
        unit_label.pack(side="left", padx=(5, 0), pady=(8, 0))

    def create_right_panel(self, parent):
        """Create right panel with real-time graphs"""
        # Create notebook for tabbed graphs
        notebook = ctk.CTkTabview(parent)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Voltage & Current Tab
        tab1 = notebook.add("Voltage & Current")
        self.create_graph(tab1, "Voltage (V)", "Current (A)",
                          ["voltage_data", "current_data"],
                          ["#4CAF50", "#2196F3"])

        # Power Tab
        tab2 = notebook.add("Power")
        self.create_graph(tab2, "Power (W)", None,
                          ["power_data"],
                          ["#FF9800"])

        # Magnetic Field Tab
        tab3 = notebook.add("Magnetic Field")
        self.create_graph(tab3, "Magnetic Field (G)", None,
                          ["magnetic_data"],
                          ["#9C27B0"])

    def create_graph(self, parent, y1_label, y2_label, data_attrs, colors):
        """Create a matplotlib graph in the given parent"""
        fig, ax = plt.subplots(figsize=(10, 4), facecolor='#2b2b2b')
        ax.set_facecolor('#1e1e1e')
        fig.patch.set_facecolor('#2b2b2b')

        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['right'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.tick_params(colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('white')

        lines = []
        ax2 = None

        if y1_label:
            line1, = ax.plot([], [], color=colors[0],
                             linewidth=2, label=y1_label)
            lines.append((line1, data_attrs[0], ax))

        if y2_label and len(colors) > 1:
            ax2 = ax.twinx()
            ax2.spines['bottom'].set_color('white')
            ax2.spines['top'].set_color('white')
            ax2.spines['right'].set_color('white')
            ax2.spines['left'].set_color('white')
            ax2.tick_params(colors='white')
            ax2.yaxis.label.set_color('white')
            line2, = ax2.plot([], [], color=colors[1],
                              linewidth=2, label=y2_label)
            lines.append((line2, data_attrs[1], ax2))
            ax2.set_ylabel(y2_label, color='white')

        ax.set_xlabel("Time (samples)", color='white')
        ax.set_ylabel(y1_label, color='white')
        ax.set_title(f"Real-Time {y1_label} Monitoring",
                     color='white', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, color='gray')
        ax.legend(loc='upper left')

        if y2_label and len(colors) > 1:
            ax2.legend(loc='upper right')

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Store animation reference
        if not hasattr(self, 'animations'):
            self.animations = []

        def animate(frame):
            for line, data_attr, axis in lines:
                if data_attr == "voltage_data":
                    data = self.voltage_data
                elif data_attr == "current_data":
                    data = self.current_data
                elif data_attr == "power_data":
                    data = self.power_data
                elif data_attr == "magnetic_data":
                    data = self.magnetic_data
                else:
                    data = []

                if len(data) > 0:
                    x_data = np.arange(len(data))
                    line.set_data(x_data, data)
                    if len(data) > 1:
                        axis.set_xlim(0, max(10, len(data)))
                        y_min = min(data) * \
                            0.9 if min(data) > 0 else min(data) * 1.1
                        y_max = max(data) * \
                            1.1 if max(data) > 0 else max(data) * 0.9
                        if y_min == y_max:
                            y_max = y_min + 1
                        axis.set_ylim(max(0, y_min), y_max)
                    else:
                        axis.set_ylim(0, max(data[0] * 1.2, 10))
                else:
                    axis.set_xlim(0, 10)
                    axis.set_ylim(0, 10)

            fig.tight_layout()
            canvas.draw()

        anim = FuncAnimation(fig, animate, interval=500,
                             blit=False, cache_frame_data=False)
        self.animations.append(anim)

    def create_bottom_panel(self, parent):
        """Create bottom panel with event log and statistics"""
        # Create notebook
        notebook = ctk.CTkTabview(parent)
        notebook.pack(fill="both", expand=True)

        # Event Log Tab
        log_tab = notebook.add("Event Log")
        self.create_event_log(log_tab)

        # Statistics Tab
        stats_tab = notebook.add("Statistics")
        self.create_statistics_panel(stats_tab)

    def create_event_log_panel(self, parent):
        """Create event log panel with tamper events history"""
        # Title
        title = ctk.CTkLabel(
            parent,
            text="Tamper Event Log",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text"]
        )
        title.pack(pady=(20, 10), padx=20, anchor="w")

        # Create treeview with scrollbar
        tree_frame = ctk.CTkFrame(parent, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Configure treeview style (use clam theme so headings render clearly)
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure(
            "Treeview",
            background=COLORS["card"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["card"],
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background="#2A2A2A",
            foreground=COLORS["text"],
            borderwidth=1,
            relief="flat",
            font=("Segoe UI", 10, "bold")
        )
        style.map('Treeview', background=[('selected', COLORS["primary"])])

        # Create scrollbar
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")

        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Time", "Voltage", "Current", "Power",
                     "Mag Field", "Event", "Type"),
            show="headings",
            yscrollcommand=scrollbar_y.set
        )

        scrollbar_y.config(command=self.tree.yview)

        # Configure columns
        self.tree.heading("Time", text="Timestamp")
        self.tree.heading("Voltage", text="Voltage (V)")
        self.tree.heading("Current", text="Current (A)")
        self.tree.heading("Power", text="Power (W)")
        self.tree.heading("Mag Field", text="Mag Field (G)")
        self.tree.heading("Event", text="Event")
        self.tree.heading("Type", text="Type")

        self.tree.column("Time", width=150)
        self.tree.column("Voltage", width=100)
        self.tree.column("Current", width=100)
        self.tree.column("Power", width=100)
        self.tree.column("Mag Field", width=120)
        self.tree.column("Event", width=250)
        self.tree.column("Type", width=150)

        # Tag styles for highlighting
        self.tree.tag_configure(
            # normal rows
            'normal', background=COLORS["card"], foreground=COLORS["text"])
        self.tree.tag_configure(
            'warning', background="#5D4037", foreground="#FFE082")  # amber on brown
        # purple with white text
        self.tree.tag_configure(
            'critical', background="#8E24AA", foreground="#FFFFFF")
        self.tree.pack(fill="both", expand=True)

        # Load existing log data from CSV
        self.load_existing_logs()

    def load_existing_logs(self):
        """Load existing log data from CSV file into the tree view"""
        try:
            import pandas as pd
            if hasattr(self, 'logger') and hasattr(self.logger, 'filename'):
                log_file = self.logger.filename
                if os.path.exists(log_file):
                    df = pd.read_csv(log_file)
                    if len(df) > 0:
                        # Get severity mapping from event types
                        for idx, row in df.iterrows():
                            timestamp = str(row.get('Timestamp', ''))
                            voltage = f"{row.get('Voltage (V)', 0):.2f}"
                            current = f"{row.get('Current (A)', 0):.2f}"
                            power = f"{row.get('Power (W)', 0):.2f}"
                            mag_field = f"{row.get('Magnetic Field (G)', 0):.2f}"
                            event = str(row.get('Event', ''))
                            event_type = str(row.get('Event Type', 'Normal'))

                            # Determine severity/tag based on event type
                            if event_type != "Normal":
                                if "critical" in event.lower() or event_type in ["Magnetic Tamper", "Bypass Detected"]:
                                    tag = 'critical'
                                else:
                                    tag = 'warning'
                            else:
                                tag = 'normal'

                            self.tree.insert("", "end", values=(
                                timestamp, voltage, current, power, mag_field,
                                event[:40] +
                                "..." if len(event) > 40 else event,
                                event_type
                            ), tags=(tag,))

                        # Scroll to bottom to show most recent
                        children = self.tree.get_children()
                        if children:
                            self.tree.see(children[-1])
        except Exception as e:
            print(f"Error loading existing logs: {e}")

    def create_stats_panel(self, parent):
        """Create statistics panel with data analysis"""
        # Title
        title = ctk.CTkLabel(
            parent,
            text="Statistical Analysis",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text"]
        )
        title.pack(pady=(20, 15), padx=20, anchor="w")

        # Stats grid
        stats_frame = ctk.CTkFrame(parent, fg_color="transparent")
        stats_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Create grid layout for stats
        for i, category in enumerate(["Voltage (V)", "Current (A)", "Power (W)", "Magnetic (G)"]):
            # Category label
            cat_label = ctk.CTkLabel(
                stats_frame,
                text=category,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLORS["text"]
            )
            cat_label.grid(row=i*2, column=0, columnspan=3,
                           sticky="w", pady=(10, 5))

            # Stats row
            min_label = ctk.CTkLabel(
                stats_frame, text="Min:", text_color=COLORS["text_secondary"])
            min_label.grid(row=i*2+1, column=0, sticky="w", padx=(0, 10))

            avg_label = ctk.CTkLabel(
                stats_frame, text="Avg:", text_color=COLORS["text_secondary"])
            avg_label.grid(row=i*2+1, column=1, sticky="w", padx=10)

            max_label = ctk.CTkLabel(
                stats_frame, text="Max:", text_color=COLORS["text_secondary"])
            max_label.grid(row=i*2+1, column=2, sticky="w", padx=10)

            # Value labels
            stat_type = category.split()[0].lower()

            min_value = ctk.CTkLabel(
                stats_frame,
                text="0.0",
                font=ctk.CTkFont(weight="bold"),
                text_color=COLORS["text"]
            )
            min_value.grid(row=i*2+1, column=0, sticky="e", padx=(0, 10))
            setattr(self, f"{stat_type}_min_label", min_value)

            avg_value = ctk.CTkLabel(
                stats_frame,
                text="0.0",
                font=ctk.CTkFont(weight="bold"),
                text_color=COLORS["text"]
            )
            avg_value.grid(row=i*2+1, column=1, sticky="e", padx=10)
            setattr(self, f"{stat_type}_avg_label", avg_value)

            max_value = ctk.CTkLabel(
                stats_frame,
                text="0.0",
                font=ctk.CTkFont(weight="bold"),
                text_color=COLORS["text"]
            )
            max_value.grid(row=i*2+1, column=2, sticky="e", padx=10)
            setattr(self, f"{stat_type}_max_label", max_value)

        # Tamper events summary
        events_frame = ctk.CTkFrame(
            parent, fg_color=COLORS["card"], corner_radius=10)
        events_frame.pack(fill="x", padx=20, pady=(0, 20))

        events_title = ctk.CTkLabel(
            events_frame,
            text="Tamper Events Summary",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        )
        events_title.pack(pady=(10, 5))

        events_grid = ctk.CTkFrame(events_frame, fg_color="transparent")
        events_grid.pack(fill="x", padx=15, pady=(0, 10))

        # Normal events
        normal_label = ctk.CTkLabel(
            events_grid, text="Normal:", text_color=COLORS["text_secondary"])
        normal_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.normal_events_label = ctk.CTkLabel(
            events_grid,
            text="0",
            font=ctk.CTkFont(weight="bold"),
            text_color=COLORS["success"]
        )
        self.normal_events_label.grid(
            row=0, column=1, sticky="e", padx=5, pady=5)

        # Tamper events
        tamper_label = ctk.CTkLabel(
            events_grid, text="Tamper:", text_color=COLORS["text_secondary"])
        tamper_label.grid(row=0, column=2, sticky="w", padx=5, pady=5)

        self.tamper_events_label = ctk.CTkLabel(
            events_grid,
            text="0",
            font=ctk.CTkFont(weight="bold"),
            text_color=COLORS["danger"]
        )
        self.tamper_events_label.grid(
            row=0, column=3, sticky="e", padx=5, pady=5)

        # Total readings
        total_label = ctk.CTkLabel(
            events_grid, text="Total Readings:", text_color=COLORS["text_secondary"])
        total_label.grid(row=1, column=0, columnspan=2,
                         sticky="w", padx=5, pady=5)

        self.total_readings_label = ctk.CTkLabel(
            events_grid,
            text="0",
            font=ctk.CTkFont(weight="bold"),
            text_color=COLORS["text"]
        )
        self.total_readings_label.grid(
            row=1, column=2, columnspan=2, sticky="e", padx=5, pady=5)

    def create_stat_card(self, parent, label, key, unit=""):
        """Create a statistics card"""
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(fill="x", pady=8)

        label_widget = ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        label_widget.pack(side="left", padx=20, pady=15)

        value_label = ctk.CTkLabel(
            card,
            text="---",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        value_label.pack(side="right", padx=20, pady=15)

        self.stats_labels[key] = (value_label, unit)

    def update_readings(self, data=None):
        """Update all UI elements with new sensor data"""
        try:
            # If no data provided, read from serial reader
            if data is None:
                data = self.reader.read_sensor_data()

            if not data:
                return

            # Calculate power if not present
            if 'power' not in data:
                power = data['voltage'] * data['current']
            else:
                power = data['power']

            # Update current values
            self.current_voltage = data['voltage']
            self.current_current = data['current']
            self.current_power = power
            self.current_magnetic = data['magnetic_field']

            # Detect tamper events
            event_type, event_message, severity = self.detector.detect_tamper(
                data['voltage'], data['current'], data['magnetic_field'], power
            )

            self.current_event = event_message
            self.current_event_type = event_type

            # Update reading labels if they exist
            if hasattr(self, 'voltage_label'):
                self.voltage_label.configure(text=f"{data['voltage']:.2f}")
            if hasattr(self, 'current_label'):
                self.current_label.configure(text=f"{data['current']:.2f}")
            if hasattr(self, 'power_label'):
                self.power_label.configure(text=f"{power:.2f}")
            if hasattr(self, 'magnetic_label'):
                self.magnetic_label.configure(
                    text=f"{data['magnetic_field']:.2f}")

            # Update event status with color coding if it exists
            if hasattr(self, 'event_status_label'):
                color_map = {
                    "Normal": "#4CAF50",
                    "warning": "#FF9800",
                    "critical": "#f44336"
                }
                self.event_status_label.configure(
                    text=event_message,
                    text_color=color_map.get(severity, "#4CAF50")
                )

            # Add to data arrays for graphs
            self.voltage_data.append(data['voltage'])
            self.current_data.append(data['current'])
            self.power_data.append(power)
            self.magnetic_data.append(data['magnetic_field'])

            # Keep only last N points
            if len(self.voltage_data) > self.data_points:
                self.voltage_data.pop(0)
                self.current_data.pop(0)
                self.power_data.pop(0)
                self.magnetic_data.pop(0)

            # Log data
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.logger.log(
                timestamp, data['voltage'], data['current'],
                power, data['magnetic_field'],
                event_message, event_type
            )

            # Add to event log tree if it exists
            if hasattr(self, 'tree'):
                row_tags = (severity if event_type != "Normal" else 'normal',)
                self.tree.insert("", "end", values=(
                    timestamp,
                    f"{data['voltage']:.2f}",
                    f"{data['current']:.2f}",
                    f"{power:.2f}",
                    f"{data['magnetic_field']:.2f}",
                    event_message[:40] +
                    "..." if len(event_message) > 40 else event_message,
                    event_type
                ), tags=row_tags)

                # Scroll to bottom (if there are items)
                children = self.tree.get_children()
                if children:
                    self.tree.see(children[-1])

            if event_type != "Normal":
                self.add_event_to_log(event_message)

            # Update graphs
            if hasattr(self, 'update_graphs'):
                self.update_graphs()

            # Update statistics periodically (every 5 readings to avoid overhead)
            if len(self.voltage_data) % 5 == 0:
                self.update_statistics()

        except Exception as e:
            print(f"Error updating readings: {e}")

    def update_statistics(self):
        """Update statistics panel with both real-time and logged data"""
        # Calculate real-time stats from current data arrays
        if len(self.voltage_data) > 0:
            self.stats = {
                'voltage_min': min(self.voltage_data),
                'voltage_avg': sum(self.voltage_data) / len(self.voltage_data),
                'voltage_max': max(self.voltage_data),
                'current_min': min(self.current_data),
                'current_avg': sum(self.current_data) / len(self.current_data),
                'current_max': max(self.current_data),
                'power_min': min(self.power_data),
                'power_avg': sum(self.power_data) / len(self.power_data),
                'power_max': max(self.power_data),
                'magnetic_min': min(self.magnetic_data),
                'magnetic_avg': sum(self.magnetic_data) / len(self.magnetic_data),
                'magnetic_max': max(self.magnetic_data)
            }

        # Also get logged stats for comparison
        logged_stats = self.logger.get_statistics()
        detector_stats = self.detector.get_statistics()

        # Update stats UI labels if they exist
        if hasattr(self, 'stats_labels'):
            for key, (label, unit) in self.stats_labels.items():
                if key in self.stats:
                    value = self.stats[key]
                    if isinstance(value, float):
                        label.configure(text=f"{value:.2f} {unit}")
                    elif isinstance(value, int):
                        label.configure(text=f"{value} {unit}")
                    else:
                        label.configure(text=f"{value} {unit}")

        # Update event counts from logged stats
        if logged_stats:
            if 'normal_events' in logged_stats and hasattr(self, 'normal_events_label'):
                self.normal_events_label.configure(
                    text=str(logged_stats.get('normal_events', 0)))
            if 'tamper_events' in logged_stats and hasattr(self, 'tamper_events_label'):
                self.tamper_events_label.configure(
                    text=str(logged_stats.get('tamper_events', 0)))
            if 'total_readings' in logged_stats and hasattr(self, 'total_readings_label'):
                self.total_readings_label.configure(
                    text=str(logged_stats.get('total_readings', 0)))

        # Update event breakdown
        if logged_stats and 'event_types' in logged_stats and logged_stats['event_types']:
            breakdown_text = "\n".join(
                [f"{k}: {v} events" for k, v in logged_stats['event_types'].items()])
            if hasattr(self, 'event_breakdown_label'):
                self.event_breakdown_label.configure(text=breakdown_text)
        elif hasattr(self, 'event_breakdown_label'):
            self.event_breakdown_label.configure(text="No events recorded yet")

    def start_monitoring(self):
        """Start data monitoring"""
        if self.running:
            return

        self.running = True
        if hasattr(self, 'start_btn'):
            self.start_btn.configure(state="disabled")
        if hasattr(self, 'stop_btn'):
            self.stop_btn.configure(state="normal")
        self.status_indicator.configure(text_color="#4CAF50")
        self.status_label.configure(text="Monitoring...")

        def monitor_loop():
            # Try opening serial if not already open
            if not self.reader.mock_mode and (not self.reader.ser or not self.reader.ser.is_open):
                self.reader.open_port()
            while self.running:
                try:
                    data = self.reader.read_sensor_data()
                    if data:
                        self.root.after(0, self.update_readings, data)
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                time.sleep(0.5)

        self.update_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.update_thread.start()

    def stop_monitoring(self):
        """Stop data monitoring"""
        self.running = False
        if hasattr(self, 'start_btn'):
            self.start_btn.configure(state="normal")
        if hasattr(self, 'stop_btn'):
            self.stop_btn.configure(state="disabled")
        self.status_indicator.configure(text_color="gray")
        self.status_label.configure(text="Stopped")
        # Ensure previous thread exits before allowing a new start
        if hasattr(self, 'update_thread') and self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)

    def export_to_excel(self):
        """Export logged data to Excel"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if file_path:
                result = self.logger.export_to_excel(file_path)
                if result:
                    messagebox.showinfo(
                        "Success", f"Data exported to:\n{file_path}")
                else:
                    messagebox.showerror("Error", "Failed to export data")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    def run(self):
        """Start the application"""
        self.root.mainloop()
        self.running = False
        if self.reader:
            self.reader.close()
