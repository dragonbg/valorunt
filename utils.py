"""
Utility functions for the Valorant aim assist program.
"""

import cv2
import numpy as np
import win32api
import win32con
import keyboard
import time
import config

def get_screen_resolution():
    """Get the current screen resolution"""
    return win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)

def is_in_game_resolution():
    """Check if the current screen resolution matches the configured game resolution"""
    screen_width, screen_height = get_screen_resolution()
    return (screen_width == config.GAME_RESOLUTION["width"] and 
            screen_height == config.GAME_RESOLUTION["height"])

def adjust_color_range(color_range, saturation_adjust=0, value_adjust=0):
    """Adjust the HSV color range to account for different lighting conditions"""
    lower = color_range["lower"].copy()
    upper = color_range["upper"].copy()
    
    # Adjust saturation
    lower[1] = max(0, lower[1] + saturation_adjust)
    upper[1] = min(255, upper[1] + saturation_adjust)
    
    # Adjust value
    lower[2] = max(0, lower[2] + value_adjust)
    upper[2] = min(255, upper[2] + value_adjust)
    
    return {"lower": lower, "upper": upper}

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

def smooth_movement(current_pos, target_pos, smoothing_factor):
    """Calculate smoothed movement towards a target position"""
    # Calculate raw movement vector
    dx = target_pos[0] - current_pos[0]
    dy = target_pos[1] - current_pos[1]
    
    # Apply smoothing
    move_x = dx * smoothing_factor
    move_y = dy * smoothing_factor
    
    return int(move_x), int(move_y)

def wait_for_key_press(key, prompt_message=None):
    """Wait for a specific key to be pressed"""
    if prompt_message:
        print(prompt_message)
    
    while True:
        if keyboard.is_pressed(key):
            time.sleep(0.3)  # Debounce
            return True
        time.sleep(0.01)

def apply_headshot_offset(position, offset):
    """Apply vertical offset to aim at head level"""
    return (position[0], position[1] + offset)

def enhance_image_contrast(img):
    """Enhance image contrast to improve detection in dark areas"""
    # Convert to YUV color space
    yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    
    # Apply histogram equalization to Y channel
    yuv[:,:,0] = cv2.equalizeHist(yuv[:,:,0])
    
    # Convert back to BGR
    return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

def calculate_region_of_interest(center_pos, size, screen_size):
    """Calculate region of interest based on center position and size"""
    half_size = size // 2
    left = max(0, center_pos[0] - half_size)
    top = max(0, center_pos[1] - half_size)
    
    # Ensure the region doesn't go beyond screen boundaries
    width = min(size, screen_size[0] - left)
    height = min(size, screen_size[1] - top)
    
    return {"left": left, "top": top, "width": width, "height": height}

def draw_crosshair(img, center, color=(0, 255, 0), size=10, thickness=2):
    """Draw a crosshair on the image for visualization"""
    cv2.line(img, (center[0] - size, center[1]), (center[0] + size, center[1]), color, thickness)
    cv2.line(img, (center[0], center[1] - size), (center[0], center[1] + size), color, thickness)
    return img 