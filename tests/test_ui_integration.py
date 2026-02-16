"""
UI Integration Tests
"""

import pytest
import tkinter as tk
from unittest.mock import MagicMock
from src.ui.main_window import MainWindow
from src.core.calculator import APMCalculator


@pytest.fixture
def mock_tk_root():
    """Create a mock root window without showing it."""
    root = tk.Tk()
    root.withdraw()  # Hide the window
    yield root
    root.destroy()


def test_ui_startup(mock_tk_root):
    """
    Test if the MainWindow can be instantiated without errors.
    """
    calculator = APMCalculator()
    
    try:
        app = MainWindow(mock_tk_root, calculator)
        
        # Verify critical components are created
        assert app.root is mock_tk_root
        assert app.calculator is calculator
        assert hasattr(app, 'apm_label')
        assert hasattr(app, 'start_btn')
        
        # Verify initial state
        assert app.running is False
        assert app.start_btn.cget('text') == "START TRACKING"
        
    except Exception as e:
        pytest.fail(f"UI failed to initialize: {e}")


def test_ui_toggle_tracking(mock_tk_root):
    """
    Test the start/stop button logic.
    """
    calculator = APMCalculator()
    # Mock calculator methods to avoid actual hardware hooks
    calculator.start = MagicMock()
    calculator.stop = MagicMock()
    
    app = MainWindow(mock_tk_root, calculator)
    
    # 1. Start Tracking
    app.toggle_tracking()
    assert app.running is True
    assert app.start_btn.cget('text') == "STOP TRACKING"
    calculator.start.assert_called_once()
    
    # 2. Stop Tracking
    app.toggle_tracking()
    assert app.running is False
    assert app.start_btn.cget('text') == "START TRACKING"
    calculator.stop.assert_called_once()
