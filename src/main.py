"""
Entry point for the APMLive application.
"""

import sys
import os
from types import TracebackType
from typing import Type, Optional
import tkinter as tk

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
from src.core.calculator import APMCalculator
from src.ui.main_window import MainWindow
from src.utils.logger import setup_logger

logger = setup_logger()


def handle_exception(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_traceback: Optional[TracebackType],
) -> None:
    """Global exception handler to log unhandled exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


def main() -> None:
    """Initialize and start the application."""
    logger.info("Application starting...")
    try:
        root = tk.Tk()

        # Initialize Core Logic
        calculator = APMCalculator()

        # Initialize UI
        _app = MainWindow(root, calculator)

        # Start Application
        root.mainloop()
    except Exception as e:
        logger.critical("Fatal error in main loop: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Application stopped")


if __name__ == "__main__":
    main()
