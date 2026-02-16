"""
APM Calculator Module
Handles the core logic for tracking user actions and calculating APM/APS statistics.
"""

import time
import threading
from collections import deque
from typing import Dict, Optional, Union, Any, List, Callable
from pynput import mouse, keyboard  # type: ignore


class APMCalculator:
    """
    Core logic for APM tracking.
    Handles input monitoring and APM calculations in a thread-safe manner.
    Implements Observer pattern to notify listeners of updates.
    """

    def __init__(self, window_size: int = 60) -> None:
        # Thread safety
        self._lock = threading.Lock()

        # Core tracking data structures
        self.actions: deque[float] = deque()  # Stores timestamps of recent actions
        self.total_actions: int = 0  # Total actions in current session
        self.session_start: Optional[float] = None  # Session start timestamp
        self.running: bool = False  # Tracking state

        # Configuration
        self.window_size: int = window_size

        # Listeners
        self.mouse_listener: Optional[mouse.Listener] = None
        self.keyboard_listener: Optional[keyboard.Listener] = None

        # Observers
        self._observers: List[Callable[[Dict[str, Any]], None]] = []
        self._update_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def add_observer(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register an observer callback."""
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unregister an observer callback."""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self) -> None:
        """Notify all observers with current metrics."""
        metrics = self.get_metrics()
        for callback in self._observers:
            try:
                callback(metrics)
            except Exception as e:
                print(f"Error notifying observer: {e}")

    def start(self) -> None:
        """Start tracking inputs."""
        if self.running:
            return

        self.running = True
        self.session_start = time.time()
        self.actions.clear()
        self.total_actions = 0

        # Start listeners
        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self._on_press)

        self.mouse_listener.start()
        self.keyboard_listener.start()

        # Start update loop thread
        self._stop_event.clear()
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()

    def stop(self) -> None:
        """Stop tracking inputs."""
        if not self.running:
            return

        self.running = False
        self._stop_event.set()

        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

        if self._update_thread:
            self._update_thread.join(timeout=1.0)

    def _update_loop(self) -> None:
        """Background loop to calculate and notify metrics."""
        while not self._stop_event.is_set():
            self._notify_observers()
            time.sleep(0.1)  # 100ms update rate

    def reset(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self.actions.clear()
            self.total_actions = 0
            self.session_start = time.time() if self.running else None

    def _record_action(self) -> None:
        """Record an action timestamp safely."""
        if not self.running:
            return

        current_time = time.time()
        with self._lock:
            self.actions.append(current_time)
            self.total_actions += 1

            # Optimization: Remove old actions immediately to prevent memory growth
            # We keep a bit more than window_size just in case, but strict cleanup happens in calculate
            # This ensures we never grow indefinitely even if get_metrics is not called
            while (
                self.actions and current_time - self.actions[0] > self.window_size + 10
            ):
                self.actions.popleft()

    def _on_click(self, _x: int, _y: int, _button: Any, pressed: bool) -> None:
        """Mouse click handler."""
        if pressed:
            self._record_action()

    def _on_press(self, _key: Any) -> None:
        """Keyboard press handler."""
        self._record_action()

    def get_metrics(self) -> Dict[str, Union[float, int]]:
        """
        Calculate and return current metrics.
        Returns a dictionary with current_apm, avg_apm, total_actions, session_time.
        """
        if not self.running or self.session_start is None:
            return {
                "current_apm": 0.0,
                "avg_apm": 0.0,
                "aps": 0.0,
                "total_actions": 0,
                "session_time": 0,
            }

        current_time = time.time()
        session_duration = current_time - self.session_start

        # Snapshot data within lock to minimize contention with input threads
        with self._lock:
            # Clean up old actions for accurate sliding window calculation
            while self.actions and current_time - self.actions[0] > self.window_size:
                self.actions.popleft()

            # Copy data for calculation outside lock (fast C-level copy)
            actions_snapshot = list(self.actions)
            total_actions_snapshot = self.total_actions

        # --- Calculations performed without holding the lock ---
        
        recent_actions_count = len(actions_snapshot)

        # Calculate APS (Actions Per Second) - last 10 seconds
        # We iterate backwards to be faster
        aps_actions = 0
        for timestamp in reversed(actions_snapshot):
            if current_time - timestamp <= 10:
                aps_actions += 1
            else:
                break

        # Calculate Current APM
        time_window = min(self.window_size, session_duration)
        if time_window > 0:
            current_apm = (recent_actions_count / time_window) * 60
        else:
            current_apm = 0

        # Calculate Average APM
        if session_duration > 0:
            avg_apm = (total_actions_snapshot / session_duration) * 60
        else:
            avg_apm = 0

        # Calculate APS
        aps = (
            aps_actions / 10.0
            if session_duration >= 10
            else (aps_actions / session_duration if session_duration > 0 else 0)
        )

        return {
            "current_apm": round(current_apm, 1),
            "avg_apm": round(avg_apm, 1),
            "aps": round(aps, 1),
            "total_actions": total_actions_snapshot,
            "session_time": int(session_duration),
        }
