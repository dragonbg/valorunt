"""
Triggerbot for Valorant - Educational purposes only
This automatically fires when an enemy is detected under the crosshair
"""

import cv2
import numpy as np
import time
import win32api
import win32con
import keyboard
import mss
import threading
import sys
import os
from datetime import datetime, timedelta
import config
import utils
import random

class ValorantTriggerBot:
    def __init__(self):
        # Configuration
        self.crosshair_size = 20  # Size of crosshair detection zone
        self.monitor = {
            "top": config.GAME_RESOLUTION["height"] // 2 - self.crosshair_size // 2,
            "left": config.GAME_RESOLUTION["width"] // 2 - self.crosshair_size // 2, 
            "width": self.crosshair_size,
            "height": self.crosshair_size
        }
        
        # Center of the screen
        self.center_x = config.GAME_RESOLUTION["width"] // 2
        self.center_y = config.GAME_RESOLUTION["height"] // 2
        
        # Settings from config
        self.color_lower1 = config.TARGET_COLOR["lower_red1"]
        self.color_upper1 = config.TARGET_COLOR["upper_red1"]
        self.color_lower2 = config.TARGET_COLOR["lower_red2"]
        self.color_upper2 = config.TARGET_COLOR["upper_red2"]
        
        # Keybinds
        self.exit_key = config.KEYBINDS["exit_key"]
        self.toggle_key = config.KEYBINDS["toggle_key"]
        self.debug_key = config.KEYBINDS["debug_key"]
        
        # Reaction time (ms) - randomized for more human-like behavior
        self.base_reaction_time = 150  # Base time in ms
        self.reaction_jitter = 50      # Random jitter range +/- in ms
        
        # Minimum pixel threshold for firing
        self.min_target_pixels = 30
        
        # States
        self.running = True
        self.triggerbot_enabled = True
        self.debug_mode = config.DEBUG["enabled"]
        self.last_scan_time = datetime.now()
        self.cooldown = timedelta(milliseconds=1000 / config.PERFORMANCE["scan_rate"])
        
        # Performance metrics
        self.fps = 0
        self.frame_count = 0
        self.fps_time = time.time()
        
        # Anti-detection measures
        self.last_shot_time = time.time() - 10  # Initialize with a past time
        self.min_time_between_shots = 0.05      # Minimum time between shots (50ms)
        self.consecutive_shots = 0              # Count consecutive shots to prevent spray patterns
        self.max_consecutive_shots = 8          # Maximum consecutive shots before forced delay
        
        # False trigger prevention
        self.confirmed_targets = 0              # Number of consecutive frames with target detected
        self.required_confirmations = 2         # Frames needed before triggering
        
        # Screen capture
        self.sct = mss.mss()
        
        # Debug directory
        if config.DEBUG["save_screenshots"]:
            self.debug_dir = "debug_screenshots"
            os.makedirs(self.debug_dir, exist_ok=True)
        
        print("Triggerbot initialized. Press END to exit, F2 to toggle on/off, F3 for debug mode.")

    def detect_enemy_in_crosshair(self, img):
        """Detect if an enemy is under the crosshair"""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Create mask for enemy colors
        mask1 = cv2.inRange(hsv, self.color_lower1, self.color_upper1)
        mask2 = cv2.inRange(hsv, self.color_lower2, self.color_upper2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # Apply morphological operations to reduce noise
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Count detected pixels
        detected_pixels = cv2.countNonZero(mask)
        
        # Debug visualization
        debug_img = None
        if self.debug_mode and config.DEBUG["show_detection"]:
            debug_img = img.copy()
            # Overlay mask on debug image
            debug_img[mask > 0] = [0, 0, 255]  # Red overlay on detected areas
            cv2.putText(debug_img, f"Detected: {detected_pixels} px", (5, 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        return detected_pixels >= self.min_target_pixels, detected_pixels, debug_img

    def show_debug_image(self, img):
        """Display debug image"""
        # Add FPS counter
        if config.DEBUG["show_fps"]:
            cv2.putText(img, f"FPS: {self.fps:.1f}", (5, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
        # Show triggerbot status
        status = "ENABLED" if self.triggerbot_enabled else "DISABLED"
        cv2.putText(img, f"Triggerbot: {status}", (5, 45), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Show confirmation counter
        cv2.putText(img, f"Confirmations: {self.confirmed_targets}/{self.required_confirmations}", 
                   (5, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Display the debug window
        cv2.imshow("Triggerbot Debug", img)
        cv2.waitKey(1)

    def click_mouse(self):
        """Simulate a mouse click with human-like behavior"""
        current_time = time.time()
        
        # Check if enough time has passed since last shot
        if current_time - self.last_shot_time < self.min_time_between_shots:
            return
        
        # Check if we've fired too many consecutive shots
        if self.consecutive_shots >= self.max_consecutive_shots:
            # Force a pause with random timing to seem more human
            time.sleep(random.uniform(0.08, 0.2))
            self.consecutive_shots = 0  # Reset counter
        
        # Add human-like reaction time
        reaction_time = (self.base_reaction_time + random.uniform(-self.reaction_jitter, self.reaction_jitter)) / 1000.0
        time.sleep(reaction_time)
        
        # Simulate mouse down
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        
        # Random hold duration
        hold_duration = random.uniform(0.02, 0.06)
        time.sleep(hold_duration)
        
        # Simulate mouse up
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        
        # Update timing variables
        self.last_shot_time = current_time
        self.consecutive_shots += 1

    def keyboard_listener(self):
        """Thread to listen for keyboard inputs"""
        while self.running:
            if keyboard.is_pressed(self.exit_key):
                self.running = False
                print("Exiting triggerbot...")
                break
                
            if keyboard.is_pressed(self.toggle_key):
                self.triggerbot_enabled = not self.triggerbot_enabled
                state = "enabled" if self.triggerbot_enabled else "disabled"
                print(f"Triggerbot {state}")
                time.sleep(0.3)  # Debounce
                
            if keyboard.is_pressed(self.debug_key):
                self.debug_mode = not self.debug_mode
                state = "enabled" if self.debug_mode else "disabled"
                print(f"Debug mode {state}")
                
                # Close debug window if debug mode is disabled
                if not self.debug_mode:
                    cv2.destroyAllWindows()
                
                time.sleep(0.3)  # Debounce
                
            # Adjust min pixels with numpad +/-
            if keyboard.is_pressed('num+'):
                self.min_target_pixels = min(200, self.min_target_pixels + 5)
                print(f"Minimum target pixels: {self.min_target_pixels}")
                time.sleep(0.1)
                
            if keyboard.is_pressed('num-'):
                self.min_target_pixels = max(5, self.min_target_pixels - 5)
                print(f"Minimum target pixels: {self.min_target_pixels}")
                time.sleep(0.1)
                
            time.sleep(0.01)

    def update_fps(self):
        """Update the FPS counter"""
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.fps_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.fps_time)
            self.frame_count = 0
            self.fps_time = current_time

    def run(self):
        """Main loop of the triggerbot"""
        # Start keyboard listener in a separate thread
        keyboard_thread = threading.Thread(target=self.keyboard_listener)
        keyboard_thread.daemon = True
        keyboard_thread.start()
        
        try:
            while self.running:
                current_time = datetime.now()
                
                # Rate limiting to maintain performance
                if current_time - self.last_scan_time < self.cooldown:
                    time.sleep(0.001)
                    continue
                    
                self.last_scan_time = current_time
                
                # Update FPS counter
                self.update_fps()
                
                # Only scan when triggerbot is enabled
                if not self.triggerbot_enabled:
                    time.sleep(0.01)
                    continue
                
                # Capture small region around crosshair
                screenshot = np.array(self.sct.grab(self.monitor))
                
                # Check if enemy is in crosshair
                has_target, pixel_count, debug_img = self.detect_enemy_in_crosshair(screenshot)
                
                # Debug visualization
                if self.debug_mode and debug_img is not None:
                    self.show_debug_image(debug_img)
                    
                    # Save screenshot for debugging
                    if has_target and config.DEBUG["save_screenshots"]:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        filename = os.path.join(self.debug_dir, f"trigger_{timestamp}.jpg")
                        cv2.imwrite(filename, debug_img)
                
                # Target confirmation system to prevent false triggers
                if has_target:
                    self.confirmed_targets += 1
                    if self.confirmed_targets >= self.required_confirmations:
                        # Fire only if not in middle of firing
                        if not keyboard.is_pressed(win32con.VK_LBUTTON):
                            self.click_mouse()
                else:
                    # Reset confirmation counter if no target detected
                    self.confirmed_targets = 0
                    # Also reset consecutive shots counter when no target
                    self.consecutive_shots = 0
        
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Clean up
            cv2.destroyAllWindows()
            print("Triggerbot terminated")

if __name__ == "__main__":
    print("Starting educational triggerbot program...")
    print("DISCLAIMER: This is for EDUCATIONAL PURPOSES ONLY.")
    print("Use in offline mode only. Unauthorized use in online games may violate terms of service.")
    
    # Wait for 3 seconds to give user time to read disclaimer
    time.sleep(3)
    
    triggerbot = ValorantTriggerBot()
    triggerbot.run() 