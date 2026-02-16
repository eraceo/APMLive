"""
Data Exporter Module
Handles exporting APM data to JSON and TXT files.
"""

import os
import json
import threading
from typing import Dict, Any, Optional
from src.utils.logger import setup_logger

logger = setup_logger("Exporter")


class DataExporter:
    """
    Handles data export to TXT and JSON files.
    """

    def __init__(self, data_dir: Optional[str] = None) -> None:
        if data_dir is None:
            # We need to handle the case where LOCALAPPDATA might not be set, though on Windows it usually is.
            # Fallback to current directory if not found, or raise error?
            # For now, let's assume it exists or fallback to a safe default like "."
            local_app_data = os.getenv("LOCALAPPDATA")
            if local_app_data:
                self.data_dir = os.path.join(local_app_data, "APMLive")
            else:
                self.data_dir = os.path.join(os.getcwd(), "APMLive_Data")
        else:
            self.data_dir = data_dir

        self.output_file: str = os.path.join(self.data_dir, "apm_data.txt")
        self.json_file: str = os.path.join(self.data_dir, "apm_data.json")
        self.settings_file: str = os.path.join(self.data_dir, "settings.json")

        # Default settings
        self.txt_settings: Dict[str, bool] = {
            "apm": True,
            "total_actions": True,
            "session_time": True,
            "avg_apm": False,
            "actions_per_second": False,
            "timestamp": False,
        }

        # Ensure directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        self.load_settings()

    def load_settings(self) -> None:
        """Load export settings from JSON file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    saved_settings = json.load(f)
                    self.txt_settings.update(saved_settings.get("txt_export", {}))
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error loading settings: {e}")

    def save_settings(self) -> None:
        """Save current export settings to JSON file."""
        try:
            settings_data = {"txt_export": self.txt_settings}
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, indent=2)
        except (IOError, TypeError) as e:
            logger.error(f"Error saving settings: {e}")

    def update_settings(self, new_settings: Dict[str, bool]) -> None:
        """Update settings and save to disk."""
        self.txt_settings.update(new_settings)
        self.save_settings()

    def export(self, metrics: Dict[str, Any]) -> None:
        """
        Write metrics to files based on configuration.
        Should be called periodically.
        """
        # We run this in a thread to avoid blocking the UI/Calculator if I/O is slow
        threading.Thread(target=self._write_files, args=(metrics,), daemon=True).start()

    def _write_files(self, metrics: Dict[str, Any]) -> None:
        try:
            # 1. JSON Export (always full data)
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(metrics, f)

            # 2. TXT Export (configurable)
            output_parts = []

            if self.txt_settings.get("timestamp", False):
                output_parts.append(f"TS: {int(metrics.get('timestamp', 0))}")

            if self.txt_settings.get("apm", True):
                output_parts.append(f"APM: {int(metrics.get('current_apm', 0))}")

            if self.txt_settings.get("avg_apm", False):
                output_parts.append(f"AVG: {int(metrics.get('avg_apm', 0))}")

            if self.txt_settings.get("actions_per_second", False):
                output_parts.append(f"APS: {metrics.get('aps', 0)}")

            if self.txt_settings.get("total_actions", True):
                output_parts.append(f"Total: {metrics.get('total_actions', 0)}")

            if self.txt_settings.get("session_time", True):
                # Format time HH:MM:SS
                total_seconds = int(metrics.get("session_time", 0))
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                output_parts.append(f"Time: {time_str}")

            content = " | ".join(output_parts)

            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(content)

        except (IOError, TypeError, ValueError) as e:
            logger.error(f"Export error: {e}")
