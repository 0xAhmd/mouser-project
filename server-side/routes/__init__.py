"""
Routes package for API endpoints
"""

from .mouse_routes import mouse_bp
from .keyboard_routes import keyboard_bp
from .gesture_routes import gesture_bp
from .status_routes import status_bp

__all__ = ['mouse_bp', 'keyboard_bp', 'gesture_bp', 'status_bp']