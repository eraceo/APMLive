"""
APMLive - APM Calculator for Gamers
Version: 1.0.0
Developer: erace
License: MIT

This application provides real-time APM (Actions Per Minute) tracking for gamers.
It features a modern GUI with live metrics, performance graphs, and data export capabilities.
The application tracks both mouse and keyboard inputs to calculate accurate APM values.

Key Features:
- Real-time APM calculation with 60-second sliding window
- Live performance graph visualization
- Detailed performance metrics
- Data export to TXT and JSON formats
- Customizable export settings
- Modern dark theme UI
"""

import time
import threading
import json
from pynput import mouse, keyboard
from collections import deque
import tkinter as tk
from tkinter import ttk
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')

class APMCalculator:
    """
    Main application class for APM tracking and visualization.
    
    This class handles:
    - Input tracking (mouse and keyboard)
    - APM calculations
    - GUI management
    - Data persistence
    - Real-time updates
    """
    def __init__(self):
        # Core tracking data structures
        self.actions = deque()  # Stores timestamps of recent actions
        self.current_apm = 0    # Current APM value
        self.total_actions = 0  # Total actions in current session
        self.session_start = time.time()  # Session start timestamp
        self.running = False    # Tracking state
        
        # Keyboard state tracking
        self.pressed_keys = set()  # Currently pressed keys
        
        # Configuration parameters
        self.window_size = 60      # APM calculation window in seconds
        self.update_interval = 1   # UI update interval in seconds
        
        # Graph data storage
        self.apm_history = deque(maxlen=60)  # Last 60 seconds of APM values
        self.time_history = deque(maxlen=60)  # Corresponding timestamps
        
        # TXT export configuration
        self.txt_settings = {
            'apm': True,              # Current APM
            'total_actions': True,    # Total actions count
            'session_time': True,     # Session duration
            'avg_apm': False,         # Average APM
            'actions_per_second': False,  # Actions per second
            'timestamp': False        # Unix timestamp
        }
        
        # File paths for data persistence
        self.data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'APMLive')
        self.output_file = os.path.join(self.data_dir, "apm_data.txt")
        self.json_file = os.path.join(self.data_dir, "apm_data.json")
        self.settings_file = os.path.join(self.data_dir, "settings.json")
        
        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Load settings
        self.load_settings()
        
        # GUI setup
        self.setup_gui()
        
        # Start listeners
        self.start_listeners()
        
    def load_settings(self):
        """
        Load application settings from the settings file.
        Handles the configuration for data export options.
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.txt_settings.update(saved_settings.get('txt_export', {}))
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """
        Save current application settings to the settings file.
        Persists the data export configuration.
        """
        try:
            settings_data = {'txt_export': self.txt_settings}
            with open(self.settings_file, 'w') as f:
                json.dump(settings_data, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
        
    def setup_gui(self):
        """
        Initialize and configure the main application window.
        Sets up the dark theme and creates all UI components.
        """
        self.root = tk.Tk()
        self.root.title("APMLive")
        self.root.geometry("600x800")
        self.root.configure(bg='#121212')  # Dark background
        self.root.resizable(False, False)
        
        # Define color scheme for the application
        self.colors = {
            'bg_primary': '#121212',      # Main dark background
            'bg_secondary': '#1E1E1E',    # Secondary dark background
            'bg_tertiary': '#2D2D2D',     # Tertiary dark background
            'accent': '#4285F4',          # Dark tech blue
            'success': '#00A67C',         # Dark APM green
            'danger': '#FF79B0',          # Dark punchy pink
            'text_primary': '#F1F1F1',    # Main dark text
            'text_secondary': '#AAAAAA',  # Secondary dark text
            'border': '#333333'           # Dark border
        }
        
        self.setup_styles()
        self.create_header()
        self.create_metrics_section()
        self.create_graph_section()
        self.create_stats_section()
        self.create_controls_section()
        self.create_footer()
        
    def setup_styles(self):
        """
        Configure the visual styles for all UI components.
        Sets up fonts, colors, and other visual properties.
        """
        style = ttk.Style()
        style.theme_use('clam')
        
        # Header style
        style.configure('Header.TLabel', 
                       font=('Roboto', 24, 'bold'),
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'])
        
        # Main metric style
        style.configure('Metric.TLabel',
                       font=('Roboto', 28, 'bold'),
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['accent'])
        
        # Metric title style
        style.configure('MetricTitle.TLabel',
                       font=('Roboto', 10, 'normal'),
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_secondary'])
        
        # Stat value style
        style.configure('Stat.TLabel',
                       font=('Roboto', 14, 'bold'),
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'])
        
        # Stat title style
        style.configure('StatTitle.TLabel',
                       font=('Roboto', 9, 'normal'),
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_secondary'])
        
        # Footer style
        style.configure('Footer.TLabel',
                       font=('Roboto', 8, 'normal'),
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_secondary'])
    
    def create_header(self):
        """
        Create the application header with title and status indicators.
        Includes the app title, about button, settings button, and status display.
        """
        header_frame = tk.Frame(self.root, bg=self.colors['bg_primary'], height=60)
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 0))
        header_frame.pack_propagate(False)
        
        # Title container with buttons
        title_container = tk.Frame(header_frame, bg=self.colors['bg_primary'])
        title_container.pack(fill=tk.X, pady=(15, 5))
        
        title_label = ttk.Label(title_container, text="APM LIVE", style='Header.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # About button
        about_btn = tk.Button(title_container, text="ℹ", 
                            bg=self.colors['bg_tertiary'], 
                            fg=self.colors['text_primary'],
                            font=('Roboto', 16),
                            relief=tk.FLAT, bd=0,
                            padx=10, pady=5,
                            cursor='hand2',
                            command=self.open_about)
        about_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Settings button
        settings_btn = tk.Button(title_container, text="⚙", 
                               bg=self.colors['bg_tertiary'], 
                               fg=self.colors['text_primary'],
                               font=('Roboto', 16),
                               relief=tk.FLAT, bd=0,
                               padx=10, pady=5,
                               cursor='hand2',
                               command=self.open_settings)
        settings_btn.pack(side=tk.RIGHT)
        
        # Status display
        subtitle_frame = tk.Frame(header_frame, bg=self.colors['bg_primary'])
        subtitle_frame.pack()
        
        status_dot = tk.Label(subtitle_frame, text="●", 
                             bg=self.colors['bg_primary'], 
                             fg=self.colors['danger'], 
                             font=('Roboto', 12))
        status_dot.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(subtitle_frame, text="OFFLINE", 
                                   bg=self.colors['bg_primary'], 
                                   fg=self.colors['text_secondary'],
                                   font=('Roboto', 10, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.status_dot = status_dot
    
    def open_about(self):
        """
        Open the About window.
        Displays application information, version, and credits.
        """
        about_window = tk.Toplevel(self.root)
        about_window.title("About - APMLive")
        about_window.geometry("400x300")
        about_window.configure(bg=self.colors['bg_primary'])
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Title section
        title_frame = tk.Frame(about_window, bg=self.colors['bg_primary'])
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(title_frame, text="APMLive", 
                bg=self.colors['bg_primary'], 
                fg=self.colors['text_primary'],
                font=('Roboto', 24, 'bold')).pack()
        
        tk.Label(title_frame, text="Version 1.0.0", 
                bg=self.colors['bg_primary'], 
                fg=self.colors['text_secondary'],
                font=('Roboto', 12)).pack(pady=(5, 0))
        
        # Information section
        info_frame = tk.Frame(about_window, bg=self.colors['bg_secondary'])
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        info_text = """
Created by erace

A simple yet powerful APM calculator
for gamers who want to track their performance.

MIT License
© 2025 erace
        """
        
        tk.Label(info_frame, text=info_text,
                bg=self.colors['bg_secondary'],
                fg=self.colors['text_primary'],
                font=('Roboto', 10),
                justify=tk.CENTER).pack(pady=20)
        
        # Close button
        close_btn = tk.Button(about_window, text="Close",
                            bg=self.colors['bg_tertiary'],
                            fg=self.colors['text_primary'],
                            font=('Roboto', 10, 'bold'),
                            relief=tk.FLAT,
                            bd=0,
                            padx=20,
                            pady=10,
                            cursor='hand2',
                            command=about_window.destroy)
        close_btn.pack(pady=(0, 20))
    
    def open_settings(self):
        """
        Open the Settings window.
        Allows configuration of TXT export options.
        """
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings - TXT Export")
        settings_window.geometry("450x550")
        settings_window.configure(bg=self.colors['bg_primary'])
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Title section
        title_frame = tk.Frame(settings_window, bg=self.colors['bg_primary'])
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(title_frame, text="TXT Export Configuration", 
                bg=self.colors['bg_primary'], 
                fg=self.colors['text_primary'],
                font=('Roboto', 16, 'bold')).pack()
        
        tk.Label(title_frame, text="Choose which data to include in the TXT file", 
                bg=self.colors['bg_primary'], 
                fg=self.colors['text_secondary'],
                font=('Roboto', 9)).pack(pady=(5, 0))
        
        # Options section
        options_frame = tk.Frame(settings_window, bg=self.colors['bg_secondary'])
        options_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.setting_vars = {}
        
        # Define export options
        options = [
            ('apm', 'Current APM', 'Actions per minute in real-time'),
            ('total_actions', 'Total Actions', 'Total number of actions'),
            ('session_time', 'Session Time', 'Session duration'),
            ('avg_apm', 'Average APM', 'Average APM for the session'),
            ('actions_per_second', 'Actions/sec', 'Actions per second'),
            ('timestamp', 'Timestamp', 'Unix timestamp')
        ]
        
        tk.Label(options_frame, text="Export options:", 
                bg=self.colors['bg_secondary'], 
                fg=self.colors['text_primary'],
                font=('Roboto', 12, 'bold')).pack(pady=(15, 10), anchor='w', padx=15)
        
        # Create option checkboxes
        for key, title, desc in options:
            option_frame = tk.Frame(options_frame, bg=self.colors['bg_secondary'])
            option_frame.pack(fill=tk.X, padx=15, pady=5)
            
            var = tk.BooleanVar(value=self.txt_settings[key])
            self.setting_vars[key] = var
            
            checkbox = tk.Checkbutton(option_frame, 
                                    variable=var,
                                    bg=self.colors['bg_secondary'],
                                    fg=self.colors['text_primary'],
                                    selectcolor=self.colors['bg_tertiary'],
                                    activebackground=self.colors['bg_secondary'],
                                    font=('Roboto', 10, 'bold'))
            checkbox.pack(side=tk.LEFT)
            
            info_frame = tk.Frame(option_frame, bg=self.colors['bg_secondary'])
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
            
            tk.Label(info_frame, text=title, 
                    bg=self.colors['bg_secondary'], 
                    fg=self.colors['text_primary'],
                    font=('Roboto', 10, 'bold')).pack(anchor='w')
            
            tk.Label(info_frame, text=desc, 
                    bg=self.colors['bg_secondary'], 
                    fg=self.colors['text_secondary'],
                    font=('Roboto', 8)).pack(anchor='w')
        
        # Button section
        button_frame = tk.Frame(settings_window, bg=self.colors['bg_primary'])
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        def save_and_close():
            """Save settings and close the window"""
            for key, var in self.setting_vars.items():
                self.txt_settings[key] = var.get()
            self.save_settings()
            settings_window.destroy()
        
        def cancel():
            """Close the window without saving"""
            settings_window.destroy()
        
        # Common button style
        button_style = {
            'font': ('Roboto', 10, 'bold'),
            'relief': tk.FLAT,
            'bd': 0,
            'padx': 20,
            'pady': 10,
            'cursor': 'hand2'
        }
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              bg=self.colors['bg_tertiary'], 
                              fg=self.colors['text_primary'],
                              command=cancel,
                              **button_style)
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Save button
        save_btn = tk.Button(button_frame, text="Save", 
                            bg=self.colors['success'], 
                            fg='white',
                            command=save_and_close,
                            **button_style)
        save_btn.pack(side=tk.RIGHT)
    
    def create_metrics_section(self):
        """
        Create the main metrics display section.
        Shows current APM, total actions, and session time.
        """
        metrics_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        metrics_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # APM display card
        apm_card = tk.Frame(metrics_frame, bg=self.colors['bg_secondary'], 
                           relief=tk.FLAT, bd=1)
        apm_card.pack(fill=tk.X, pady=(0, 10))
        
        border_frame = tk.Frame(apm_card, bg=self.colors['border'], height=1)
        border_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Label(apm_card, text="ACTIONS PER MINUTE", style='MetricTitle.TLabel').pack(pady=(10, 2))
        self.apm_label = ttk.Label(apm_card, text="0", style='Metric.TLabel')
        self.apm_label.pack(pady=(0, 10))
        
        # Stats row with total actions and session time
        stats_row = tk.Frame(metrics_frame, bg=self.colors['bg_primary'])
        stats_row.pack(fill=tk.X)
        
        # Total actions card
        total_card = tk.Frame(stats_row, bg=self.colors['bg_tertiary'])
        total_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 7))
        
        ttk.Label(total_card, text="TOTAL", style='StatTitle.TLabel').pack(pady=(12, 2))
        self.total_label = ttk.Label(total_card, text="0", style='Stat.TLabel')
        self.total_label.pack(pady=(0, 12))
        
        # Session time card
        time_card = tk.Frame(stats_row, bg=self.colors['bg_tertiary'])
        time_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(7, 0))
        
        ttk.Label(time_card, text="SESSION", style='StatTitle.TLabel').pack(pady=(12, 2))
        self.time_label = ttk.Label(time_card, text="00:00:00", style='Stat.TLabel')
        self.time_label.pack(pady=(0, 12))
    
    def create_graph_section(self):
        """
        Create the real-time APM graph section.
        Sets up matplotlib figure and canvas for live updates.
        """
        graph_frame = tk.Frame(self.root, bg=self.colors['bg_secondary'])
        graph_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        tk.Label(graph_frame, text="APM HISTORY", 
                bg=self.colors['bg_secondary'], 
                fg=self.colors['text_secondary'],
                font=('Roboto', 9, 'bold')).pack(pady=(15, 10))
        
        # Create matplotlib figure
        self.fig = plt.Figure(figsize=(8, 2.5), dpi=100)
        self.fig.patch.set_facecolor(self.colors['bg_secondary'])
        
        # Configure plot
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.colors['bg_secondary'])
        self.ax.tick_params(colors=self.colors['text_secondary'])
        self.ax.spines['bottom'].set_color(self.colors['border'])
        self.ax.spines['top'].set_color(self.colors['border'])
        self.ax.spines['left'].set_color(self.colors['border'])
        self.ax.spines['right'].set_color(self.colors['border'])
        
        # Create line plot
        self.line, = self.ax.plot([], [], color=self.colors['accent'], linewidth=2)
        
        # Set initial plot limits
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, 60)
        self.ax.grid(True, color=self.colors['border'], linestyle='--', alpha=0.3)
        
        # Configure axis labels
        self.ax.set_xlabel('Time (seconds)', color=self.colors['text_secondary'], fontsize=8)
        self.ax.set_ylabel('APM', color=self.colors['text_secondary'], fontsize=8)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
    
    def create_stats_section(self):
        """
        Create the detailed performance metrics section.
        Shows average APM and actions per second.
        """
        stats_frame = tk.Frame(self.root, bg=self.colors['bg_secondary'])
        stats_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        tk.Label(stats_frame, text="PERFORMANCE METRICS", 
                bg=self.colors['bg_secondary'], 
                fg=self.colors['text_secondary'],
                font=('Roboto', 9, 'bold')).pack(pady=(15, 10))
        
        grid_frame = tk.Frame(stats_frame, bg=self.colors['bg_secondary'])
        grid_frame.pack(padx=15, pady=(0, 15))
        
        # Average APM display
        avg_frame = tk.Frame(grid_frame, bg=self.colors['bg_secondary'])
        avg_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(avg_frame, text="Avg APM:", 
                bg=self.colors['bg_secondary'], 
                fg=self.colors['text_secondary'],
                font=('Roboto', 10)).pack(side=tk.LEFT)
        
        self.avg_apm_label = tk.Label(avg_frame, text="0", 
                                     bg=self.colors['bg_secondary'], 
                                     fg=self.colors['text_primary'],
                                     font=('Roboto', 10, 'bold'))
        self.avg_apm_label.pack(side=tk.RIGHT)
        
        # Actions per second display
        aps_frame = tk.Frame(grid_frame, bg=self.colors['bg_secondary'])
        aps_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(aps_frame, text="Actions/sec:", 
                bg=self.colors['bg_secondary'], 
                fg=self.colors['text_secondary'],
                font=('Roboto', 10)).pack(side=tk.LEFT)
        
        self.aps_label = tk.Label(aps_frame, text="0.0", 
                                 bg=self.colors['bg_secondary'], 
                                 fg=self.colors['text_primary'],
                                 font=('Roboto', 10, 'bold'))
        self.aps_label.pack(side=tk.RIGHT)
    
    def create_controls_section(self):
        """
        Create the control buttons section.
        Includes Start, Stop, and Reset buttons.
        """
        controls_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        controls_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        button_frame = tk.Frame(controls_frame, bg=self.colors['bg_primary'])
        button_frame.pack()
        
        # Common button style
        button_style = {
            'font': ('Roboto', 11, 'bold'),
            'relief': tk.FLAT,
            'bd': 0,
            'padx': 25,
            'pady': 12,
            'cursor': 'hand2'
        }
        
        # Start button
        self.start_button = tk.Button(button_frame, text="START", 
                                     bg=self.colors['success'], 
                                     fg='white',
                                     activebackground='#00C896',
                                     command=self.start_recording,
                                     **button_style)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop button
        self.stop_button = tk.Button(button_frame, text="STOP", 
                                    bg=self.colors['danger'], 
                                    fg='white',
                                    activebackground='#FF4081',
                                    command=self.stop_recording,
                                    state='disabled',
                                    **button_style)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Reset button
        self.reset_button = tk.Button(button_frame, text="RESET", 
                                     bg=self.colors['bg_tertiary'], 
                                     fg=self.colors['text_primary'],
                                     activebackground=self.colors['border'],
                                     command=self.reset_data,
                                     **button_style)
        self.reset_button.pack(side=tk.LEFT)
    
    def create_footer(self):
        """
        Create the application footer.
        Shows data directory location and calculation information.
        """
        footer_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=(0, 10))
        
        ttk.Label(footer_frame, 
                 text=f"Data saved in {self.data_dir}", 
                 style='Footer.TLabel').pack()
        
        ttk.Label(footer_frame, 
                 text="Calculation based on a 60-second sliding window", 
                 style='Footer.TLabel').pack()
    
    def start_listeners(self):
        """Initialize mouse and keyboard listeners"""
        self.mouse_listener = None
        self.keyboard_listener = None
        
    def create_listeners(self):
        """Create new listeners"""
        self.mouse_listener = mouse.Listener(
            on_click=lambda x, y, button, pressed: self.on_action() if pressed else None,
            on_scroll=self.on_action
        )
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
    
    def on_key_press(self, key):
        """
        Handle keyboard key press events.
        Only counts each key once until it's released.
        
        Args:
            key: The key that was pressed
        """
        if self.running:
            key_str = str(key)
            
            if key_str not in self.pressed_keys:
                self.pressed_keys.add(key_str)
                self.on_action()
    
    def on_key_release(self, key):
        """
        Handle keyboard key release events.
        Removes the key from the pressed keys set.
        
        Args:
            key: The key that was released
        """
        if self.running:
            key_str = str(key)
            self.pressed_keys.discard(key_str)
        
    def on_action(self, *args):
        """
        Record a user action (mouse click, scroll, or key press).
        Updates the action queue and total count.
        """
        if self.running:
            current_time = time.time()
            self.actions.append(current_time)
            self.total_actions += 1
            
            while self.actions and current_time - self.actions[0] > self.window_size:
                self.actions.popleft()
    
    def calculate_apm(self):
        """
        Calculate the current APM based on recent actions.
        
        Returns:
            float: The current APM value rounded to 1 decimal place
        """
        if not self.actions:
            return 0
        
        current_time = time.time()
        recent_actions = len([action for action in self.actions 
                            if current_time - action <= self.window_size])
        
        time_window = min(self.window_size, current_time - self.session_start)
        if time_window > 0:
            apm = (recent_actions / time_window) * 60
        else:
            apm = 0
            
        return round(apm, 1)
    
    def calculate_average_apm(self):
        """
        Calculate the average APM for the entire session.
        
        Returns:
            float: The average APM value rounded to 1 decimal place
        """
        session_duration = time.time() - self.session_start
        if session_duration > 0:
            return round((self.total_actions / session_duration) * 60, 1)
        return 0
    
    def calculate_aps(self):
        """
        Calculate the current actions per second based on the last 10 seconds.
        
        Returns:
            float: The current actions per second value rounded to 1 decimal place
        """
        if not self.actions:
            return 0
        
        current_time = time.time()
        recent_actions = len([action for action in self.actions 
                            if current_time - action <= 10])
        
        return round(recent_actions / 10, 1)
    
    def update_display(self):
        """
        Update the GUI with current metrics and graph data.
        This method is called periodically to refresh the display.
        """
        if self.running:
            self.current_apm = self.calculate_apm()
            avg_apm = self.calculate_average_apm()
            aps = self.calculate_aps()
            
            # Update metric labels
            self.apm_label.config(text=str(int(self.current_apm)))
            self.total_label.config(text=str(self.total_actions))
            self.avg_apm_label.config(text=str(int(avg_apm)))
            self.aps_label.config(text=str(aps))
            
            # Update session time
            session_time = int(time.time() - self.session_start)
            hours = session_time // 3600
            minutes = (session_time % 3600) // 60
            seconds = session_time % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.time_label.config(text=time_str)
            
            # Update graph
            current_time = time.time() - self.session_start
            self.apm_history.append(self.current_apm)
            self.time_history.append(current_time)
            
            self.line.set_data(list(self.time_history), list(self.apm_history))
            
            # Adjust graph scale
            max_apm = max(self.apm_history) if self.apm_history else 100
            y_max = max(100, (max_apm // 100 + 1) * 100)
            self.ax.set_ylim(0, y_max)
            
            x_min = max(0, current_time - 60)
            self.ax.set_xlim(x_min, current_time)
            
            self.canvas.draw()
            
            # Export data
            self.write_to_files()
        
        # Schedule next update
        self.root.after(self.update_interval * 1000, self.update_display)
    
    def write_to_files(self):
        """
        Write current metrics to TXT and JSON files.
        Handles data export based on user configuration.
        """
        try:
            # Prepare TXT content
            txt_content = []
            if self.txt_settings['apm']:
                txt_content.append(f"APM: {self.current_apm}")
            if self.txt_settings['total_actions']:
                txt_content.append(f"Total: {self.total_actions}")
            if self.txt_settings['session_time']:
                session_time = int(time.time() - self.session_start)
                txt_content.append(f"Session: {session_time}s")
            if self.txt_settings['avg_apm']:
                txt_content.append(f"Avg APM: {self.calculate_average_apm()}")
            if self.txt_settings['actions_per_second']:
                txt_content.append(f"Actions/sec: {self.calculate_aps()}")
            if self.txt_settings['timestamp']:
                txt_content.append(f"Timestamp: {int(time.time())}")
            
            # Write TXT file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(txt_content))
            
            # Prepare and write JSON data
            data = {
                "apm": self.current_apm,
                "total_actions": self.total_actions,
                "average_apm": self.calculate_average_apm(),
                "actions_per_second": self.calculate_aps(),
                "session_duration": int(time.time() - self.session_start),
                "timestamp": time.time()
            }
            
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error writing to files: {e}")
    
    def start_recording(self):
        """
        Start tracking user actions.
        Initializes input listeners and updates UI state.
        """
        if not self.running:
            self.running = True
            self.session_start = time.time()
            
            self.create_listeners()
            self.mouse_listener.start()
            self.keyboard_listener.start()
            
            # Update UI state
            self.start_button.config(state='disabled', bg=self.colors['bg_tertiary'])
            self.stop_button.config(state='normal', bg=self.colors['danger'])
            self.status_label.config(text="RECORDING", fg=self.colors['success'])
            self.status_dot.config(fg=self.colors['success'])
            
            print("Recording started...")
    
    def stop_recording(self):
        """
        Stop tracking user actions.
        Stops input listeners and updates UI state.
        """
        if self.running:
            self.running = False
            
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            
            # Update UI state
            self.start_button.config(state='normal', bg=self.colors['success'])
            self.stop_button.config(state='disabled', bg=self.colors['bg_tertiary'])
            self.status_label.config(text="OFFLINE", fg=self.colors['text_secondary'])
            self.status_dot.config(fg=self.colors['danger'])
            
            print("Recording stopped.")
    
    def reset_data(self):
        """
        Reset all tracking data and UI elements.
        Clears action history and resets counters.
        """
        # Clear tracking data
        self.actions.clear()
        self.total_actions = 0
        self.current_apm = 0
        self.session_start = time.time()
        
        # Clear keyboard state
        self.pressed_keys.clear()
        
        # Reset graph
        self.apm_history.clear()
        self.time_history.clear()
        self.line.set_data([], [])
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, 60)
        self.canvas.draw()
        
        # Reset UI elements
        self.apm_label.config(text="0")
        self.total_label.config(text="0")
        self.avg_apm_label.config(text="0")
        self.aps_label.config(text="0.0")
        self.time_label.config(text="00:00:00")
        
        # Clear output files
        try:
            open(self.output_file, 'w').close()
            open(self.json_file, 'w').close()
        except:
            pass
        
        print("Data reset.")
    
    def run(self):
        """
        Start the application main loop.
        Handles the main application lifecycle.
        """
        self.update_display()
        
        try:
            self.root.mainloop()
        finally:
            if self.running:
                self.stop_recording()

if __name__ == "__main__":
    try:
        import pynput
    except ImportError:
        print("Installing pynput...")
        os.system("pip install pynput")
        import pynput
    
    print("Starting APMLive...")
    print("Interface loaded - Data exported to apm_data.txt")
    
    app = APMCalculator()
    app.run()