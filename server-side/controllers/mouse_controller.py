"""
Mouse control functionality
"""

import time
import logging
from pynput import mouse
from pynput.mouse import Button
from config.settings import Config

logger = logging.getLogger(__name__)

class MouseController:
    """Handles all mouse-related operations"""
    
    def __init__(self):
        self.controller = mouse.Controller()
    
    def move(self, dx, dy):
        """Move mouse cursor by delta values"""
        current_x, current_y = self.controller.position
        new_x = current_x + dx
        new_y = current_y + dy
        self.controller.position = (new_x, new_y)
    
    def left_click(self):
        """Perform left mouse click"""
        self.controller.click(Button.left, 1)
    
    def right_click(self):
        """Perform right mouse click"""
        self.controller.click(Button.right, 1)
    
    def double_click(self):
        """Perform double click"""
        self.controller.click(Button.left, 2)
    
    def middle_click(self):
        """Perform middle mouse button click"""
        self.controller.click(Button.middle, 1)
    
    def scroll_vertical(self, direction, amount=1):
        """Perform vertical scrolling"""
        amount = min(amount, Config.MAX_SCROLL_AMOUNT)
        for _ in range(amount):
            if direction == 'up':
                self.controller.scroll(0, 1)
            else:
                self.controller.scroll(0, -1)
    
    def scroll_horizontal(self, direction, amount=1):
        """Perform horizontal scrolling"""
        try:
            if direction == 'left':
                self.controller.scroll(-amount, 0)
            else:
                self.controller.scroll(amount, 0)
            return True
        except Exception as e:
            logger.warning(f"Horizontal scroll not supported: {e}")
            return False
    
    def press_button(self, button):
        """Press and hold mouse button"""
        if button == 'left':
            self.controller.press(Button.left)
        elif button == 'right':
            self.controller.press(Button.right)
        elif button == 'middle':
            self.controller.press(Button.middle)
    
    def release_button(self, button):
        """Release mouse button"""
        if button == 'left':
            self.controller.release(Button.left)
        elif button == 'right':
            self.controller.release(Button.right)
        elif button == 'middle':
            self.controller.release(Button.middle)
    
    def get_position(self):
        """Get current mouse position"""
        return self.controller.position
    
    def set_position(self, x, y):
        """Set absolute mouse position"""
        self.controller.position = (x, y)