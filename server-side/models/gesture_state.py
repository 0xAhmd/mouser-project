"""
Gesture state management
"""

import time
from config.settings import Config

class GestureState:
    """Manages state for various gestures and interactions"""
    
    def __init__(self):
        self.is_dragging = False
        self.is_text_selecting = False
        self.drag_start_position = None
        self.last_scroll_time = 0
        self.scroll_cooldown = Config.SCROLL_COOLDOWN
        self.zoom_cooldown = Config.ZOOM_COOLDOWN
        self.last_zoom_time = 0
    
    def reset_drag(self):
        """Reset all drag-related states"""
        self.is_dragging = False
        self.is_text_selecting = False
        self.drag_start_position = None
    
    def can_scroll(self):
        """Check if enough time has passed since last scroll"""
        current_time = time.time()
        return current_time - self.last_scroll_time >= self.scroll_cooldown
    
    def can_zoom(self):
        """Check if enough time has passed since last zoom"""
        current_time = time.time()
        return current_time - self.last_zoom_time >= self.zoom_cooldown
    
    def update_scroll_time(self):
        """Update last scroll time"""
        self.last_scroll_time = time.time()
    
    def update_zoom_time(self):
        """Update last zoom time"""
        self.last_zoom_time = time.time()
    
    def start_drag(self, position, is_text_selection=False):
        """Start a drag operation"""
        self.drag_start_position = position
        self.is_dragging = True
        self.is_text_selecting = is_text_selection
    
    def get_state_dict(self):
        """Get current state as dictionary"""
        return {
            "is_dragging": self.is_dragging,
            "is_text_selecting": self.is_text_selecting,
            "has_drag_position": self.drag_start_position is not None
        }