#!/usr/bin/env python3
"""
Enhanced PC Mouse & Keyboard Control Server for Ubuntu
Main application entry point
"""

from flask import Flask
import sys
from config.settings import Config
from routes.mouse_routes import mouse_bp
from routes.keyboard_routes import keyboard_bp
from routes.gesture_routes import gesture_bp
from routes.status_routes import status_bp
from utils.logger import setup_logger
from utils.network_utils import print_server_info

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register blueprints
    app.register_blueprint(mouse_bp)
    app.register_blueprint(keyboard_bp)
    app.register_blueprint(gesture_bp)
    app.register_blueprint(status_bp)
    
    return app

def main():
    """Main application entry point"""
    # Setup logging
    logger = setup_logger()
    
    # Create Flask app
    app = create_app()
    
    # Print server information
    print_server_info()
    
    try:
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
