import tkinter as tk
from collections import deque
from typing import Deque, List, Tuple
from src.utils.config import AppColors, AppFonts

class GraphWidget(tk.Canvas):
    """
    A lightweight, high-performance graph widget using Tkinter Canvas.
    Replaces heavy Matplotlib for real-time plotting.
    """
    def __init__(self, master, width=600, height=200, bg=AppColors.BG_SECONDARY, **kwargs):
        super().__init__(master, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        
        self.width = width
        self.height = height
        self.bg_color = bg
        
        # Data storage
        self.max_points = 60  # Store 60 seconds of data (assuming ~1 update/sec) or more if higher freq
        self.data: Deque[float] = deque(maxlen=600) # Store more points for smoothness if needed
        
        # Viewport settings
        self.y_min = 0
        self.y_max = 100
        self.padding_top = 20
        self.padding_bottom = 20
        self.padding_left = 40 # Space for labels
        self.padding_right = 10
        
        # Grid lines
        self.grid_lines_ids: List[int] = []
        self.label_ids: List[int] = []
        
        # The main data line
        self.line_id = None
        
        # Initial draw
        self._draw_grid()

        # Handle resize
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        self.width = event.width
        self.height = event.height
        self._draw_grid()
        self._redraw_line()

    def _draw_grid(self):
        """Draws background grid and labels."""
        self.delete("grid")
        self.delete("label")
        
        w = self.width
        h = self.height
        
        # Draw Y-axis grid lines (0, 50, 100, 150...)
        # We want about 4-5 lines
        step = self.y_max // 4 if self.y_max > 0 else 25
        if step == 0: step = 25
        
        for y_val in range(0, int(self.y_max * 1.2) + step, step):
            if y_val > self.y_max * 1.5: break
            
            y_pos = self._map_y(y_val)
            
            # Don't draw if out of bounds
            if y_pos < self.padding_top or y_pos > h - self.padding_bottom:
                continue
                
            # Line
            self.create_line(
                self.padding_left, y_pos, 
                w - self.padding_right, y_pos, 
                fill=AppColors.BORDER, dash=(2, 4), tags="grid"
            )
            
            # Label
            self.create_text(
                self.padding_left - 5, y_pos,
                text=str(y_val),
                fill=AppColors.TEXT_SECONDARY,
                anchor="e",
                font=("Roboto", 8),
                tags="label"
            )

    def _map_y(self, value: float) -> float:
        """Map a data value to a Y coordinate on canvas."""
        # Invert Y because canvas 0 is top
        available_height = self.height - self.padding_top - self.padding_bottom
        if self.y_max == self.y_min:
            return self.height - self.padding_bottom
            
        ratio = (value - self.y_min) / (self.y_max - self.y_min)
        return (self.height - self.padding_bottom) - (ratio * available_height)

    def update_data(self, new_value: float):
        """Add a new data point and update the graph."""
        self.data.append(new_value)
        
        # Auto-scale Y axis
        current_max = max(self.data) if self.data else 0
        target_max = max(100, current_max * 1.2)
        
        # Smooth scaling or instant? Instant for responsiveness, maybe dampen later
        if target_max != self.y_max:
            self.y_max = target_max
            self._draw_grid() # Re-draw grid if scale changes
            
        self._redraw_line()

    def _redraw_line(self):
        """Redraws the polyline."""
        if not self.data:
            return
            
        points = []
        w = self.width
        # X spacing: Spread data points across the available width
        # We show the last N points.
        # If we have fewer than max_points, we start from left.
        # Ideally, it's a sliding window.
        
        available_width = w - self.padding_left - self.padding_right
        
        # We want to display exactly 'maxlen' points filling the screen?
        # Or relative to time? 
        # For simplicity in this APM graph, we assume constant update rate.
        # We map indices to X.
        
        num_points = len(self.data)
        if num_points < 2:
            self.delete("line")
            return

        # Always map the last 60 points (or whatever maxlen is) to the width
        # If we have 60 points, index 0 is at left, index 59 is at right.
        # If we have 10 points, index 0 is at left, index 9 is at 10/60th of width? 
        # No, usually we want the graph to "fill" as it goes or "scroll".
        # Let's do "fill then scroll".
        
        max_capacity = self.data.maxlen if self.data.maxlen else 60
        
        step_x = available_width / (max_capacity - 1)
        
        for i, value in enumerate(self.data):
            # If we are not full yet, should we stretch or just fill part?
            # "Scroll" effect: Newest data is always at right edge?
            # Or "Fill" effect: Newest data moves to right?
            # Let's do "Newest at right edge" (Scroll)
            # But if we have few points, they should be at the right? 
            # Standard monitoring graphs:
            # Time 0: Point at left.
            # Time 10: Point at 10s mark.
            # Time 60: Point at right edge.
            # Time 61: Shift left.
            
            # So:
            # x = padding_left + (i * step_x) -> This fills from left.
            # When full, i=0 is pushed out.
            
            # Wait, deque pops from left. So self.data[0] is the oldest.
            # So self.data[0] should be at the left.
            # self.data[-1] (newest) should be at the right?
            # Yes, if full.
            
            # If not full (e.g. 10 points), and max capacity is 60.
            # Should self.data[0] be at left, and self.data[9] be at 1/6th?
            # Yes, that looks like a history graph building up.
            
            x = self.padding_left + (i * step_x)
            y = self._map_y(value)
            points.extend([x, y])
            
        if self.line_id:
            self.coords(self.line_id, *points)
        else:
            self.line_id = self.create_line(
                *points, 
                fill=AppColors.ACCENT, 
                width=2, 
                smooth=True,
                tags="line"
            )

    def clear(self):
        self.data.clear()
        self.delete("line")
        self.line_id = None
