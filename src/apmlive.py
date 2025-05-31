"""
APMLive - APM Calculator for Gamers
Version: 1.0.0
Developer: erace
License: MIT
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
    def __init__(self):
        self.actions = deque()
        self.current_apm = 0
        self.total_actions = 0
        self.session_start = time.time()
        self.running = False
        
        # Add for key tracking
        self.pressed_keys = set()
        
        # Configuration
        self.window_size = 60
        self.update_interval = 1
        
        # Graph data
        self.apm_history = deque(maxlen=60)  # Store last 60 seconds of APM
        self.time_history = deque(maxlen=60)  # Store timestamps
        
        # TXT export settings
        self.txt_settings = {
            'apm': True,
            'total_actions': True,
            'session_time': True,
            'avg_apm': False,
            'actions_per_second': False,
            'timestamp': False
        }
        
        # Use user data directory
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
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.txt_settings.update(saved_settings.get('txt_export', {}))
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings"""
        try:
            settings_data = {'txt_export': self.txt_settings}
            with open(self.settings_file, 'w') as f:
                json.dump(settings_data, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
        
    def setup_gui(self):
        """Create modern GUI"""
        self.root = tk.Tk()
        self.root.title("APMLive")
        self.root.geometry("600x800")  # Réduction de la hauteur de la fenêtre
        self.root.configure(bg='#121212')  # Fond sombre
        self.root.resizable(False, False)
        
        self.colors = {
            'bg_primary': '#121212',      # Fond principal sombre
            'bg_secondary': '#1E1E1E',    # Fond secondaire sombre
            'bg_tertiary': '#2D2D2D',     # Fond tertiaire sombre
            'accent': '#4285F4',          # Bleu techno sombre
            'success': '#00A67C',         # Vert APM sombre
            'danger': '#FF79B0',          # Rose punchy sombre
            'text_primary': '#F1F1F1',    # Texte principal sombre
            'text_secondary': '#AAAAAA',  # Texte secondaire sombre
            'border': '#333333'           # Bordure sombre
        }
        
        self.setup_styles()
        self.create_header()
        self.create_metrics_section()
        self.create_graph_section()
        self.create_stats_section()
        self.create_controls_section()
        self.create_footer()
        
    def setup_styles(self):
        """Configure modern styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Header.TLabel', 
                       font=('Roboto', 24, 'bold'),
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'])
        
        style.configure('Metric.TLabel',
                       font=('Roboto', 28, 'bold'),
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['accent'])
        
        style.configure('MetricTitle.TLabel',
                       font=('Roboto', 10, 'normal'),
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_secondary'])
        
        style.configure('Stat.TLabel',
                       font=('Roboto', 14, 'bold'),
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'])
        
        style.configure('StatTitle.TLabel',
                       font=('Roboto', 9, 'normal'),
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_secondary'])
        
        style.configure('Footer.TLabel',
                       font=('Roboto', 8, 'normal'),
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_secondary'])
    
    def create_header(self):
        """Create modern header"""
        header_frame = tk.Frame(self.root, bg=self.colors['bg_primary'], height=60)  # Réduction de la hauteur du header
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 0))  # Réduction du padding vertical
        header_frame.pack_propagate(False)
        
        # Container for title and buttons
        title_container = tk.Frame(header_frame, bg=self.colors['bg_primary'])
        title_container.pack(fill=tk.X, pady=(15, 5))
        
        # Main title
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
        
        # Subtitle
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
        """Open About window"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About - APMLive")
        about_window.geometry("400x300")
        about_window.configure(bg=self.colors['bg_primary'])
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Title
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
        
        # Information
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
        """Open settings window"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings - TXT Export")
        settings_window.geometry("450x550")
        settings_window.configure(bg=self.colors['bg_primary'])
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Title
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
        
        # Options container
        options_frame = tk.Frame(settings_window, bg=self.colors['bg_secondary'])
        options_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Variables for checkboxes
        self.setting_vars = {}
        
        # Available options
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
        
        # Buttons
        button_frame = tk.Frame(settings_window, bg=self.colors['bg_primary'])
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        def save_and_close():
            for key, var in self.setting_vars.items():
                self.txt_settings[key] = var.get()
            self.save_settings()
            settings_window.destroy()
        
        def cancel():
            settings_window.destroy()
        
        button_style = {
            'font': ('Roboto', 10, 'bold'),
            'relief': tk.FLAT,
            'bd': 0,
            'padx': 20,
            'pady': 10,
            'cursor': 'hand2'
        }
        
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              bg=self.colors['bg_tertiary'], 
                              fg=self.colors['text_primary'],
                              command=cancel,
                              **button_style)
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        save_btn = tk.Button(button_frame, text="Save", 
                            bg=self.colors['success'], 
                            fg='white',
                            command=save_and_close,
                            **button_style)
        save_btn.pack(side=tk.RIGHT)
    
    def create_metrics_section(self):
        """Create main metrics section"""
        metrics_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        metrics_frame.pack(fill=tk.X, padx=20, pady=10)  # Réduction du padding vertical
        
        # APM card
        apm_card = tk.Frame(metrics_frame, bg=self.colors['bg_secondary'], 
                           relief=tk.FLAT, bd=1)
        apm_card.pack(fill=tk.X, pady=(0, 10))  # Réduction du padding vertical
        
        border_frame = tk.Frame(apm_card, bg=self.colors['border'], height=1)
        border_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Label(apm_card, text="ACTIONS PER MINUTE", style='MetricTitle.TLabel').pack(pady=(10, 2))  # Réduction du padding vertical
        self.apm_label = ttk.Label(apm_card, text="0", style='Metric.TLabel')
        self.apm_label.pack(pady=(0, 10))  # Réduction du padding vertical
        
        # Stats cards in line
        stats_row = tk.Frame(metrics_frame, bg=self.colors['bg_primary'])
        stats_row.pack(fill=tk.X)
        
        # Total Actions card
        total_card = tk.Frame(stats_row, bg=self.colors['bg_tertiary'])
        total_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 7))
        
        ttk.Label(total_card, text="TOTAL", style='StatTitle.TLabel').pack(pady=(12, 2))
        self.total_label = ttk.Label(total_card, text="0", style='Stat.TLabel')
        self.total_label.pack(pady=(0, 12))
        
        # Session Time card
        time_card = tk.Frame(stats_row, bg=self.colors['bg_tertiary'])
        time_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(7, 0))
        
        ttk.Label(time_card, text="SESSION", style='StatTitle.TLabel').pack(pady=(12, 2))
        self.time_label = ttk.Label(time_card, text="00:00:00", style='Stat.TLabel')
        self.time_label.pack(pady=(0, 12))
    
    def create_graph_section(self):
        """Create real-time graph section"""
        graph_frame = tk.Frame(self.root, bg=self.colors['bg_secondary'])
        graph_frame.pack(fill=tk.X, padx=20, pady=(0, 10))  # Réduction du padding vertical
        
        # Title
        tk.Label(graph_frame, text="APM HISTORY", 
                bg=self.colors['bg_secondary'], 
                fg=self.colors['text_secondary'],
                font=('Roboto', 9, 'bold')).pack(pady=(15, 10))
        
        # Create matplotlib figure
        self.fig = plt.Figure(figsize=(8, 2.5), dpi=100)  # Réduction de la hauteur du graphique
        self.fig.patch.set_facecolor(self.colors['bg_secondary'])
        
        # Create subplot
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.colors['bg_secondary'])
        self.ax.tick_params(colors=self.colors['text_secondary'])
        self.ax.spines['bottom'].set_color(self.colors['border'])
        self.ax.spines['top'].set_color(self.colors['border'])
        self.ax.spines['left'].set_color(self.colors['border'])
        self.ax.spines['right'].set_color(self.colors['border'])
        
        # Create line plot
        self.line, = self.ax.plot([], [], color=self.colors['accent'], linewidth=2)
        
        # Configure axes
        self.ax.set_ylim(0, 100)  # Start with 0-100 APM range
        self.ax.set_xlim(0, 60)   # Show last 60 seconds
        self.ax.grid(True, color=self.colors['border'], linestyle='--', alpha=0.3)
        
        # Add labels
        self.ax.set_xlabel('Time (seconds)', color=self.colors['text_secondary'], fontsize=8)
        self.ax.set_ylabel('APM', color=self.colors['text_secondary'], fontsize=8)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
    
    def create_stats_section(self):
        """Create detailed stats section"""
        stats_frame = tk.Frame(self.root, bg=self.colors['bg_secondary'])
        stats_frame.pack(fill=tk.X, padx=20, pady=(0, 10))  # Réduction du padding vertical
        
        tk.Label(stats_frame, text="PERFORMANCE METRICS", 
                bg=self.colors['bg_secondary'], 
                fg=self.colors['text_secondary'],
                font=('Roboto', 9, 'bold')).pack(pady=(15, 10))
        
        grid_frame = tk.Frame(stats_frame, bg=self.colors['bg_secondary'])
        grid_frame.pack(padx=15, pady=(0, 15))
        
        # Average APM
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
        
        # Actions per second
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
        """Create controls section"""
        controls_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        controls_frame.pack(fill=tk.X, padx=20, pady=(0, 10))  # Réduction du padding vertical
        
        button_frame = tk.Frame(controls_frame, bg=self.colors['bg_primary'])
        button_frame.pack()
        
        button_style = {
            'font': ('Roboto', 11, 'bold'),
            'relief': tk.FLAT,
            'bd': 0,
            'padx': 25,
            'pady': 12,
            'cursor': 'hand2'
        }
        
        self.start_button = tk.Button(button_frame, text="START", 
                                     bg=self.colors['success'], 
                                     fg='white',
                                     activebackground='#00C896',
                                     command=self.start_recording,
                                     **button_style)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = tk.Button(button_frame, text="STOP", 
                                    bg=self.colors['danger'], 
                                    fg='white',
                                    activebackground='#FF4081',
                                    command=self.stop_recording,
                                    state='disabled',
                                    **button_style)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reset_button = tk.Button(button_frame, text="RESET", 
                                     bg=self.colors['bg_tertiary'], 
                                     fg=self.colors['text_primary'],
                                     activebackground=self.colors['border'],
                                     command=self.reset_data,
                                     **button_style)
        self.reset_button.pack(side=tk.LEFT)
    
    def create_footer(self):
        """Create footer"""
        footer_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=(0, 10))  # Réduction du padding vertical
        
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
        
        # Modify keyboard listener to handle press AND release
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
    
    def on_key_press(self, key):
        """Handle key press (count only once)"""
        if self.running:
            # Convert key to string for comparison
            key_str = str(key)
            
            # Only count if key wasn't already pressed
            if key_str not in self.pressed_keys:
                self.pressed_keys.add(key_str)
                self.on_action()
    
    def on_key_release(self, key):
        """Handle key release"""
        if self.running:
            key_str = str(key)
            # Remove key from pressed keys set
            self.pressed_keys.discard(key_str)
        
    def on_action(self, *args):
        """Record an action"""
        if self.running:
            current_time = time.time()
            self.actions.append(current_time)
            self.total_actions += 1
            
            while self.actions and current_time - self.actions[0] > self.window_size:
                self.actions.popleft()
    
    def calculate_apm(self):
        """Calculate current APM"""
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
        """Calculate session average APM"""
        session_duration = time.time() - self.session_start
        if session_duration > 0:
            return round((self.total_actions / session_duration) * 60, 1)
        return 0
    
    def calculate_aps(self):
        """Calculate actions per second"""
        if not self.actions:
            return 0
        
        current_time = time.time()
        recent_actions = len([action for action in self.actions 
                            if current_time - action <= 10])
        
        return round(recent_actions / 10, 1)
    
    def update_display(self):
        """Update display"""
        if self.running:
            self.current_apm = self.calculate_apm()
            avg_apm = self.calculate_average_apm()
            aps = self.calculate_aps()
            
            # Update labels
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
            
            # Update line data
            self.line.set_data(list(self.time_history), list(self.apm_history))
            
            # Adjust y-axis if needed
            max_apm = max(self.apm_history) if self.apm_history else 100
            y_max = max(100, (max_apm // 100 + 1) * 100)  # Round up to nearest 100
            self.ax.set_ylim(0, y_max)
            
            # Adjust x-axis to show last 60 seconds
            x_min = max(0, current_time - 60)
            self.ax.set_xlim(x_min, current_time)
            
            # Redraw canvas
            self.canvas.draw()
            
            self.write_to_files()
        
        self.root.after(self.update_interval * 1000, self.update_display)
    
    def write_to_files(self):
        """Write data to output files"""
        try:
            # Custom TXT export
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
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(txt_content))
            
            # Complete JSON export
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
        """Start recording"""
        if not self.running:
            self.running = True
            self.session_start = time.time()
            
            self.create_listeners()
            self.mouse_listener.start()
            self.keyboard_listener.start()
            
            self.start_button.config(state='disabled', bg=self.colors['bg_tertiary'])
            self.stop_button.config(state='normal', bg=self.colors['danger'])
            self.status_label.config(text="RECORDING", fg=self.colors['success'])
            self.status_dot.config(fg=self.colors['success'])
            
            print("Recording started...")
    
    def stop_recording(self):
        """Stop recording"""
        if self.running:
            self.running = False
            
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            
            self.start_button.config(state='normal', bg=self.colors['success'])
            self.stop_button.config(state='disabled', bg=self.colors['bg_tertiary'])
            self.status_label.config(text="OFFLINE", fg=self.colors['text_secondary'])
            self.status_dot.config(fg=self.colors['danger'])
            
            print("Recording stopped.")
    
    def reset_data(self):
        """Reset data"""
        self.actions.clear()
        self.total_actions = 0
        self.current_apm = 0
        self.session_start = time.time()
        
        # Clear pressed keys
        self.pressed_keys.clear()
        
        # Clear graph data
        self.apm_history.clear()
        self.time_history.clear()
        self.line.set_data([], [])
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, 60)
        self.canvas.draw()
        
        # Reset labels
        self.apm_label.config(text="0")
        self.total_label.config(text="0")
        self.avg_apm_label.config(text="0")
        self.aps_label.config(text="0.0")
        self.time_label.config(text="00:00:00")
        
        try:
            open(self.output_file, 'w').close()
            open(self.json_file, 'w').close()
        except:
            pass
        
        print("Data reset.")
    
    def run(self):
        """Run the application"""
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