import pytest
import time
from unittest.mock import MagicMock
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
    assert metrics['current_apm'] == 0.0
    assert metrics['total_actions'] == 0
    assert metrics['avg_apm'] == 0.0

def test_action_recording(calculator):
    calculator.running = True
    calculator.session_start = time.time()
    
    # Record 60 actions
    for _ in range(60):
        calculator._record_action()
        
    metrics = calculator.get_metrics()
    assert metrics['total_actions'] == 60

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
    assert 58 <= metrics['current_apm'] <= 62
    assert 58 <= metrics['avg_apm'] <= 62

def test_reset(calculator):
    calculator.running = True
    calculator._record_action()
    calculator.reset()
    
    metrics = calculator.get_metrics()
    assert metrics['total_actions'] == 0
    assert len(calculator.actions) == 0
