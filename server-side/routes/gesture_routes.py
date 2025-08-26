"""
Advanced gesture control routes
"""

import logging
import time
from flask import Blueprint, request, jsonify
from controllers.mouse_controller import MouseController
from controllers.keyboard_controller import KeyboardController
from models.gesture_state import GestureState
from config.settings import Config
from pynput.keyboard import Key

logger = logging.getLogger(__name__)

gesture_bp = Blueprint('gesture', __name__)

# Global instances
mouse_controller = MouseController()
keyboard_controller = KeyboardController()
gesture_state = GestureState()

def safe_scroll_gesture(direction, amount):
    """Safely perform scroll for gestures"""
    if not gesture_state.can_scroll():
        return False
    
    try:
        mouse_controller.scroll_vertical(direction, amount)
        gesture_state.update_scroll_time()
        return True
    except Exception as e:
        logger.error(f"Error during gesture scroll: {e}")
        return False

def safe_zoom_gesture(zoom_in, amount):
    """Safely perform zoom for gestures"""
    if not gesture_state.can_zoom():
        return False
    
    try:
        if keyboard_controller.zoom_with_ctrl():
            for _ in range(amount):
                mouse_controller.scroll_vertical('up' if zoom_in else 'down', 1)
                time.sleep(0.02)
            keyboard_controller.release_ctrl_for_zoom()
            gesture_state.update_zoom_time()
            return True
        return False
    except Exception as e:
        logger.error(f"Error during gesture zoom: {e}")
        keyboard_controller.release_ctrl_for_zoom()
        return False

@gesture_bp.route('/gesture', methods=['POST'])
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
            delta_y = gesture_data.get('deltaY', 0)
            sensitivity = gesture_data.get('sensitivity', Config.SCROLL_SENSITIVITY)
            
            scroll_amount = abs(delta_y * sensitivity)
            if scroll_amount > 0.1:  # Threshold to avoid micro-movements
                direction = 'up' if delta_y < 0 else 'down'  # Natural scrolling
                amount = max(1, min(Config.MAX_SCROLL_AMOUNT, int(scroll_amount * 10)))
                safe_scroll_gesture(direction, amount)
            
        elif gesture_type == 'pinch_zoom':
            scale_delta = gesture_data.get('scaleDelta', 0)
            sensitivity = gesture_data.get('sensitivity', Config.ZOOM_SENSITIVITY)
            
            adjusted_delta = scale_delta * sensitivity
            if abs(adjusted_delta) > 0.01:  # Threshold to avoid micro-movements
                zoom_in = adjusted_delta > 0
                amount = max(1, min(Config.MAX_ZOOM_AMOUNT, int(abs(adjusted_delta) * 20)))
                safe_zoom_gesture(zoom_in, amount)
        
        elif gesture_type == 'text_selection':
            phase = gesture_data.get('phase', 'start')  # start, update, end
            finger_count = gesture_data.get('finger_count', 1)
            
            # Only process text selection for single finger
            if finger_count != 1:
                logger.info(f"Ignoring text selection for {finger_count} fingers")
                return jsonify({"status": "ignored", "message": f"Text selection only works with single finger, received {finger_count} fingers"})
            
            if phase == 'start':
                current_pos = mouse_controller.get_position()
                gesture_state.start_drag(current_pos, True)
                mouse_controller.press_button('left')
                
            elif phase == 'update':
                if gesture_state.is_text_selecting and gesture_state.is_dragging:
                    dx = gesture_data.get('dx', 0)
                    dy = gesture_data.get('dy', 0)
                    
                    # Apply precision factor for text selection
                    precision_factor = Config.TEXT_SELECTION_PRECISION
                    adjusted_dx = dx * precision_factor
                    adjusted_dy = dy * precision_factor
                    
                    mouse_controller.move(adjusted_dx, adjusted_dy)
                    
            elif phase == 'end':
                if gesture_state.is_text_selecting:
                    mouse_controller.release_button('left')
                    gesture_state.reset_drag()
        
        elif gesture_type == 'three_finger_swipe':
            direction = gesture_data.get('direction', 'up')
            
            if direction == 'up':
                # Show all windows / Mission Control
                keyboard_controller.press_key_combination(['cmd', 'f3'])
                
            elif direction == 'down':
                # Show desktop
                keyboard_controller.press_key_combination(['cmd', 'f11'])
                
            elif direction == 'left':
                # Switch to next desktop/workspace
                keyboard_controller.press_key_combination(['ctrl', 'alt', 'right'])
                
            elif direction == 'right':
                # Switch to previous desktop/workspace
                keyboard_controller.press_key_combination(['ctrl', 'alt', 'left'])
        
        else:
            return jsonify({"status": "error", "error": f"Unknown gesture type: {gesture_type}"}), 400
            
        return jsonify({"status": "success", "message": f"Gesture {gesture_type} executed"})
        
    except Exception as e:
        logger.error(f"Error handling gesture command: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500