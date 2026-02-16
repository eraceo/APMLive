import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from src.core.calculator import APMCalculator


@pytest.fixture
def calculator():
    calc = APMCalculator(window_size=60)
    # Mock listeners to avoid actual hardware hooks during tests
    calc.mouse_listener = MagicMock()
    calc.keyboard_listener = MagicMock()
    return calc


def test_initial_state(calculator):
    metrics = calculator.get_metrics()
    assert metrics["current_apm"] == 0.0
    assert metrics["total_actions"] == 0
    assert metrics["avg_apm"] == 0.0


def test_action_recording(calculator):
    calculator.running = True
    calculator.session_start = time.time()

    # Record 60 actions
    for _ in range(60):
        calculator._record_action()

    metrics = calculator.get_metrics()
    assert metrics["total_actions"] == 60


def test_apm_calculation(calculator):
    calculator.running = True
    calculator.session_start = time.time() - 60  # Session started 60s ago

    # Simulate 60 actions spread over the last minute
    # Ideally 1 action per second = 60 APM
    current_time = time.time()
    with calculator._lock:
        for i in range(60):
            calculator.actions.append(current_time - i)
        calculator.total_actions = 60

    metrics = calculator.get_metrics()
    # Depending on exact timing, it should be close to 60
    assert 58 <= metrics["current_apm"] <= 62
    assert 58 <= metrics["avg_apm"] <= 62


def test_reset(calculator):
    calculator.running = True
    calculator._record_action()
    calculator.reset()

    metrics = calculator.get_metrics()
    assert metrics["total_actions"] == 0
    assert len(calculator.actions) == 0


# --- NOUVEAUX TESTS POUR LA COUVERTURE ---


def test_start_stop(calculator):
    """Test start and stop logic, ensuring threads are managed correctly."""
    with patch("threading.Thread") as MockThread, patch(
        "pynput.mouse.Listener"
    ) as MockMouse, patch("pynput.keyboard.Listener") as MockKeyboard:

        # Setup mock thread
        mock_thread_instance = MockThread.return_value

        # 1. Start
        calculator.start()
        assert calculator.running is True
        assert calculator.session_start is not None

        # Check listeners started
        MockMouse.return_value.start.assert_called_once()
        MockKeyboard.return_value.start.assert_called_once()

        # Check update thread started
        MockThread.assert_called_with(target=calculator._update_loop, daemon=True)
        mock_thread_instance.start.assert_called_once()

        # 2. Start again (should do nothing)
        calculator.start()
        # Counts should not increase
        assert MockMouse.return_value.start.call_count == 1

        # 3. Stop
        calculator.stop()
        assert calculator.running is False
        assert calculator._stop_event.is_set()

        # Check listeners stopped
        calculator.mouse_listener.stop.assert_called_once()
        calculator.keyboard_listener.stop.assert_called_once()

        # Check thread join
        mock_thread_instance.join.assert_called_with(timeout=1.0)

        # 4. Stop again (should do nothing)
        calculator.stop()


def test_update_loop(calculator):
    """Test the background update loop."""
    # We want to run the loop for a short time and verify it calls notify_observers
    calculator._stop_event.clear()

    # Mock notify_observers to track calls
    calculator._notify_observers = MagicMock()

    # Create a thread to run the loop
    t = threading.Thread(target=calculator._update_loop)
    t.start()

    # Wait until called (polling)
    start_time = time.time()
    while calculator._notify_observers.call_count == 0:
        if time.time() - start_time > 2.0:
            break
        time.sleep(0.05)

    calculator._stop_event.set()
    t.join(timeout=1.0)

    assert calculator._notify_observers.call_count >= 1


def test_observer_pattern(calculator):
    """Test adding, removing, and notifying observers."""
    mock_observer = MagicMock()

    # Add
    calculator.add_observer(mock_observer)
    assert mock_observer in calculator._observers

    # Add duplicate (should be ignored)
    calculator.add_observer(mock_observer)
    assert len(calculator._observers) == 1

    # Notify
    calculator.running = True
    calculator.session_start = time.time()
    calculator._notify_observers()
    mock_observer.assert_called_once()

    # Remove
    calculator.remove_observer(mock_observer)
    assert mock_observer not in calculator._observers

    # Notify (should not call)
    calculator._notify_observers()
    assert mock_observer.call_count == 1  # Still 1 from previous call


def test_observer_error_handling(calculator):
    """Test that observer errors don't crash the app."""
    bad_observer = MagicMock(side_effect=Exception("Boom"))
    calculator.add_observer(bad_observer)

    calculator.running = True
    calculator.session_start = time.time()

    # Should not raise exception
    try:
        calculator._notify_observers()
    except Exception:
        pytest.fail("Observer error should be caught")


def test_input_handlers(calculator):
    """Test the actual input callback methods."""
    calculator.running = True
    calculator.session_start = time.time()

    # Mouse
    calculator._on_click(0, 0, None, True)  # Pressed
    assert calculator.total_actions == 1

    calculator._on_click(0, 0, None, False)  # Released (should ignore)
    assert calculator.total_actions == 1

    # Keyboard
    calculator._on_press(None)
    assert calculator.total_actions == 2


def test_record_action_not_running(calculator):
    """Test _record_action when not running."""
    calculator.running = False
    calculator._record_action()
    assert calculator.total_actions == 0
    assert len(calculator.actions) == 0


def test_buffer_cleanup(calculator):
    """Test that old actions are removed from the buffer."""
    calculator.running = True
    calculator.session_start = time.time() - 100

    current_time = time.time()

    # 1. Test cleanup during recording (_record_action)
    with calculator._lock:
        calculator.actions.append(current_time - 80)  # 80s ago (older than 60+10)

    # Add new action, should trigger cleanup
    calculator._record_action()

    # The old action should be removed because 80 > 70
    assert len(calculator.actions) == 1  # Only the new one remains

    # 2. Test cleanup during metrics calculation (get_metrics)
    calculator.actions.clear()
    with calculator._lock:
        calculator.actions.append(current_time - 65)  # 65s ago (older than 60)

    metrics = calculator.get_metrics()

    # get_metrics cleans strictly > window_size (60)
    # So the action from 65s ago should be removed for calculation purposes
    # Wait, we need to check internal state or result
    # If removed, recent_actions_count should be 0 (if we only added that one)
    assert metrics["current_apm"] == 0.0


def test_aps_calculation_edge_cases(calculator):
    """Test APS calculation including edge cases."""
    calculator.running = True
    calculator.session_start = time.time()

    # Case 1: Session < 10s
    # 5 actions in 5 seconds
    current_time = time.time()
    with calculator._lock:
        for i in range(5):
            calculator.actions.append(current_time - i)
        calculator.total_actions = 5
        # Mock session start to be 5s ago
        calculator.session_start = current_time - 5

    metrics = calculator.get_metrics()
    # APS = 5 actions / 5 seconds = 1.0
    assert metrics["aps"] == 1.0

    # Case 2: Session > 10s (Standard)
    # 10 actions in last 10s
    with calculator._lock:
        calculator.actions.clear()
        for i in range(10):
            calculator.actions.append(current_time - i)
        calculator.total_actions = 10
        # Mock session start to be 20s ago
        calculator.session_start = current_time - 20

    metrics = calculator.get_metrics()
    # APS = 10 actions / 10s (fixed window) = 1.0
    assert metrics["aps"] == 1.0

    # Case 3: Session 0s (Edge case)
    # Clear actions to avoid APS calculation dividing by zero or small duration
    with calculator._lock:
        calculator.actions.clear()
        calculator.total_actions = 0
    calculator.session_start = time.time()
    metrics = calculator.get_metrics()
    assert metrics["aps"] == 0.0

    # Case 6: Avg APM with session_duration = 0
    # This covers the 'else' branch in: avg_apm = ... if session_duration > 0 else 0
    with calculator._lock:
        calculator.actions.clear()
        calculator.total_actions = 10
    calculator.session_start = time.time()  # 0s duration (approx)
    metrics = calculator.get_metrics()
    # It might be slightly > 0 due to execution time, so we check if duration logic works
    # If duration is effectively 0, avg_apm should be 0
    # To force 0 duration, we can set start time to future slightly
    calculator.session_start = time.time() + 1
    metrics = calculator.get_metrics()
    assert metrics["avg_apm"] == 0.0

    # Case 4: APS loop break (optimization coverage)
    # Add actions older than 10s
    with calculator._lock:
        calculator.actions.clear()
        calculator.actions.append(current_time - 15)  # 15s ago
        # Ensure session is long enough for loop to check timestamps
        calculator.session_start = current_time - 20

    metrics = calculator.get_metrics()
    assert metrics["aps"] == 0.0

    # Case 5: APS calculation with session_duration > 0 but < 10 (Branch coverage)
    # This covers the 'else' branch in: else (aps_actions / session_duration if session_duration > 0 else 0)
    with calculator._lock:
        calculator.actions.clear()
        calculator.total_actions = 0
    calculator.session_start = current_time - 5  # 5s duration
    metrics = calculator.get_metrics()
    assert metrics["aps"] == 0.0


def test_apm_calculation_zero_window(calculator):
    """Test APM calculation when time window is 0."""
    calculator.running = True
    calculator.session_start = time.time()
    # time_window = min(window_size, session_duration)
    # if session_duration is 0, time_window is 0
    metrics = calculator.get_metrics()
    assert metrics["current_apm"] == 0.0
    assert metrics["avg_apm"] == 0.0


def test_get_metrics_not_running(calculator):
    """Test metrics when not running."""
    calculator.running = False
    metrics = calculator.get_metrics()
    assert metrics["current_apm"] == 0
    assert metrics["session_time"] == 0
