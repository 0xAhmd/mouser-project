"""
Mouse control routes
"""

import logging
from flask import Blueprint, request, jsonify
from controllers.mouse_controller import MouseController
from controllers.keyboard_controller import KeyboardController
from models.gesture_state import GestureState
from config.settings import Config
import time

logger = logging.getLogger(__name__)

mouse_bp = Blueprint('mouse', __name__)

# Global instances
mouse_controller = MouseController()
keyboard_controller = KeyboardController()
gesture_state = GestureState()

def safe_scroll(direction, amount=1):
    """Safely perform scroll with cooldown"""
    if not gesture_state.can_scroll():
        return False
    
    try:
        mouse_controller.scroll_vertical(direction, amount)
        gesture_state.update_scroll_time()
        return True
    except Exception as e:
        logger.error(f"Error during scroll: {e}")
        return False

def safe_zoom(zoom_in=True, amount=1):
    """Safely perform zoom with Ctrl+Scroll with cooldown"""
    if not gesture_state.can_zoom():
        return False
    
    try:
        # Start zoom operation
        if keyboard_controller.zoom_with_ctrl():
            # Perform scroll while holding Ctrl
            amount = min(amount, Config.MAX_ZOOM_AMOUNT)
            for _ in range(amount):
                mouse_controller.scroll_vertical('up' if zoom_in else 'down', 1)
                time.sleep(0.02)
            
            # Release Ctrl
            keyboard_controller.release_ctrl_for_zoom()
            gesture_state.update_zoom_time()
            return True
        return False
        
    except Exception as e:
        logger.error(f"Error during zoom: {e}")
        keyboard_controller.release_ctrl_for_zoom()
        return False

@mouse_bp.route('/mouse', methods=['POST'])
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
            dx = command_data.get('dx', 0)
            dy = command_data.get('dy', 0)
            mouse_controller.move(dx, dy)
            
        elif action == 'left_click':
            mouse_controller.left_click()
            
        elif action == 'right_click':
            mouse_controller.right_click()
            
        elif action == 'double_click':
            mouse_controller.double_click()
            
        elif action == 'scroll_up':
            amount = command_data.get('amount', 1)
            safe_scroll('up', amount)
            
        elif action == 'scroll_down':
            amount = command_data.get('amount', 1)
            safe_scroll('down', amount)
            
        elif action == 'smooth_scroll':
            direction = command_data.get('direction', 'up')
            intensity = command_data.get('intensity', 1)
            scroll_amount = max(1, min(5, int(abs(intensity * 3))))
            safe_scroll(direction, scroll_amount)
            
        elif action == 'pinch_zoom':
            scale_delta = command_data.get('scale_delta', 0)
            zoom_in = scale_delta > 0
            zoom_amount = max(1, min(3, int(abs(scale_delta * 5))))
            safe_zoom(zoom_in, zoom_amount)
            
        elif action == 'drag_start':
            finger_count = command_data.get('finger_count', 1)
            
            if finger_count == 1:
                current_pos = mouse_controller.get_position()
                selection_mode = command_data.get('selection_mode', False)
                gesture_state.start_drag(current_pos, selection_mode)
                mouse_controller.press_button('left')
            else:
                logger.info(f"Ignoring drag_start for {finger_count} fingers")
            
        elif action == 'drag_update':
            if gesture_state.is_dragging:
                dx = command_data.get('dx', 0)
                dy = command_data.get('dy', 0)
                mouse_controller.move(dx, dy)
            
        elif action == 'drag_end':
            if gesture_state.is_dragging:
                mouse_controller.release_button('left')
                gesture_state.reset_drag()
            
        elif action == 'middle_click':
            mouse_controller.middle_click()
            
        elif action == 'scroll_horizontal':
            direction = command_data.get('direction', 'left')
            amount = command_data.get('amount', 1)
            
            if not mouse_controller.scroll_horizontal(direction, amount):
                # Fallback to arrow keys
                key = 'left' if direction == 'left' else 'right'
                for _ in range(amount):
                    keyboard_controller.press_key(key)
            
        else:
            return jsonify({"status": "error", "error": f"Unknown mouse action: {action}"}), 400
            
        return jsonify({"status": "success", "message": f"Mouse {action} executed"})
        
    except Exception as e:
        logger.error(f"Error handling mouse command: {e}")
        gesture_state.reset_drag()
        keyboard_controller.release_all_keys()
        return jsonify({"status": "error", "error": str(e)}), 500