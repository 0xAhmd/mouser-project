"""
Status and utility routes
"""

import logging
from flask import Blueprint, jsonify
from controllers.mouse_controller import MouseController
from controllers.keyboard_controller import KeyboardController
from models.gesture_state import GestureState
from utils.network_utils import get_local_ip
from config.settings import Config
from pynput.mouse import Button

logger = logging.getLogger(__name__)

status_bp = Blueprint('status', __name__)

# Global instances
mouse_controller = MouseController()
keyboard_controller = KeyboardController()
gesture_state = GestureState()

@status_bp.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Enhanced server is running"})

@status_bp.route('/status', methods=['GET'])
def get_status():
    """Get current mouse position and server status with enhanced info"""
    try:
        x, y = mouse_controller.get_position()
        return jsonify({
            "status": "running",
            "version": Config.VERSION,
            "mouse_position": {"x": x, "y": y},
            "server_ip": get_local_ip(),
            "features": [
                "mouse", "keyboard", "enhanced_gestures", 
                "two_finger_scroll", "pinch_zoom", "text_selection",
                "three_finger_swipe", "smooth_scrolling"
            ],
            "gesture_state": gesture_state.get_state_dict(),
            "config": {
                "scroll_cooldown": Config.SCROLL_COOLDOWN,
                "zoom_cooldown": Config.ZOOM_COOLDOWN,
                "max_scroll_amount": Config.MAX_SCROLL_AMOUNT,
                "max_zoom_amount": Config.MAX_ZOOM_AMOUNT
            }
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@status_bp.route('/reset', methods=['POST'])
def reset_state():
    """Reset all gesture states - useful for recovery"""
    try:
        gesture_state.reset_drag()
        
        # Release any potentially stuck keys
        keyboard_controller.release_all_keys()
        
        # Release mouse buttons
        try:
            mouse_controller.release_button('left')
            mouse_controller.release_button('right')
            mouse_controller.release_button('middle')
        except:
            pass
            
        return jsonify({"status": "success", "message": "All states reset"})
        
    except Exception as e:
        logger.error(f"Error resetting state: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500