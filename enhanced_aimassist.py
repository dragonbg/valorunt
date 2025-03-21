"""
Enhanced Aim Assist for Valorant - Educational purposes only
Uses advanced techniques to bypass input detection without Arduino
"""

import cv2
import numpy as np
import time
import win32api
import win32con
import win32gui
import win32process
import keyboard
import mss
import mouse
import threading
import sys
import os
import random
import ctypes
from datetime import datetime, timedelta
import config

# Direct input simulation
SendInput = ctypes.windll.user32.SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

class EnhancedAimAssist:
    def __init__(self):
        # Constants for SendInput
        self.MOUSEEVENTF_MOVE = 0x0001
        self.MOUSEEVENTF_LEFTDOWN = 0x0002
        self.MOUSEEVENTF_LEFTUP = 0x0004
        self.MOUSEEVENTF_RIGHTDOWN = 0x0008
        self.MOUSEEVENTF_RIGHTUP = 0x0010
        self.MOUSEEVENTF_ABSOLUTE = 0x8000
        self.INPUT_MOUSE = 0
        
        # Configuration
        self.monitor = {
            "top": 0, 
            "left": 0, 
            "width": config.GAME_RESOLUTION["width"], 
            "height": config.GAME_RESOLUTION["height"]
        }
        self.center_x = self.monitor["width"] // 2
        self.center_y = self.monitor["height"] // 2
        
        # Settings from config
        self.color_lower1 = config.TARGET_COLOR["lower_red1"]
        self.color_upper1 = config.TARGET_COLOR["upper_red1"]
        self.color_lower2 = config.TARGET_COLOR["lower_red2"]
        self.color_upper2 = config.TARGET_COLOR["upper_red2"]
        
        self.aim_lock_key = config.KEYBINDS["aim_lock_key"]
        self.exit_key = config.KEYBINDS["exit_key"]
        self.toggle_key = config.KEYBINDS["toggle_key"]
        self.debug_key = config.KEYBINDS["debug_key"]
        
        self.scan_region_size = config.PERFORMANCE["scan_region_size"]
        self.aim_speed = config.AIM_ASSIST["aim_speed"] * 0.8  # Reduce speed for more natural movement
        self.smoothing_factor = config.AIM_ASSIST["smoothing_factor"]
        self.max_adjustment = int(config.AIM_ASSIST["max_adjustment"] * 0.7)  # Reduced for subtlety
        self.headshot_offset = config.AIM_ASSIST["headshot_offset"]
        self.min_contour_area = config.PERFORMANCE["minimum_contour_area"]
        
        self.scan_rate = config.PERFORMANCE["scan_rate"]
        
        # Input method settings
        self.input_methods = ["direct", "sendinput", "setcursorpos", "event"]
        self.current_method = 0  # Start with direct method
        
        # Advanced input settings
        self.humanize_movement = True
        self.movement_stagger = True
        self.movement_patterns = [
            [0.8, 1.0, 0.8],  # Acceleration-deceleration pattern
            [0.5, 1.0, 0.7],  # Front-loaded pattern
            [0.7, 0.9, 1.0]   # End-loaded pattern
        ]
        self.current_pattern = 0
        self.aim_jitter = 2.0  # Pixel jitter to make movement look organic
        
        # Anti-detection settings
        self.aim_inertia = 0.3  # Simulates mouse inertia
        self.prev_dx = 0
        self.prev_dy = 0
        self.intermittent_assist = True
        self.assist_percentage = 85  # Percentage of time aim assist is active
        
        # States
        self.running = True
        self.aim_assist_enabled = True
        self.debug_mode = config.DEBUG["enabled"]
        self.last_scan_time = datetime.now()
        self.cooldown = timedelta(milliseconds=1000 / self.scan_rate)
        
        # Performance metrics
        self.fps = 0
        self.frame_count = 0
        self.fps_time = time.time()
        
        # Screen capture
        self.sct = mss.mss()
        
        # Debug directory
        if config.DEBUG["save_screenshots"]:
            self.debug_dir = "debug_screenshots"
            os.makedirs(self.debug_dir, exist_ok=True)
            
        # Game window focus handling
        self.valorant_window = None
        self.valorant_pid = None
        self.find_valorant_window()
        
        print("Enhanced aim assist initialized with advanced input methods.")
        print("Press END to exit, F2 to toggle on/off, F3 for debug mode.")
        print("Press CTRL+ALT+M to cycle input methods.")

    def find_valorant_window(self):
        """Find the Valorant window handle and process ID"""
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd) and 'VALORANT' in win32gui.GetWindowText(hwnd):
                hwnds.append(hwnd)
            return True
            
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        
        if hwnds:
            self.valorant_window = hwnds[0]
            tid, self.valorant_pid = win32process.GetWindowThreadProcessId(self.valorant_window)
            print(f"Found Valorant window: {win32gui.GetWindowText(self.valorant_window)}")
        else:
            print("Valorant window not found. Will try to detect again later.")
            
    def is_valorant_focused(self):
        """Check if Valorant is the focused window"""
        if not self.valorant_window:
            self.find_valorant_window()
            return False
            
        return self.valorant_window == win32gui.GetForegroundWindow()

    def update_scan_region(self):
        """Update the scanning region to be centered around the crosshair"""
        # Get current mouse position
        cursor_pos = win32api.GetCursorPos()
        
        # Update center coordinates
        self.center_x = cursor_pos[0]
        self.center_y = cursor_pos[1]
        
        # Calculate region - focus on center of screen
        half_size = self.scan_region_size // 2
        self.monitor["left"] = max(0, self.center_x - half_size)
        self.monitor["top"] = max(0, self.center_y - half_size)
        self.monitor["width"] = min(self.scan_region_size, self.monitor["left"] + self.scan_region_size)
        self.monitor["height"] = min(self.scan_region_size, self.monitor["top"] + self.scan_region_size)

    def process_frame(self, img):
        """Process a frame to find enemy highlights"""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Create mask for red colors (enemy highlights)
        mask1 = cv2.inRange(hsv, self.color_lower1, self.color_upper1)
        mask2 = cv2.inRange(hsv, self.color_lower2, self.color_upper2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # Apply morphological operations to reduce noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # For debugging
        debug_img = None
        if self.debug_mode and config.DEBUG["show_detection"]:
            debug_img = img.copy()
            cv2.drawContours(debug_img, contours, -1, (0, 255, 0), 2)
        
        if not contours:
            if self.debug_mode and debug_img is not None:
                self.show_debug_image(debug_img)
            return None, debug_img
        
        # Filter contours by minimum area
        valid_contours = [c for c in contours if cv2.contourArea(c) > self.min_contour_area]
        if not valid_contours:
            if self.debug_mode and debug_img is not None:
                self.show_debug_image(debug_img)
            return None, debug_img
        
        # Find the largest contour (likely to be the enemy)
        largest_contour = max(valid_contours, key=cv2.contourArea)
        
        # Get the center of the contour (enemy position)
        M = cv2.moments(largest_contour)
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"]) + self.monitor["left"]
            cy = int(M["m01"] / M["m00"]) + self.monitor["top"]
            
            # Apply headshot offset
            cy += self.headshot_offset
            
            # Draw target for debugging
            if self.debug_mode and debug_img is not None:
                rel_x = int(M["m10"] / M["m00"])  # Relative to captured region
                rel_y = int(M["m01"] / M["m00"])
                cv2.circle(debug_img, (rel_x, rel_y), 5, (0, 0, 255), -1)
                cv2.line(debug_img, (rel_x - 10, rel_y), (rel_x + 10, rel_y), (0, 0, 255), 2)
                cv2.line(debug_img, (rel_x, rel_y - 10), (rel_x, rel_y + 10), (0, 0, 255), 2)
                
                # Show calculated aim point with headshot offset
                cv2.circle(debug_img, (rel_x, rel_y + self.headshot_offset), 3, (255, 0, 0), -1)
                
                self.show_debug_image(debug_img)
                
                # Save screenshot for debugging
                if config.DEBUG["save_screenshots"]:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = os.path.join(self.debug_dir, f"detection_{timestamp}.jpg")
                    cv2.imwrite(filename, debug_img)
            
            return (cx, cy), debug_img
        
        if self.debug_mode and debug_img is not None:
            self.show_debug_image(debug_img)
        
        return None, debug_img

    def show_debug_image(self, img):
        """Display debug image with detection visualization"""
        # Add FPS counter
        if config.DEBUG["show_fps"]:
            cv2.putText(img, f"FPS: {self.fps:.1f}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
        # Show aim assist status
        status = "ENABLED" if self.aim_assist_enabled else "DISABLED"
        cv2.putText(img, f"Enhanced Aim: {status}", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
        # Show input method
        method = self.input_methods[self.current_method].upper()
        cv2.putText(img, f"Input Method: {method}", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display the debug window
        cv2.imshow("Enhanced Aim Assist Debug", img)
        cv2.waitKey(1)

    def calculate_aim_adjustment(self, target_pos):
        """Calculate the mouse movement needed to aim at target with humanization"""
        if not target_pos:
            return 0, 0
            
        # Calculate distance from crosshair to target
        dx = target_pos[0] - self.center_x
        dy = target_pos[1] - self.center_y
        
        # Calculate distance
        distance = np.sqrt(dx*dx + dy*dy)
        
        if distance <= 3:  # Already on target (smaller threshold)
            return 0, 0
        
        # Apply current movement pattern for more human-like aiming
        pattern = self.movement_patterns[self.current_pattern]
        progress = min(1.0, distance / 300)  # Progress through the pattern
        
        if progress < 0.33:
            pattern_strength = pattern[0]
        elif progress < 0.66:
            pattern_strength = pattern[1]
        else:
            pattern_strength = pattern[2]
            
        # Apply smoothing and pattern strength
        strength = self.smoothing_factor * pattern_strength
        
        # Apply micro-adjustments to avoid detection patterns
        if distance < 50:
            # Add slight randomization for small movements
            random_factor = np.random.uniform(0.82, 1.12)
            strength *= random_factor
        
        # Apply inertia to simulate physical mouse behavior
        if self.humanize_movement:
            # Weight current movement with previous movement
            dx = dx * (1 - self.aim_inertia) + self.prev_dx * self.aim_inertia
            dy = dy * (1 - self.aim_inertia) + self.prev_dy * self.aim_inertia
            
            # Add small jitter
            if self.aim_jitter > 0:
                dx += np.random.uniform(-self.aim_jitter, self.aim_jitter)
                dy += np.random.uniform(-self.aim_jitter, self.aim_jitter)
        
        # Calculate final movement
        move_x = int(dx * self.aim_speed * strength)
        move_y = int(dy * self.aim_speed * strength)
        
        # Limit maximum adjustment per frame
        if abs(move_x) > self.max_adjustment:
            move_x = self.max_adjustment if move_x > 0 else -self.max_adjustment
            
        if abs(move_y) > self.max_adjustment:
            move_y = self.max_adjustment if move_y > 0 else -self.max_adjustment
            
        # Update previous movement for inertia
        self.prev_dx = move_x
        self.prev_dy = move_y
            
        return move_x, move_y

    def mouse_move_direct(self, dx, dy):
        """Move the mouse using the direct Windows API method"""
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)
        
    def mouse_move_sendinput(self, dx, dy):
        """Move the mouse using the SendInput method"""
        x = ctypes.c_long(dx)
        y = ctypes.c_long(dy)
        
        # Create the mouse input structure
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.mi = MouseInput(x, y, 0, self.MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
        
        # Create the input structure
        command = Input(ctypes.c_ulong(self.INPUT_MOUSE), ii_)
        
        # Send the input command
        ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))
        
    def mouse_move_setcursorpos(self, dx, dy):
        """Move the mouse by setting cursor position"""
        current_pos = win32api.GetCursorPos()
        win32api.SetCursorPos((current_pos[0] + dx, current_pos[1] + dy))
        
    def mouse_move_event(self, dx, dy):
        """Move the mouse using a MouseMove event"""
        current_pos = win32api.GetCursorPos()
        ctypes.windll.user32.SetCursorPos(current_pos[0] + dx, current_pos[1] + dy)

    def aim_at_target(self, target_pos):
        """Move the mouse towards the target position using advanced techniques"""
        # Skip some movements to be less detectable
        if self.intermittent_assist and random.randint(1, 100) > self.assist_percentage:
            return
            
        move_x, move_y = self.calculate_aim_adjustment(target_pos)
        
        if move_x == 0 and move_y == 0:
            return
            
        if self.movement_stagger:
            # Break movement into smaller, variable steps
            steps = random.randint(2, 4)
            delays = [random.uniform(0.001, 0.004) for _ in range(steps-1)]
            
            for i in range(steps):
                # Variable step sizes
                step_factor = 1.0 if i == steps-1 else random.uniform(0.2, 0.5)
                step_x = int(move_x * step_factor / steps)
                step_y = int(move_y * step_factor / steps)
                
                # Skip empty steps
                if step_x == 0 and step_y == 0:
                    continue
                
                # Use the selected input method
                if self.current_method == 0:
                    self.mouse_move_direct(step_x, step_y)
                elif self.current_method == 1:
                    self.mouse_move_sendinput(step_x, step_y)
                elif self.current_method == 2:
                    self.mouse_move_setcursorpos(step_x, step_y)
                else:
                    self.mouse_move_event(step_x, step_y)
                
                # Add small delay between steps for more human-like movement
                if i < steps-1:
                    time.sleep(delays[i])
        else:
            # Use the selected input method
            if self.current_method == 0:
                self.mouse_move_direct(move_x, move_y)
            elif self.current_method == 1:
                self.mouse_move_sendinput(move_x, move_y)
            elif self.current_method == 2:
                self.mouse_move_setcursorpos(move_x, move_y)
            else:
                self.mouse_move_event(move_x, move_y)

    def keyboard_listener(self):
        """Thread to listen for keyboard inputs"""
        while self.running:
            if keyboard.is_pressed(self.exit_key):
                self.running = False
                print("Exiting enhanced aim assist...")
                break
                
            if keyboard.is_pressed(self.toggle_key):
                self.aim_assist_enabled = not self.aim_assist_enabled
                state = "enabled" if self.aim_assist_enabled else "disabled"
                print(f"Enhanced aim assist {state}")
                time.sleep(0.3)  # Debounce
                
            if keyboard.is_pressed(self.debug_key):
                self.debug_mode = not self.debug_mode
                state = "enabled" if self.debug_mode else "disabled"
                print(f"Debug mode {state}")
                
                # Close debug window if debug mode is disabled
                if not self.debug_mode:
                    cv2.destroyAllWindows()
                
                time.sleep(0.3)  # Debounce
            
            # Toggle humanization
            if keyboard.is_pressed('ctrl+alt+h'):
                self.humanize_movement = not self.humanize_movement
                state = "enabled" if self.humanize_movement else "disabled"
                print(f"Movement humanization {state}")
                time.sleep(0.3)  # Debounce
                
            # Toggle movement stagger
            if keyboard.is_pressed('ctrl+alt+s'):
                self.movement_stagger = not self.movement_stagger
                state = "enabled" if self.movement_stagger else "disabled"
                print(f"Movement stagger {state}")
                time.sleep(0.3)  # Debounce
                
            # Cycle movement patterns
            if keyboard.is_pressed('ctrl+alt+p'):
                self.current_pattern = (self.current_pattern + 1) % len(self.movement_patterns)
                print(f"Using movement pattern {self.current_pattern + 1}")
                time.sleep(0.3)  # Debounce
                
            # Cycle input methods
            if keyboard.is_pressed('ctrl+alt+m'):
                self.current_method = (self.current_method + 1) % len(self.input_methods)
                print(f"Using input method: {self.input_methods[self.current_method]}")
                time.sleep(0.3)  # Debounce
                
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
        """Main loop of the enhanced aim assist"""
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
                
                # Periodically check for Valorant window if not found
                if not self.valorant_window and self.frame_count % 100 == 0:
                    self.find_valorant_window()
                
                # Update FPS counter
                self.update_fps()
                
                # Update scan region around current mouse position
                self.update_scan_region()
                
                # Capture screen region
                screenshot = np.array(self.sct.grab(self.monitor))
                
                # Process the frame to find enemies
                target_pos, _ = self.process_frame(screenshot)
                
                # Only assist when the aim key is pressed and assist is enabled
                if keyboard.is_pressed(self.aim_lock_key) and self.aim_assist_enabled and target_pos:
                    # Aim at the target if found
                    self.aim_at_target(target_pos)
                    
                    # Occasionally add extra delay to avoid patterns
                    if random.random() < 0.15:  # 15% chance
                        time.sleep(random.uniform(0.001, 0.005))
        
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Clean up
            cv2.destroyAllWindows()
            print("Enhanced aim assist terminated")

if __name__ == "__main__":
    print("Starting enhanced aim assist for educational purposes...")
    print("DISCLAIMER: This is for EDUCATIONAL PURPOSES ONLY.")
    print("Use in offline mode only. Unauthorized use in online games may violate terms of service.")
    
    # Wait for 3 seconds to give user time to read disclaimer
    time.sleep(3)
    
    print("\nAdvanced controls:")
    print("- CTRL+ALT+M: Cycle through input methods")
    print("- CTRL+ALT+H: Toggle movement humanization")
    print("- CTRL+ALT+S: Toggle movement stagger")
    print("- CTRL+ALT+P: Cycle movement patterns")
    
    aim_assist = EnhancedAimAssist()
    aim_assist.run() 