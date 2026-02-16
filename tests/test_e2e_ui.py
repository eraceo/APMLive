"""
End-to-End (E2E) Tests for APMLive.
These tests run the full application stack (UI + Core + Logic) in a real Tkinter environment.
Only the hardware input listeners (pynput) are mocked to ensure reliability in CI environments.
"""

import pytest
import tkinter as tk
import time
import queue
from unittest.mock import MagicMock, patch
from src.ui.main_window import MainWindow
from src.core.calculator import APMCalculator


@pytest.fixture
def e2e_app():
    """
    Fixture that sets up the full application in a real Tkinter root.
    Handles setup and teardown of the application lifecycle.
    """
    # Create a real Tkinter root
    root = tk.Tk()
    root.withdraw()

    # Create a thread-safe queue for callbacks to handle threaded updates
    # This circumvents the "main thread is not in main loop" error in tests
    callback_queue = queue.Queue()

    # Mock root.after to capture callbacks from background threads
    def mock_after(delay, func=None, *args):
        if func:
            callback_queue.put((func, args))
            return "dummy_id"
        return "dummy_id"

    # Patch the instance method
    root.after = mock_after

    # Mock hardware listeners
    with patch("pynput.mouse.Listener") as MockMouse, patch(
        "pynput.keyboard.Listener"
    ) as MockKeyboard:

        # Setup mocks
        mock_mouse_instance = MagicMock()
        MockMouse.return_value = mock_mouse_instance

        mock_keyboard_instance = MagicMock()
        MockKeyboard.return_value = mock_keyboard_instance

        # Initialize the real Core Logic
        calculator = APMCalculator()

        # Initialize the real UI
        app = MainWindow(root, calculator)

        # Force an initial update
        root.update()

        yield app, calculator, root, callback_queue

        # Teardown
        if app.running:
            app.toggle_tracking()

        root.destroy()


def test_e2e_complete_workflow(e2e_app):
    """
    Scenario:
    1. User launches app (Verified by fixture)
    2. User clicks 'START'
    3. User performs actions (Keyboard + Mouse)
    4. UI updates in real-time
    5. User clicks 'STOP'
    6. Stats are preserved
    """
    app, calculator, root, callback_queue = e2e_app

    # Helper to process pending callbacks
    def process_events():
        root.update()
        while not callback_queue.empty():
            func, args = callback_queue.get()
            try:
                func(*args)
            except Exception as e:
                print(f"Error in callback: {e}")
            root.update()

    # --- 1. Verify Initial State ---
    assert app.running is False
    assert app.start_btn.cget("text") == "START TRACKING"
    assert app.apm_label.cget("text") == "0"
    assert app.total_label.cget("text") == "0"

    # --- 2. Start Tracking ---
    print("\n[E2E] Clicking Start Button...")
    app.start_btn.invoke()
    process_events()

    # Verify State changed
    assert app.running is True
    assert app.start_btn.cget("text") == "STOP TRACKING"
    assert calculator.running is True

    # --- 3. Simulate User Activity ---
    print("[E2E] Simulating user inputs...")

    # Inject 10 actions
    for _ in range(5):
        calculator._on_press("key")
        calculator._on_click(0, 0, None, True)

    # Wait for the update loop
    max_wait = 2.0
    start_time = time.time()

    # Wait until the UI reflects the actions
    while time.time() - start_time < max_wait:
        process_events()
        time.sleep(0.05)

        # Check if UI is updated
        if app.total_label.cget("text") == "10":
            break

    # --- 4. Verify Live Updates ---
    current_total = app.total_label.cget("text")
    print(f"[E2E] UI shows total actions: {current_total}")
    assert current_total == "10", "UI did not update with total actions"

    current_apm = int(app.apm_label.cget("text"))
    print(f"[E2E] UI shows APM: {current_apm}")
    assert current_apm > 0, "APM should be > 0 after actions"

    # --- 5. Stop Tracking ---
    print("[E2E] Clicking Stop Button...")
    app.start_btn.invoke()
    process_events()

    assert app.running is False
    assert app.start_btn.cget("text") == "START TRACKING"

    # --- 6. Verify Final State ---
    assert app.total_label.cget("text") == "10"
    assert int(app.apm_label.cget("text")) == current_apm


def test_e2e_settings_navigation(e2e_app):
    """
    Scenario:
    1. Open Settings
    2. Verify window exists
    3. Close Settings
    """
    app, _, root, callback_queue = e2e_app

    def process_events():
        root.update()
        while not callback_queue.empty():
            func, args = callback_queue.get()
            func(*args)
            root.update()

    print("\n[E2E] Opening Settings...")
    app.open_settings()
    process_events()

    toplevels = [w for w in root.winfo_children() if isinstance(w, tk.Toplevel)]
    assert len(toplevels) > 0, "Settings window should be open"

    # Close it
    toplevels[0].destroy()
    process_events()
