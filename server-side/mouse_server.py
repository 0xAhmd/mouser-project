#!/usr/bin/env python3
"""
Enhanced PC Mouse & Keyboard Control Server for Ubuntu
Receives commands from Flutter mobile app and controls the mouse and keyboard
Now supports advanced gestures: two-finger scrolling, pinch to zoom, text selection, etc.

Requirements:
pip install flask pynput

Run with: python3 enhanced_mouse_keyboard_server.py
"""

from flask import Flask, request, jsonify
import json
from pynput.mouse import Button, Listener as MouseListener
from pynput import mouse, keyboard
from pynput.keyboard import Key, KeyCode
import threading
import socket
import sys
import time
import logging

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Controllers
mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()

# State management for gestures
class GestureState:
    def __init__(self):
        self.is_dragging = False
        self.is_text_selecting = False
        self.drag_start_position = None
        self.last_scroll_time = 0
        self.scroll_cooldown = 0.05  # 50ms cooldown between scroll events
        self.zoom_cooldown = 0.1     # 100ms cooldown between zoom events
        self.last_zoom_time = 0
        
    def reset_drag(self):
        self.is_dragging = False
        self.is_text_selecting = False
        self.drag_start_position = None

gesture_state = GestureState()

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def get_key_from_string(key_string):
    """Convert string to pynput key - Enhanced with more keys"""
    # Handle arrow keys from Flutter format
    if key_string.endswith('_arrow'):
        direction = key_string.replace('_arrow', '')
        arrow_keys = {
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right
        }
        return arrow_keys.get(direction, Key.up)
    
    # Enhanced special keys mapping
    special_keys = {
        'return': Key.enter,
        'Return': Key.enter,
        'enter': Key.enter,
        'Enter': Key.enter,
        'space': Key.space,
        'Space': Key.space,
        'backspace': Key.backspace,
        'BackSpace': Key.backspace,
        'delete': Key.delete,
        'Delete': Key.delete,
        'tab': Key.tab,
        'Tab': Key.tab,
        'escape': Key.esc,
        'Escape': Key.esc,
        'esc': Key.esc,
        'shift': Key.shift,
        'Shift': Key.shift,
        'ctrl': Key.ctrl,
        'Ctrl': Key.ctrl,
        'control': Key.ctrl,
        'Control': Key.ctrl,
        'alt': Key.alt,
        'Alt': Key.alt,
        'cmd': Key.cmd,
        'Cmd': Key.cmd,
        'super': Key.cmd,
        'Super': Key.cmd,
        'win': Key.cmd,  # Windows key maps to cmd
        'windows': Key.cmd,
        'up': Key.up,
        'down': Key.down,
        'left': Key.left,
        'right': Key.right,
        'home': Key.home,
        'Home': Key.home,
        'end': Key.end,
        'End': Key.end,
        'page_up': Key.page_up,
        'PageUp': Key.page_up,
        'page_down': Key.page_down,
        'PageDown': Key.page_down,
        'caps_lock': Key.caps_lock,
        'CapsLock': Key.caps_lock,
        'num_lock': Key.num_lock,
        'NumLock': Key.num_lock,
        'scroll_lock': Key.scroll_lock,
        'ScrollLock': Key.scroll_lock,
        'insert': Key.insert,
        'Insert': Key.insert,
        'print_screen': Key.print_screen,
        'PrintScreen': Key.print_screen,
        'pause': Key.pause,
        'Pause': Key.pause,
        'menu': Key.menu,
        'Menu': Key.menu,
        # Function keys
        'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
        'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
        'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
        'F1': Key.f1, 'F2': Key.f2, 'F3': Key.f3, 'F4': Key.f4,
        'F5': Key.f5, 'F6': Key.f6, 'F7': Key.f7, 'F8': Key.f8,
        'F9': Key.f9, 'F10': Key.f10, 'F11': Key.f11, 'F12': Key.f12,
        # Number pad
        'num_0': KeyCode.from_char('0'),
        'num_1': KeyCode.from_char('1'),
        'num_2': KeyCode.from_char('2'),
        'num_3': KeyCode.from_char('3'),
        'num_4': KeyCode.from_char('4'),
        'num_5': KeyCode.from_char('5'),
        'num_6': KeyCode.from_char('6'),
        'num_7': KeyCode.from_char('7'),
        'num_8': KeyCode.from_char('8'),
        'num_9': KeyCode.from_char('9'),
        # Special characters
        '+': KeyCode.from_char('+'),
        '-': KeyCode.from_char('-'),
        '*': KeyCode.from_char('*'),
        '/': KeyCode.from_char('/'),
        '=': KeyCode.from_char('='),
        '0': KeyCode.from_char('0'),
    }
    
    # Check if it's a special key
    if key_string in special_keys:
        return special_keys[key_string]
    else:
        # Regular character - handle single characters
        if len(key_string) == 1:
            return KeyCode.from_char(key_string)
        else:
            # Try to match as special key case-insensitively
            lower_key = key_string.lower()
            if lower_key in special_keys:
                return special_keys[lower_key]
            # Default to first character if unknown
            return KeyCode.from_char(key_string[0])

def safe_scroll(direction, amount=1):
    """Safely perform scroll with cooldown to prevent overwhelming the system"""
    current_time = time.time()
    if current_time - gesture_state.last_scroll_time < gesture_state.scroll_cooldown:
        return False
    
    try:
        for _ in range(min(amount, 3)):  # Limit to max 3 scroll events per call
            if direction == 'up':
                mouse_controller.scroll(0, 1)
            else:
                mouse_controller.scroll(0, -1)
        gesture_state.last_scroll_time = current_time
        return True
    except Exception as e:
        logger.error(f"Error during scroll: {e}")
        return False

def safe_zoom(zoom_in=True, amount=1):
    """Safely perform zoom with Ctrl+Scroll with cooldown"""
    current_time = time.time()
    if current_time - gesture_state.last_zoom_time < gesture_state.zoom_cooldown:
        return False
    
    try:
        # Hold Ctrl key
        keyboard_controller.press(Key.ctrl)
        time.sleep(0.01)  # Small delay to ensure key is registered
        
        # Perform scroll while holding Ctrl
        for _ in range(min(amount, 2)):  # Limit zoom amount
            if zoom_in:
                mouse_controller.scroll(0, 1)
            else:
                mouse_controller.scroll(0, -1)
            time.sleep(0.02)  # Small delay between scroll events
        
        # Release Ctrl key
        keyboard_controller.release(Key.ctrl)
        gesture_state.last_zoom_time = current_time
        return True
    except Exception as e:
        logger.error(f"Error during zoom: {e}")
        # Ensure Ctrl is released even if error occurs
        try:
            keyboard_controller.release(Key.ctrl)
        except:
            pass
        return False

@app.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Enhanced server is running"})

@app.route('/mouse', methods=['POST'])
def handle_mouse_command():
    """Handle enhanced mouse commands from mobile app"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "error": "No JSON data provided"}), 400
            
        action = data.get('action')
        command_data = data.get('data', {})
        
        logger.info(f"Received mouse command: {action}, data: {command_data}")
        
        if action == 'move':
            # Move mouse cursor
            dx = command_data.get('dx', 0)
            dy = command_data.get('dy', 0)
            
            # Get current position and add delta
            current_x, current_y = mouse_controller.position
            new_x = current_x + dx
            new_y = current_y + dy
            
            mouse_controller.position = (new_x, new_y)
            
        elif action == 'left_click':
            mouse_controller.click(Button.left, 1)
            
        elif action == 'right_click':
            mouse_controller.click(Button.right, 1)
            
        elif action == 'double_click':
            mouse_controller.click(Button.left, 2)
            
        elif action == 'scroll_up':
            amount = command_data.get('amount', 1)
            safe_scroll('up', amount)
            
        elif action == 'scroll_down':
            amount = command_data.get('amount', 1)
            safe_scroll('down', amount)
            
        elif action == 'smooth_scroll':
            # Enhanced smooth scrolling for two-finger gestures
            direction = command_data.get('direction', 'up')
            intensity = command_data.get('intensity', 1)
            
            # Convert intensity to scroll amount (1-5 scrolls)
            scroll_amount = max(1, min(5, int(abs(intensity * 3))))
            safe_scroll(direction, scroll_amount)
            
        elif action == 'pinch_zoom':
            # Handle pinch to zoom gesture
            scale_delta = command_data.get('scale_delta', 0)
            zoom_in = scale_delta > 0
            zoom_amount = max(1, min(3, int(abs(scale_delta * 5))))
            
            safe_zoom(zoom_in, zoom_amount)
            
        elif action == 'drag_start':
            # Start drag operation (for text selection) - ONLY for single finger
            finger_count = command_data.get('finger_count', 1)
            
            # Only allow text selection with single finger
            if finger_count == 1:
                current_x, current_y = mouse_controller.position
                gesture_state.drag_start_position = (current_x, current_y)
                gesture_state.is_dragging = True
                
                # Check if this is for text selection
                selection_mode = command_data.get('selection_mode', False)
                if selection_mode:
                    gesture_state.is_text_selecting = True
                
                mouse_controller.press(Button.left)
            else:
                # Ignore drag start for multi-finger gestures
                logger.info(f"Ignoring drag_start for {finger_count} fingers - preserving scroll functionality")
            
        elif action == 'drag_update':
            # Update drag position during text selection
            if gesture_state.is_dragging:
                dx = command_data.get('dx', 0)
                dy = command_data.get('dy', 0)
                
                current_x, current_y = mouse_controller.position
                new_x = current_x + dx
                new_y = current_y + dy
                
                mouse_controller.position = (new_x, new_y)
            
        elif action == 'drag_end':
            # End drag operation
            if gesture_state.is_dragging:
                mouse_controller.release(Button.left)
                gesture_state.reset_drag()
            
        elif action == 'middle_click':
            # Middle mouse button click
            mouse_controller.click(Button.middle, 1)
            
        elif action == 'scroll_horizontal':
            # Horizontal scrolling (if supported)
            direction = command_data.get('direction', 'left')
            amount = command_data.get('amount', 1)
            
            try:
                if direction == 'left':
                    mouse_controller.scroll(-amount, 0)
                else:
                    mouse_controller.scroll(amount, 0)
            except:
                # Fallback to left/right arrow keys if horizontal scroll not supported
                key = Key.left if direction == 'left' else Key.right
                for _ in range(amount):
                    keyboard_controller.press(key)
                    keyboard_controller.release(key)
            
        else:
            return jsonify({"status": "error", "error": f"Unknown mouse action: {action}"}), 400
            
        return jsonify({"status": "success", "message": f"Mouse {action} executed"})
        
    except Exception as e:
        logger.error(f"Error handling mouse command: {e}")
        # Reset gesture state on error
        gesture_state.reset_drag()
        try:
            keyboard_controller.release(Key.ctrl)
        except:
            pass
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/keyboard', methods=['POST'])
def handle_keyboard_command():
    """Handle enhanced keyboard commands from mobile app"""
    try:
        if not request.is_json:
            return jsonify({"status": "error", "error": "Request must be JSON"}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "error": "No JSON data provided"}), 400
            
        action = data.get('action')
        command_data = data.get('data', {})
        
        logger.info(f"Received keyboard command: {action}, data: {command_data}")
        
        if action == 'type':
            # Type text
            text = command_data.get('text', '')
            if text:
                keyboard_controller.type(text)
            
        elif action == 'key':
            # Press and release a single key with enhanced modifier support
            key_string = command_data.get('key', '')
            shift = command_data.get('shift', False)
            ctrl = command_data.get('ctrl', False)
            alt = command_data.get('alt', False)
            cmd = command_data.get('cmd', False)
            
            if not key_string:
                return jsonify({"status": "error", "error": "No key provided"}), 400
            
            logger.info(f"Processing key: {key_string}, modifiers: shift={shift}, ctrl={ctrl}, alt={alt}, cmd={cmd}")
            
            # Handle modifier combinations
            modifiers = []
            if ctrl:
                modifiers.append(Key.ctrl)
            if alt:
                modifiers.append(Key.alt)
            if shift:
                modifiers.append(Key.shift)
            if cmd:
                modifiers.append(Key.cmd)
            
            try:
                key = get_key_from_string(key_string)
                
                # Press modifiers
                for mod in modifiers:
                    keyboard_controller.press(mod)
                    time.sleep(0.01)
                
                # Press and release the main key
                keyboard_controller.press(key)
                time.sleep(0.02)
                keyboard_controller.release(key)
                
                # Release modifiers in reverse order
                for mod in reversed(modifiers):
                    keyboard_controller.release(mod)
                    time.sleep(0.01)
                    
            except Exception as key_error:
                logger.error(f"Error processing key '{key_string}': {key_error}")
                # Clean up any pressed modifiers
                for mod in modifiers:
                    try:
                        keyboard_controller.release(mod)
                    except:
                        pass
                return jsonify({"status": "error", "error": f"Invalid key: {key_string}"}), 400
                
        elif action == 'key_press':
            # Legacy support - Press and release a single key
            key_string = command_data.get('key', '')
            if key_string:
                key = get_key_from_string(key_string)
                keyboard_controller.press(key)
                keyboard_controller.release(key)
            
        elif action == 'key_combination':
            # Handle key combinations like Ctrl+C, Alt+Tab, etc.
            keys = command_data.get('keys', [])
            if not keys:
                return jsonify({"status": "error", "error": "No keys provided for combination"}), 400
            
            # Convert strings to keys
            key_objects = []
            try:
                key_objects = [get_key_from_string(k) for k in keys]
            except Exception as e:
                return jsonify({"status": "error", "error": f"Invalid key in combination: {e}"}), 400
            
            # Press all keys with small delays
            for key in key_objects:
                keyboard_controller.press(key)
                time.sleep(0.01)
            
            # Hold for a moment
            time.sleep(0.05)
            
            # Release all keys in reverse order
            for key in reversed(key_objects):
                keyboard_controller.release(key)
                time.sleep(0.01)
                
        elif action == 'key_hold_start':
            # Start holding a key
            key_string = command_data.get('key', '')
            if key_string:
                key = get_key_from_string(key_string)
                keyboard_controller.press(key)
            
        elif action == 'key_hold_end':
            # Stop holding a key
            key_string = command_data.get('key', '')
            if key_string:
                key = get_key_from_string(key_string)
                keyboard_controller.release(key)
        
        elif action == 'enhanced_shortcut':
            # Handle enhanced shortcuts for text manipulation
            shortcut_type = command_data.get('type', '')
            
            shortcut_map = {
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
            
            if shortcut_type in shortcut_map:
                keys = shortcut_map[shortcut_type]
                key_objects = [get_key_from_string(k) for k in keys]
                
                # Execute shortcut
                for key in key_objects:
                    keyboard_controller.press(key)
                    time.sleep(0.01)
                
                time.sleep(0.05)
                
                for key in reversed(key_objects):
                    keyboard_controller.release(key)
                    time.sleep(0.01)
            else:
                return jsonify({"status": "error", "error": f"Unknown shortcut: {shortcut_type}"}), 400
            
        else:
            return jsonify({"status": "error", "error": f"Unknown keyboard action: {action}"}), 400
            
        return jsonify({"status": "success", "message": f"Keyboard {action} executed"})
        
    except Exception as e:
        logger.error(f"Error handling keyboard command: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/gesture', methods=['POST'])
def handle_gesture_command():
    """Handle complex gesture commands"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "error": "No JSON data provided"}), 400
            
        gesture_type = data.get('type')
        gesture_data = data.get('data', {})
        
        logger.info(f"Received gesture command: {gesture_type}, data: {gesture_data}")
        
        if gesture_type == 'two_finger_scroll':
            # Enhanced two-finger scrolling
            delta_y = gesture_data.get('deltaY', 0)
            sensitivity = gesture_data.get('sensitivity', 0.5)
            
            # Convert delta to scroll direction and amount
            scroll_amount = abs(delta_y * sensitivity)
            if scroll_amount > 0.1:  # Threshold to avoid micro-movements
                direction = 'up' if delta_y < 0 else 'down'  # Natural scrolling
                amount = max(1, min(5, int(scroll_amount * 10)))
                safe_scroll(direction, amount)
            
        elif gesture_type == 'pinch_zoom':
            # Enhanced pinch to zoom
            scale_delta = gesture_data.get('scaleDelta', 0)
            sensitivity = gesture_data.get('sensitivity', 0.3)
            
            adjusted_delta = scale_delta * sensitivity
            if abs(adjusted_delta) > 0.01:  # Threshold to avoid micro-movements
                zoom_in = adjusted_delta > 0
                amount = max(1, min(3, int(abs(adjusted_delta) * 20)))
                safe_zoom(zoom_in, amount)
        
        elif gesture_type == 'text_selection':
            # Enhanced text selection gesture - ONLY for single finger
            phase = gesture_data.get('phase', 'start')  # start, update, end
            finger_count = gesture_data.get('finger_count', 1)
            
            # Only process text selection for single finger
            if finger_count != 1:
                logger.info(f"Ignoring text selection for {finger_count} fingers")
                return jsonify({"status": "ignored", "message": f"Text selection only works with single finger, received {finger_count} fingers"})
            
            if phase == 'start':
                current_x, current_y = mouse_controller.position
                gesture_state.drag_start_position = (current_x, current_y)
                gesture_state.is_text_selecting = True
                gesture_state.is_dragging = True
                mouse_controller.press(Button.left)
                
            elif phase == 'update':
                if gesture_state.is_text_selecting and gesture_state.is_dragging:
                    dx = gesture_data.get('dx', 0)
                    dy = gesture_data.get('dy', 0)
                    
                    # Slower movement for precision
                    precision_factor = 0.3
                    current_x, current_y = mouse_controller.position
                    new_x = current_x + (dx * precision_factor)
                    new_y = current_y + (dy * precision_factor)
                    
                    mouse_controller.position = (new_x, new_y)
                    
            elif phase == 'end':
                if gesture_state.is_text_selecting:
                    mouse_controller.release(Button.left)
                    gesture_state.reset_drag()
        
        elif gesture_type == 'three_finger_swipe':
            # Three-finger gestures for desktop navigation
            direction = gesture_data.get('direction', 'up')
            
            if direction == 'up':
                # Show all windows / Mission Control (macOS) or Overview (Linux)
                keyboard_controller.press(Key.cmd)
                keyboard_controller.press(Key.f3)
                time.sleep(0.1)
                keyboard_controller.release(Key.f3)
                keyboard_controller.release(Key.cmd)
                
            elif direction == 'down':
                # Show desktop
                keyboard_controller.press(Key.cmd)
                keyboard_controller.press(Key.f11)
                time.sleep(0.1)
                keyboard_controller.release(Key.f11)
                keyboard_controller.release(Key.cmd)
                
            elif direction == 'left':
                # Switch to next desktop/workspace
                keyboard_controller.press(Key.ctrl)
                keyboard_controller.press(Key.alt)
                keyboard_controller.press(Key.right)
                time.sleep(0.1)
                keyboard_controller.release(Key.right)
                keyboard_controller.release(Key.alt)
                keyboard_controller.release(Key.ctrl)
                
            elif direction == 'right':
                # Switch to previous desktop/workspace
                keyboard_controller.press(Key.ctrl)
                keyboard_controller.press(Key.alt)
                keyboard_controller.press(Key.left)
                time.sleep(0.1)
                keyboard_controller.release(Key.left)
                keyboard_controller.release(Key.alt)
                keyboard_controller.release(Key.ctrl)
        
        else:
            return jsonify({"status": "error", "error": f"Unknown gesture type: {gesture_type}"}), 400
            
        return jsonify({"status": "success", "message": f"Gesture {gesture_type} executed"})
        
    except Exception as e:
        logger.error(f"Error handling gesture command: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get current mouse position and server status with enhanced info"""
    x, y = mouse_controller.position
    return jsonify({
        "status": "running",
        "version": "2.0-enhanced",
        "mouse_position": {"x": x, "y": y},
        "server_ip": get_local_ip(),
        "features": [
            "mouse", "keyboard", "enhanced_gestures", 
            "two_finger_scroll", "pinch_zoom", "text_selection",
            "three_finger_swipe", "smooth_scrolling"
        ],
        "gesture_state": {
            "is_dragging": gesture_state.is_dragging,
            "is_text_selecting": gesture_state.is_text_selecting
        }
    })

@app.route('/reset', methods=['POST'])
def reset_state():
    """Reset all gesture states - useful for recovery"""
    try:
        gesture_state.reset_drag()
        
        # Release any potentially stuck keys
        for key in [Key.ctrl, Key.alt, Key.shift, Key.cmd]:
            try:
                keyboard_controller.release(key)
            except:
                pass
        
        # Release mouse buttons
        try:
            mouse_controller.release(Button.left)
            mouse_controller.release(Button.right)
            mouse_controller.release(Button.middle)
        except:
            pass
            
        return jsonify({"status": "success", "message": "All states reset"})
        
    except Exception as e:
        logger.error(f"Error resetting state: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

def print_server_info():
    """Print enhanced server information"""
    local_ip = get_local_ip()
    print("=" * 70)
    print("🚀 ENHANCED PC Mouse & Keyboard Control Server Starting...")
    print("=" * 70)
    print(f"📡 Server IP: {local_ip}")
    print(f"🔌 Server Port: 8080")
    print(f"📱 Mobile App Connection URL: http://{local_ip}:8080")
    print("=" * 70)
    print("✨ Enhanced Features:")
    print("• 🖱️  Advanced Mouse Control (move, click, scroll, drag)")
    print("• ⌨️  Enhanced Keyboard Control (type, combinations, shortcuts)")
    print("• 👆 Two-Finger Scrolling (smooth & responsive)")
    print("• 🤏 Pinch to Zoom (with Ctrl+Scroll)")
    print("• 📝 Text Selection (long-press + drag)")
    print("• 👇 Right-Click (two-finger tap)")
    print("• 🖐️  Three-Finger Desktop Navigation")
    print("• 🔄 Smart Gesture Recognition")
    print("=" * 70)
    print("🌐 API Endpoints:")
    print("• POST /mouse - Mouse commands")
    print("• POST /keyboard - Keyboard commands") 
    print("• POST /gesture - Advanced gesture commands")
    print("• GET /status - Server status & gesture state")
    print("• GET /ping - Health check")
    print("• POST /reset - Reset all states")
    print("=" * 70)
    print("📋 Setup Instructions:")
    print("1. ✅ Make sure your phone and PC are on the same WiFi network")
    print(f"2. 📲 Enter this IP in your mobile app: {local_ip}")
    print("3. 🔗 Tap 'Connect' in the mobile app")
    print("4. 🎮 Use enhanced gestures on your phone!")
    print("=" * 70)
    print("🎯 Gesture Guide:")
    print("• One finger: Move cursor, tap to click, LONG PRESS for text selection")
    print("• Two fingers: Scroll vertically, pinch to zoom, tap for right-click")
    print("• Long press (1 finger only): Start text selection mode")
    print("• Three fingers: Desktop/workspace navigation")
    print("=" * 70)
    print("⚠️  Press Ctrl+C to stop the server")
    print("=" * 70)

if __name__ == '__main__':
    print_server_info()
    
    try:
        # Run Flask app with enhanced settings
        app.run(
            host='0.0.0.0',  # Allow connections from any IP
            port=8080,
            debug=False,  # Disable debug mode for better performance
            threaded=True,
            use_reloader=False  # Disable reloader to prevent issues
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down enhanced server...")
        # Clean up any remaining states
        gesture_state.reset_drag()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
