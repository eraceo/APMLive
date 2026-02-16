"""
Main Window Module
Handles the main GUI logic and user interaction.
"""

import tkinter as tk
import logging
from tkinter import ttk
from typing import Dict, Any

from src.utils.config import AppColors, AppFonts
from src.core.exporter import DataExporter
from src.ui.settings_window import SettingsWindow
from src.core.calculator import APMCalculator
from src.ui.graph_widget import GraphWidget

logger = logging.getLogger("APMLive.UI")


class MainWindow:
    """
    Main application window.
    Coordinates between the UI, the Calculator, and the Exporter.
    """

    def __init__(self, root: tk.Tk, calculator: APMCalculator) -> None:
        self.root = root
        self.calculator = calculator
        self.exporter = DataExporter()

        # Register Observers
        self.calculator.add_observer(self.on_metrics_update)
        self.calculator.add_observer(self.exporter.export)

        # Window Setup
        self.root.title("APMLive")
        self.root.geometry("600x800")
        self.root.configure(bg=AppColors.BG_PRIMARY)
        self.root.resizable(False, False)

        # Center window
        self._center_window()

        # UI Components
        self._setup_styles()
        self._create_header()
        self._create_metrics()
        self._create_graph()
        self._create_controls()

        self.running: bool = False

    def _center_window(self) -> None:
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 800) // 2
        self.root.geometry(f"600x800+{x}+{y}")

    def _setup_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Header.TLabel",
            font=AppFonts.HEADER,
            background=AppColors.BG_PRIMARY,
            foreground=AppColors.TEXT_PRIMARY,
        )

        style.configure(
            "Metric.TLabel",
            font=AppFonts.METRIC_LARGE,
            background=AppColors.BG_SECONDARY,
            foreground=AppColors.ACCENT,
        )

        style.configure(
            "Stat.TLabel",
            font=AppFonts.STAT_VALUE,
            background=AppColors.BG_TERTIARY,
            foreground=AppColors.TEXT_PRIMARY,
        )

    def _create_header(self) -> None:
        header_frame = tk.Frame(self.root, bg=AppColors.BG_PRIMARY, height=60)
        header_frame.pack(fill=tk.X, padx=20, pady=(10, 0))

        title_label = ttk.Label(header_frame, text="APM LIVE", style="Header.TLabel")
        title_label.pack(side=tk.LEFT, pady=10)

        # Settings Button
        settings_btn = tk.Button(
            header_frame,
            text="⚙",
            bg=AppColors.BG_TERTIARY,
            fg=AppColors.TEXT_PRIMARY,
            font=("Roboto", 16),
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.open_settings,
        )
        settings_btn.pack(side=tk.RIGHT, pady=10, padx=(10, 0))

        # Status Indicator
        self.status_label = tk.Label(
            header_frame,
            text="OFFLINE",
            bg=AppColors.BG_PRIMARY,
            fg=AppColors.TEXT_SECONDARY,
            font=("Roboto", 10, "bold"),
        )
        self.status_label.pack(side=tk.RIGHT, pady=15)

    def open_settings(self) -> None:
        """Open the settings window."""
        SettingsWindow(self.root, self.exporter)

    def _create_metrics(self) -> None:
        metrics_frame = tk.Frame(self.root, bg=AppColors.BG_PRIMARY)
        metrics_frame.pack(fill=tk.X, padx=20, pady=10)

        # Main APM Display
        apm_card = tk.Frame(metrics_frame, bg=AppColors.BG_SECONDARY)
        apm_card.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            apm_card,
            text="ACTIONS PER MINUTE",
            bg=AppColors.BG_SECONDARY,
            fg=AppColors.TEXT_SECONDARY,
            font=AppFonts.METRIC_TITLE,
        ).pack(pady=(10, 2))

        self.apm_label = ttk.Label(apm_card, text="0", style="Metric.TLabel")
        self.apm_label.pack(pady=(0, 10))

        # Stats Row
        stats_row = tk.Frame(metrics_frame, bg=AppColors.BG_PRIMARY)
        stats_row.pack(fill=tk.X)

        # Helper to create stat card
        def create_stat_card(
            parent: tk.Widget, title: str, initial_value: str
        ) -> ttk.Label:
            card = tk.Frame(parent, bg=AppColors.BG_TERTIARY)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            tk.Label(
                card,
                text=title,
                bg=AppColors.BG_TERTIARY,
                fg=AppColors.TEXT_SECONDARY,
                font=AppFonts.STAT_TITLE,
            ).pack(pady=(10, 2))

            label = ttk.Label(card, text=initial_value, style="Stat.TLabel")
            label.pack(pady=(0, 10))
            return label

        self.total_label = create_stat_card(stats_row, "TOTAL ACTIONS", "0")
        self.avg_label = create_stat_card(stats_row, "AVERAGE APM", "0")
        self.time_label = create_stat_card(stats_row, "SESSION TIME", "00:00:00")

    def _create_graph(self) -> None:
        graph_frame = tk.Frame(self.root, bg=AppColors.BG_SECONDARY)
        graph_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(
            graph_frame,
            text="APM HISTORY (Last 60s)",
            bg=AppColors.BG_SECONDARY,
            fg=AppColors.TEXT_SECONDARY,
            font=("Roboto", 9, "bold"),
        ).pack(pady=(10, 5))

        # Replaced Matplotlib with custom Canvas GraphWidget
        self.graph = GraphWidget(graph_frame, height=200, bg=AppColors.BG_SECONDARY)
        self.graph.pack(fill=tk.BOTH, expand=True)

    def _create_controls(self) -> None:
        control_frame = tk.Frame(self.root, bg=AppColors.BG_PRIMARY)
        control_frame.pack(fill=tk.X, padx=20, pady=20)

        self.start_btn = tk.Button(
            control_frame,
            text="START TRACKING",
            bg=AppColors.ACCENT,
            fg="white",
            font=("Roboto", 12, "bold"),
            relief=tk.FLAT,
            pady=10,
            command=self.toggle_tracking,
        )
        self.start_btn.pack(fill=tk.X)

    def toggle_tracking(self) -> None:
        """Toggle the tracking state between running and stopped."""
        if not self.running:
            # Start
            self.running = True
            self.calculator.start()
            self.start_btn.config(text="STOP TRACKING", bg=AppColors.DANGER)
            self.status_label.config(text="LIVE", fg=AppColors.SUCCESS)

            # Clear graph
            self.graph.clear()
        else:
            # Stop
            self.running = False
            self.calculator.stop()
            self.start_btn.config(text="START TRACKING", bg=AppColors.ACCENT)
            self.status_label.config(text="PAUSED", fg=AppColors.DANGER)

    def on_metrics_update(self, metrics: Dict[str, Any]) -> None:
        """Callback received from APMCalculator when metrics are updated."""
        # Schedule UI update on the main thread
        try:
            self.root.after(0, lambda: self._update_view(metrics))
        except Exception as e:
            logger.error("Failed to schedule UI update: %s", e, exc_info=True)

    def _update_view(self, metrics: Dict[str, Any]) -> None:
        """Update UI elements with new metrics."""
        try:
            # Update Labels
            self.apm_label.config(text=f"{int(metrics.get('current_apm', 0))}")
            self.total_label.config(text=f"{metrics.get('total_actions', 0)}")
            self.avg_label.config(text=f"{metrics.get('avg_apm', 0)}")

            # Format time
            total_seconds = int(metrics.get("session_time", 0))
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            self.time_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            # Update Graph
            current_apm = float(metrics.get("current_apm", 0))
            self.graph.update_data(current_apm)
        except Exception as e:
            logger.error("Error updating UI view: %s", e, exc_info=True)
