"""
Network utilities
"""

import socket
from config.settings import Config

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

def print_server_info():
    """Print enhanced server information"""
    local_ip = get_local_ip()
    print("=" * 70)
    print("🚀 ENHANCED PC Mouse & Keyboard Control Server Starting...")
    print("=" * 70)
    print(f"📡 Server IP: {local_ip}")
    print(f"🔌 Server Port: {Config.PORT}")
    print(f"📱 Mobile App Connection URL: http://{local_ip}:{Config.PORT}")
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