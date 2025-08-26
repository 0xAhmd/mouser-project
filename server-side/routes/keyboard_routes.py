"""
Keyboard control routes
"""

import logging
from flask import Blueprint, request, jsonify
from controllers.keyboard_controller import KeyboardController

logger = logging.getLogger(__name__)

keyboard_bp = Blueprint('keyboard', __name__)
keyboard_controller = KeyboardController()

@keyboard_bp.route('/keyboard', methods=['POST'])
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
            text = command_data.get('text', '')
            keyboard_controller.type_text(text)
            
        elif action == 'key':
            key_string = command_data.get('key', '')
            if not key_string:
                return jsonify({"status": "error", "error": "No key provided"}), 400
            
            modifiers = {
                'shift': command_data.get('shift', False),
                'ctrl': command_data.get('ctrl', False),
                'alt': command_data.get('alt', False),
                'cmd': command_data.get('cmd', False)
            }
            
            logger.info(f"Processing key: {key_string}, modifiers: {modifiers}")
            keyboard_controller.press_key(key_string, modifiers)
                
        elif action == 'key_press':
            # Legacy support
            key_string = command_data.get('key', '')
            if key_string:
                keyboard_controller.press_key(key_string)
            
        elif action == 'key_combination':
            keys = command_data.get('keys', [])
            if not keys:
                return jsonify({"status": "error", "error": "No keys provided for combination"}), 400
            
            keyboard_controller.press_key_combination(keys)
                
        elif action == 'key_hold_start':
            key_string = command_data.get('key', '')
            if key_string:
                keyboard_controller.hold_key(key_string)
            
        elif action == 'key_hold_end':
            key_string = command_data.get('key', '')
            if key_string:
                keyboard_controller.release_key(key_string)
        
        elif action == 'enhanced_shortcut':
            shortcut_type = command_data.get('type', '')
            try:
                keyboard_controller.execute_shortcut(shortcut_type)
            except ValueError as e:
                return jsonify({"status": "error", "error": str(e)}), 400
            
        else:
            return jsonify({"status": "error", "error": f"Unknown keyboard action: {action}"}), 400
            
        return jsonify({"status": "success", "message": f"Keyboard {action} executed"})
        
    except Exception as e:
        logger.error(f"Error handling keyboard command: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500