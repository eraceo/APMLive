import time
import threading
import json
from pynput import mouse, keyboard
from collections import deque
import tkinter as tk
from tkinter import ttk
import os

class APMCalculator:
    def __init__(self):
        self.actions = deque()
        self.current_apm = 0
        self.total_actions = 0
        self.session_start = time.time()
        self.running = False
        
        # Configuration
        self.window_size = 60
        self.update_interval = 1
        
        # Utiliser le dossier de données utilisateur
        self.data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'APMLive')
        self.output_file = os.path.join(self.data_dir, "apm_data.txt")
        self.json_file = os.path.join(self.data_dir, "apm_data.json")
        
        # Créer le dossier de données s'il n'existe pas
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Interface graphique
        self.setup_gui()
        
        # Démarrage des listeners
        self.start_listeners()
        
    def setup_gui(self):
        """Créer l'interface graphique moderne"""
        self.root = tk.Tk()
        self.root.title("APMLive")
        self.root.geometry("400x500")
        self.root.configure(bg='#0d1117')
        self.root.resizable(False, False)
        
        # Configuration des couleurs modernes
        self.colors = {
            'bg_primary': '#0d1117',
            'bg_secondary': '#161b22',
            'bg_tertiary': '#21262d',
            'accent': '#58a6ff',
            'accent_hover': '#1f6feb',
            'success': '#238636',
            'danger': '#da3633',
            'text_primary': '#f0f6fc',
            'text_secondary': '#7d8590',
            'border': '#30363d'
        }
        
        # Configuration du style
        self.setup_styles()
        
        # Header avec gradient simulé
        self.create_header()
        
        # Section des métriques principales
        self.create_metrics_section()
        
        # Section des statistiques détaillées
        self.create_stats_section()
        
        # Section des contrôles
        self.create_controls_section()
        
        # Footer avec informations
        self.create_footer()
        
    def setup_styles(self):
        """Configuration des styles modernes"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Styles pour les labels
        style.configure('Header.TLabel', 
                       font=('Helvetica', 24, 'bold'),
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'])
        
        style.configure('Metric.TLabel',
                       font=('Helvetica', 28, 'bold'),
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['accent'])
        
        style.configure('MetricTitle.TLabel',
                       font=('Helvetica', 10, 'normal'),
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_secondary'])
        
        style.configure('Stat.TLabel',
                       font=('Helvetica', 14, 'bold'),
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'])
        
        style.configure('StatTitle.TLabel',
                       font=('Helvetica', 9, 'normal'),
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_secondary'])
        
        style.configure('Footer.TLabel',
                       font=('Helvetica', 8, 'normal'),
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_secondary'])
    
    def create_header(self):
        """Créer le header moderne"""
        header_frame = tk.Frame(self.root, bg=self.colors['bg_primary'], height=80)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        # Titre principal
        title_label = ttk.Label(header_frame, text="APM LIVE", style='Header.TLabel')
        title_label.pack(pady=(15, 5))
        
        # Sous-titre
        subtitle_frame = tk.Frame(header_frame, bg=self.colors['bg_primary'])
        subtitle_frame.pack()
        
        status_dot = tk.Label(subtitle_frame, text="●", 
                             bg=self.colors['bg_primary'], 
                             fg=self.colors['danger'], 
                             font=('Helvetica', 12))
        status_dot.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(subtitle_frame, text="OFFLINE", 
                                   bg=self.colors['bg_primary'], 
                                   fg=self.colors['text_secondary'],
                                   font=('Helvetica', 10, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.status_dot = status_dot
    
    def create_metrics_section(self):
        """Créer la section des métriques principales"""
        metrics_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        metrics_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Carte APM
        apm_card = tk.Frame(metrics_frame, bg=self.colors['bg_secondary'], 
                           relief=tk.FLAT, bd=1)
        apm_card.pack(fill=tk.X, pady=(0, 15))
        
        # Effet de bordure
        border_frame = tk.Frame(apm_card, bg=self.colors['border'], height=1)
        border_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Label(apm_card, text="ACTIONS PER MINUTE", style='MetricTitle.TLabel').pack(pady=(15, 5))
        self.apm_label = ttk.Label(apm_card, text="0", style='Metric.TLabel')
        self.apm_label.pack(pady=(0, 15))
        
        # Cartes des statistiques en ligne
        stats_row = tk.Frame(metrics_frame, bg=self.colors['bg_primary'])
        stats_row.pack(fill=tk.X)
        
        # Carte Total Actions
        total_card = tk.Frame(stats_row, bg=self.colors['bg_tertiary'])
        total_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 7))
        
        ttk.Label(total_card, text="TOTAL", style='StatTitle.TLabel').pack(pady=(12, 2))
        self.total_label = ttk.Label(total_card, text="0", style='Stat.TLabel')
        self.total_label.pack(pady=(0, 12))
        
        # Carte Session Time
        time_card = tk.Frame(stats_row, bg=self.colors['bg_tertiary'])
        time_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(7, 0))
        
        ttk.Label(time_card, text="SESSION", style='StatTitle.TLabel').pack(pady=(12, 2))
        self.time_label = ttk.Label(time_card, text="00:00:00", style='Stat.TLabel')
        self.time_label.pack(pady=(0, 12))
    
    def create_stats_section(self):
        """Créer la section des statistiques détaillées"""
        stats_frame = tk.Frame(self.root, bg=self.colors['bg_secondary'])
        stats_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Titre de section
        tk.Label(stats_frame, text="PERFORMANCE METRICS", 
                bg=self.colors['bg_secondary'], 
                fg=self.colors['text_secondary'],
                font=('Helvetica', 9, 'bold')).pack(pady=(15, 10))
        
        # Grille de statistiques
        grid_frame = tk.Frame(stats_frame, bg=self.colors['bg_secondary'])
        grid_frame.pack(padx=15, pady=(0, 15))
        
        # APM Moyen
        avg_frame = tk.Frame(grid_frame, bg=self.colors['bg_secondary'])
        avg_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(avg_frame, text="Avg APM:", 
                bg=self.colors['bg_secondary'], 
                fg=self.colors['text_secondary'],
                font=('Helvetica', 10)).pack(side=tk.LEFT)
        
        self.avg_apm_label = tk.Label(avg_frame, text="0", 
                                     bg=self.colors['bg_secondary'], 
                                     fg=self.colors['text_primary'],
                                     font=('Helvetica', 10, 'bold'))
        self.avg_apm_label.pack(side=tk.RIGHT)
        
        # Actions/sec
        aps_frame = tk.Frame(grid_frame, bg=self.colors['bg_secondary'])
        aps_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(aps_frame, text="Actions/sec:", 
                bg=self.colors['bg_secondary'], 
                fg=self.colors['text_secondary'],
                font=('Helvetica', 10)).pack(side=tk.LEFT)
        
        self.aps_label = tk.Label(aps_frame, text="0.0", 
                                 bg=self.colors['bg_secondary'], 
                                 fg=self.colors['text_primary'],
                                 font=('Helvetica', 10, 'bold'))
        self.aps_label.pack(side=tk.RIGHT)
    
    def create_controls_section(self):
        """Créer la section des contrôles"""
        controls_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        controls_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Boutons modernes
        button_frame = tk.Frame(controls_frame, bg=self.colors['bg_primary'])
        button_frame.pack()
        
        # Style des boutons
        button_style = {
            'font': ('Helvetica', 11, 'bold'),
            'relief': tk.FLAT,
            'bd': 0,
            'padx': 25,
            'pady': 12,
            'cursor': 'hand2'
        }
        
        # Bouton Start
        self.start_button = tk.Button(button_frame, text="START", 
                                     bg=self.colors['success'], 
                                     fg='white',
                                     activebackground='#2ea043',
                                     command=self.start_recording,
                                     **button_style)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Bouton Stop
        self.stop_button = tk.Button(button_frame, text="STOP", 
                                    bg=self.colors['danger'], 
                                    fg='white',
                                    activebackground='#f85149',
                                    command=self.stop_recording,
                                    state='disabled',
                                    **button_style)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Bouton Reset
        self.reset_button = tk.Button(button_frame, text="RESET", 
                                     bg=self.colors['bg_tertiary'], 
                                     fg=self.colors['text_primary'],
                                     activebackground=self.colors['border'],
                                     command=self.reset_data,
                                     **button_style)
        self.reset_button.pack(side=tk.LEFT)
    
    def create_footer(self):
        """Créer le footer"""
        footer_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=(0, 15))
        
        ttk.Label(footer_frame, 
                 text=f"Données sauvegardées dans {self.data_dir}", 
                 style='Footer.TLabel').pack()
        
        ttk.Label(footer_frame, 
                 text="Calcul basé sur une fenêtre glissante de 60 secondes", 
                 style='Footer.TLabel').pack()
        
    def start_listeners(self):
        """Initialiser les listeners pour souris et clavier"""
        self.mouse_listener = None
        self.keyboard_listener = None
        
    def create_listeners(self):
        """Créer de nouveaux listeners"""
        self.mouse_listener = mouse.Listener(
            on_click=self.on_action,
            on_scroll=self.on_action
        )
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_action,
            on_release=None
        )
        
    def on_action(self, *args):
        """Enregistrer une action"""
        if self.running:
            current_time = time.time()
            self.actions.append(current_time)
            self.total_actions += 1
            
            while self.actions and current_time - self.actions[0] > self.window_size:
                self.actions.popleft()
    
    def calculate_apm(self):
        """Calculer les APM actuels"""
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
        """Calculer l'APM moyen de la session"""
        session_duration = time.time() - self.session_start
        if session_duration > 0:
            return round((self.total_actions / session_duration) * 60, 1)
        return 0
    
    def calculate_aps(self):
        """Calculer les actions par seconde"""
        if not self.actions:
            return 0
        
        current_time = time.time()
        recent_actions = len([action for action in self.actions 
                            if current_time - action <= 10])  # 10 secondes
        
        return round(recent_actions / 10, 1)
    
    def update_display(self):
        """Mettre à jour l'affichage"""
        if self.running:
            self.current_apm = self.calculate_apm()
            avg_apm = self.calculate_average_apm()
            aps = self.calculate_aps()
            
            # Mettre à jour les métriques principales
            self.apm_label.config(text=str(int(self.current_apm)))
            self.total_label.config(text=str(self.total_actions))
            
            # Mettre à jour les stats détaillées
            self.avg_apm_label.config(text=str(int(avg_apm)))
            self.aps_label.config(text=str(aps))
            
            # Temps de session
            session_time = int(time.time() - self.session_start)
            hours = session_time // 3600
            minutes = (session_time % 3600) // 60
            seconds = session_time % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.time_label.config(text=time_str)
            
            # Écrire dans les fichiers
            self.write_to_files()
        
        self.root.after(self.update_interval * 1000, self.update_display)
    
    def write_to_files(self):
        """Écrire les données dans les fichiers de sortie"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(f"APM: {self.current_apm}\n")
                f.write(f"Total: {self.total_actions}\n")
                f.write(f"Session: {int(time.time() - self.session_start)}s")
            
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
            print(f"Erreur lors de l'écriture: {e}")
    
    def start_recording(self):
        """Démarrer l'enregistrement"""
        if not self.running:
            self.running = True
            self.session_start = time.time()
            
            # Créer de nouveaux listeners à chaque démarrage
            self.create_listeners()
            self.mouse_listener.start()
            self.keyboard_listener.start()
            
            # Mise à jour de l'interface
            self.start_button.config(state='disabled', bg=self.colors['bg_tertiary'])
            self.stop_button.config(state='normal', bg=self.colors['danger'])
            self.status_label.config(text="RECORDING", fg=self.colors['success'])
            self.status_dot.config(fg=self.colors['success'])
            
            print("Enregistrement démarré...")
    
    def stop_recording(self):
        """Arrêter l'enregistrement"""
        if self.running:
            self.running = False
            
            # Arrêter les listeners s'ils existent
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            
            # Mise à jour de l'interface
            self.start_button.config(state='normal', bg=self.colors['success'])
            self.stop_button.config(state='disabled', bg=self.colors['bg_tertiary'])
            self.status_label.config(text="OFFLINE", fg=self.colors['text_secondary'])
            self.status_dot.config(fg=self.colors['danger'])
            
            print("Enregistrement arrêté.")
    
    def reset_data(self):
        """Réinitialiser les données"""
        self.actions.clear()
        self.total_actions = 0
        self.current_apm = 0
        self.session_start = time.time()
        
        # Mise à jour de l'affichage
        self.apm_label.config(text="0")
        self.total_label.config(text="0")
        self.avg_apm_label.config(text="0")
        self.aps_label.config(text="0.0")
        self.time_label.config(text="00:00:00")
        
        # Nettoyer les fichiers
        try:
            open(self.output_file, 'w').close()
            open(self.json_file, 'w').close()
        except:
            pass
        
        print("Données réinitialisées.")
    
    def run(self):
        """Lancer l'application"""
        self.update_display()
        
        try:
            self.root.mainloop()
        finally:
            # Nettoyer à la fermeture
            if self.running:
                self.stop_recording()

if __name__ == "__main__":
    try:
        import pynput
    except ImportError:
        print("Installation de pynput...")
        os.system("pip install pynput")
        import pynput
    
    print("Démarrage du calculateur APM Pro...")
    print("Interface moderne chargée - Données exportées vers apm_data.txt")
    
    app = APMCalculator()
    app.run()