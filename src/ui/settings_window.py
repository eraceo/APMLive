"""
Settings Window Module
Handles the configuration of the application settings (e.g., export options).
"""

import tkinter as tk
from typing import Dict

from src.utils.config import AppColors, AppFonts
from src.core.exporter import DataExporter


class SettingsWindow:
    """
    Window for configuring application settings.
    """

    def __init__(self, root: tk.Tk, exporter: DataExporter) -> None:
        self.root = root
        self.exporter = exporter

        self.window = tk.Toplevel(self.root)
        self.window.title("Settings - TXT Export")
        self.window.geometry("450x550")
        self.window.configure(bg=AppColors.BG_PRIMARY)
        self.window.resizable(False, False)
        self.window.transient(self.root)
        self.window.grab_set()

        self.vars: Dict[str, tk.BooleanVar] = {}
        self._create_content()

    def _create_content(self) -> None:
        # Title
        tk.Label(
            self.window,
            text="TXT Export Configuration",
            bg=AppColors.BG_PRIMARY,
            fg=AppColors.TEXT_PRIMARY,
            font=AppFonts.HEADER,
        ).pack(pady=(20, 5))

        tk.Label(
            self.window,
            text="Choose which data to include in the TXT file",
            bg=AppColors.BG_PRIMARY,
            fg=AppColors.TEXT_SECONDARY,
            font=AppFonts.NORMAL,
        ).pack(pady=(0, 20))

        # Options
        options_frame = tk.Frame(self.window, bg=AppColors.BG_SECONDARY)
        options_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        options = [
            ("apm", "Current APM", "Actions per minute in real-time"),
            ("total_actions", "Total Actions", "Total number of actions"),
            ("session_time", "Session Time", "Session duration"),
            ("avg_apm", "Average APM", "Average APM for the session"),
            ("actions_per_second", "Actions/sec", "Actions per second"),
            ("timestamp", "Timestamp", "Unix timestamp"),
        ]

        for key, title, desc in options:
            self._add_checkbox(options_frame, key, title, desc)

        # Buttons
        btn_frame = tk.Frame(self.window, bg=AppColors.BG_PRIMARY)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)

        tk.Button(
            btn_frame,
            text="Save",
            bg=AppColors.SUCCESS,
            fg="white",
            font=("Roboto", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=self._save,
        ).pack(side=tk.RIGHT)

        tk.Button(
            btn_frame,
            text="Cancel",
            bg=AppColors.BG_TERTIARY,
            fg=AppColors.TEXT_PRIMARY,
            font=("Roboto", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=self.window.destroy,
        ).pack(side=tk.RIGHT, padx=10)

    def _add_checkbox(self, parent: tk.Widget, key: str, title: str, desc: str) -> None:
        frame = tk.Frame(parent, bg=AppColors.BG_SECONDARY)
        frame.pack(fill=tk.X, padx=15, pady=5)

        var = tk.BooleanVar(value=self.exporter.txt_settings.get(key, False))
        self.vars[key] = var

        tk.Checkbutton(
            frame,
            variable=var,
            bg=AppColors.BG_SECONDARY,
            selectcolor=AppColors.BG_TERTIARY,
            activebackground=AppColors.BG_SECONDARY,
        ).pack(side=tk.LEFT)

        info = tk.Frame(frame, bg=AppColors.BG_SECONDARY)
        info.pack(side=tk.LEFT, fill=tk.X, padx=10)

        tk.Label(
            info,
            text=title,
            bg=AppColors.BG_SECONDARY,
            fg=AppColors.TEXT_PRIMARY,
            font=("Roboto", 10, "bold"),
        ).pack(anchor="w")
        tk.Label(
            info,
            text=desc,
            bg=AppColors.BG_SECONDARY,
            fg=AppColors.TEXT_SECONDARY,
            font=("Roboto", 8),
        ).pack(anchor="w")

    def _save(self) -> None:
        new_settings = {k: v.get() for k, v in self.vars.items()}
        self.exporter.txt_settings.update(new_settings)
        self.exporter.save_settings()
        self.window.destroy()
