
"""
UI Integration Tests
"""

import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
from src.ui.main_window import MainWindow
from src.core.calculator import APMCalculator

# Check if Tkinter is available/working
try:
    root = tk.Tk()
    root.destroy()
    TK_AVAILABLE = True
except tk.TclError:
    TK_AVAILABLE = False


@pytest.fixture
def mock_tk_root():
    """Create a mock root window without showing it."""
    if not TK_AVAILABLE:
        # Return a MagicMock that simulates a Tk root
        root = MagicMock()
        # Mock common Tk methods used by MainWindow
        root.register = MagicMock()
        root.winfo_screenwidth.return_value = 1920
        root.winfo_screenheight.return_value = 1080
        yield root
    else:
        root = tk.Tk()
        root.withdraw()  # Hide the window
        yield root
        root.destroy()


def test_ui_startup(mock_tk_root):
    """
    Test if the MainWindow can be instantiated without errors.
    """
    if not TK_AVAILABLE:
        # If Tk is not available, we need to patch tkinter.Label, tkinter.Button etc.
        # because MainWindow instantiates them.
        with patch('tkinter.Label'), \
             patch('tkinter.Button'), \
             patch('tkinter.Frame'), \
             patch('tkinter.Entry'), \
             patch('tkinter.StringVar'), \
             patch('tkinter.IntVar'), \
             patch('tkinter.BooleanVar'), \
             patch('tkinter.Checkbutton'):
            _run_ui_startup_test(mock_tk_root)
    else:
        _run_ui_startup_test(mock_tk_root)

def _run_ui_startup_test(root):
    calculator = APMCalculator()
    try:
        app = MainWindow(root, calculator)
        
        # Verify critical components are created
        assert app.root is root
        assert app.calculator is calculator
        assert hasattr(app, 'apm_label')
        assert hasattr(app, 'start_btn')
        
        # Verify initial state
        assert app.running is False
        # If we are mocking widgets, we can't check cget easily unless we mock that too
        if TK_AVAILABLE:
            assert app.start_btn.cget('text') == "START TRACKING"
        
    except Exception as e:
        pytest.fail(f"UI failed to initialize: {e}")


def test_ui_toggle_tracking(mock_tk_root):
    """
    Test the start/stop button logic.
    """
    if not TK_AVAILABLE:
        with patch('tkinter.Label'), \
             patch('tkinter.Button') as MockButton, \
             patch('tkinter.Frame'), \
             patch('tkinter.Entry'), \
             patch('tkinter.StringVar'), \
             patch('tkinter.IntVar'), \
             patch('tkinter.BooleanVar'), \
             patch('tkinter.Checkbutton'):
            
            # Setup MockButton to return an object with configure method
            mock_btn_instance = MagicMock()
            MockButton.return_value = mock_btn_instance
            
            _run_ui_toggle_tracking_test(mock_tk_root, mock_btn_instance)
    else:
        _run_ui_toggle_tracking_test(mock_tk_root, None)

def _run_ui_toggle_tracking_test(root, mock_btn):
    calculator = APMCalculator()
    # Mock calculator methods to avoid actual hardware hooks
    calculator.start = MagicMock()
    calculator.stop = MagicMock()
    
    app = MainWindow(root, calculator)
    
    # If mocking, we need to ensure app.start_btn refers to our mock or is captured correctly
    # MainWindow usually does: self.start_btn = tk.Button(...)
    
    # 1. Start Tracking
    app.toggle_tracking()
    assert app.running is True
    
    if TK_AVAILABLE:
        assert app.start_btn.cget('text') == "STOP TRACKING"
    elif mock_btn:
        # Check if configure was called with text="STOP TRACKING"
        # Note: tkinter widgets use configure(text=...) or config(text=...)
        # And cget is used to get values.
        # We assume toggle_tracking calls .config(text=...)
        assert mock_btn.config.called or mock_btn.configure.called
        
    calculator.start.assert_called_once()
    
    # 2. Stop Tracking
    app.toggle_tracking()
    assert app.running is False
    
    if TK_AVAILABLE:
        assert app.start_btn.cget('text') == "START TRACKING"
    
    calculator.stop.assert_called_once()
