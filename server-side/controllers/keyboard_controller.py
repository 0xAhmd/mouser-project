"""
Keyboard control functionality
"""

import time
import logging
from pynput import keyboard
from pynput.keyboard import Key
from utils.key_mapper import get_key_from_string
from config.settings import Config

logger = logging.getLogger(__name__)

class KeyboardController:
    """Handles all keyboard-related operations"""
    
    def __init__(self):
        self.controller = keyboard.Controller()
        self.shortcut_map = {
            'select_all': ['ctrl', 'a'],
            'copy': ['ctrl', 'c'],
            'paste': ['ctrl', 'v'],
            'cut': ['ctrl', 'x'],
            'undo': ['ctrl', 'z'],
            'redo': ['ctrl', 'y'],
            'find': ['ctrl', 'f'],
            'replace': ['ctrl', 'h'],
            'save': ['ctrl', 's'],
            'new': ['ctrl', 'n'],
            'open': ['ctrl', 'o'],
            'print': ['ctrl', 'p'],
            'zoom_in': ['ctrl', '+'],
            'zoom_out': ['ctrl', '-'],
            'zoom_reset': ['ctrl', '0'],
            'refresh': ['ctrl', 'r'],
            'home': ['ctrl', 'Home'],
            'end': ['ctrl', 'End'],
        }
    
    def type_text(self, text):
        """Type the given text"""
        if text:
            self.controller.type(text)
    
    def press_key(self, key_string, modifiers=None):
        """Press and release a key with optional modifiers"""
        if modifiers is None:
            modifiers = {}
        
        # Build modifier list
        mod_keys = []
        if modifiers.get('ctrl', False):
            mod_keys.append(Key.ctrl)
        if modifiers.get('alt', False):
            mod_keys.append(Key.alt)
        if modifiers.get('shift', False):
            mod_keys.append(Key.shift)
        if modifiers.get('cmd', False):
            mod_keys.append(Key.cmd)
        
        try:
            key = get_key_from_string(key_string)
            
            # Press modifiers
            for mod in mod_keys:
                self.controller.press(mod)
                time.sleep(Config.KEY_PRESS_DELAY)
            
            # Press and release main key
            self.controller.press(key)
            time.sleep(Config.KEY_PRESS_DELAY * 2)
            self.controller.release(key)
            
            # Release modifiers in reverse order
            for mod in reversed(mod_keys):
                self.controller.release(mod)
                time.sleep(Config.KEY_PRESS_DELAY)
                
        except Exception as e:
            logger.error(f"Error pressing key '{key_string}': {e}")
            # Clean up any pressed modifiers
            for mod in mod_keys:
                try:
                    self.controller.release(mod)
                except:
                    pass
            raise
    
    def press_key_combination(self, keys):
        """Press a combination of keys simultaneously"""
        if not keys:
            return
        
        # Convert strings to key objects
        key_objects = [get_key_from_string(k) for k in keys]
        
        # Press all keys
        for key in key_objects:
            self.controller.press(key)
            time.sleep(Config.KEY_PRESS_DELAY)
        
        # Hold for a moment
        time.sleep(Config.KEY_COMBINATION_DELAY)
        
        # Release all keys in reverse order
        for key in reversed(key_objects):
            self.controller.release(key)
            time.sleep(Config.KEY_PRESS_DELAY)
    
    def hold_key(self, key_string):
        """Start holding a key"""
        key = get_key_from_string(key_string)
        self.controller.press(key)
    
    def release_key(self, key_string):
        """Stop holding a key"""
        key = get_key_from_string(key_string)
        self.controller.release(key)
    
    def execute_shortcut(self, shortcut_type):
        """Execute a predefined shortcut"""
        if shortcut_type not in self.shortcut_map:
            raise ValueError(f"Unknown shortcut: {shortcut_type}")
        
        keys = self.shortcut_map[shortcut_type]
        self.press_key_combination(keys)
    
    def zoom_with_ctrl(self, zoom_in=True, amount=1):
        """Perform zoom using Ctrl+Scroll simulation"""
        try:
            # Hold Ctrl key
            self.controller.press(Key.ctrl)
            time.sleep(Config.KEY_PRESS_DELAY)
            return True
            
        except Exception as e:
            logger.error(f"Error during zoom setup: {e}")
            try:
                self.controller.release(Key.ctrl)
            except:
                pass
            return False
    
    def release_ctrl_for_zoom(self):
        """Release Ctrl key after zoom operation"""
        try:
            self.controller.release(Key.ctrl)
        except Exception as e:
            logger.error(f"Error releasing Ctrl: {e}")
    
    def release_all_keys(self):
        """Emergency release of all modifier keys"""
        modifiers = [Key.ctrl, Key.alt, Key.shift, Key.cmd]
        for key in modifiers:
            try:
                self.controller.release(key)
            except:
                pass