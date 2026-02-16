"""
Logging Configuration Module
Handles application-wide logging setup.
"""

import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(name: str = "APMLive") -> logging.Logger:
    """
    Configure and return a logger instance.
    Logs are written to %LOCALAPPDATA%/APMLive/app.log and console.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger

    # Formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # 1. File Handler (Rotating)
    # Determine log directory
    if sys.platform == "win32":
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            log_dir = Path(local_app_data) / "APMLive" / "logs"
        else:
            log_dir = Path.cwd() / "logs"
    else:
        log_dir = Path.home() / ".apmlive" / "logs"

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"

        file_handler = RotatingFileHandler(
            log_file, maxBytes=1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    except (OSError, PermissionError) as e:
        print(f"Failed to create log file: {e}")

    # 2. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger
