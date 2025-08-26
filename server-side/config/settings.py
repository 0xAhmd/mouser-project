"""
Configuration settings for the mouse/keyboard server
"""

class Config:
    """Application configuration"""
    HOST = '0.0.0.0'
    PORT = 8080
    DEBUG = False
    VERSION = "2.0-enhanced"
    
    # Gesture timing settings
    SCROLL_COOLDOWN = 0.05  # 50ms between scroll events
    ZOOM_COOLDOWN = 0.1     # 100ms between zoom events
    
    # Gesture sensitivity
    SCROLL_SENSITIVITY = 0.5
    ZOOM_SENSITIVITY = 0.3
    TEXT_SELECTION_PRECISION = 0.3
    
    # Limits
    MAX_SCROLL_AMOUNT = 5
    MAX_ZOOM_AMOUNT = 3
    KEY_PRESS_DELAY = 0.01
    KEY_COMBINATION_DELAY = 0.05