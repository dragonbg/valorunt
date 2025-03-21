"""
Configuration settings for the Valorant aim assist program.
Modify these settings to customize the behavior of the program.
"""

import numpy as np

# Game settings
GAME_RESOLUTION = {
    "width": 1920,  # Game window width
    "height": 1080  # Game window height
}

# Target detection settings
TARGET_COLOR = {
    "lower_red1": np.array([0, 100, 150]),    # Lower HSV range for red (main)
    "upper_red1": np.array([10, 255, 255]),   # Upper HSV range for red (main)
    "lower_red2": np.array([170, 100, 150]),  # Lower HSV range for red (wrap)
    "upper_red2": np.array([180, 255, 255])   # Upper HSV range for red (wrap)
}

# You can add additional color profiles for different agent abilities or skins
TARGET_COLORS_ALTERNATE = {
    "purple": {  # For some abilities or highlights
        "lower": np.array([125, 100, 100]),
        "upper": np.array([140, 255, 255])
    },
    "yellow": {  # For some abilities or highlights
        "lower": np.array([20, 100, 100]),
        "upper": np.array([30, 255, 255])
    }
}

# Performance settings
PERFORMANCE = {
    "scan_region_size": 400,   # Size of the region to scan around crosshair (pixels)
    "scan_rate": 60,           # Target scans per second
    "minimum_contour_area": 50 # Minimum size of target to detect (prevents small noise)
}

# Aim assist settings
AIM_ASSIST = {
    "aim_speed": 1.0,          # Base aim speed (higher = faster)
    "smoothing_factor": 0.5,   # Smoothing factor for aim (higher = smoother)
    "max_adjustment": 100,     # Maximum pixels to move in a single adjustment
    "headshot_offset": -10     # Vertical offset for headshot targeting
}

# Keybind settings
KEYBINDS = {
    "aim_lock_key": "shift",   # Key to hold for aim assist
    "toggle_key": "f2",        # Key to toggle aim assist on/off
    "exit_key": "end",         # Key to exit program
    "debug_key": "f3"          # Key to toggle debug visualization
}

# Debug settings
DEBUG = {
    "enabled": False,          # Enable debug visualization
    "show_fps": True,          # Show FPS counter
    "show_detection": True,    # Show detection visualization
    "save_screenshots": False  # Save screenshots of detections
} 