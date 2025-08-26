"""
Key mapping utilities
"""

from pynput.keyboard import Key, KeyCode

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