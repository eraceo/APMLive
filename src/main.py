"""
Entry point for the APMLive application.
"""

import sys
import os
import tkinter as tk

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
from src.core.calculator import APMCalculator
from src.ui.main_window import MainWindow


def main() -> None:
    """Initialize and start the application."""
    root = tk.Tk()

    # Initialize Core Logic
    calculator = APMCalculator()

    # Initialize UI
    _app = MainWindow(root, calculator)

    # Start Application
    root.mainloop()


if __name__ == "__main__":
    main()
