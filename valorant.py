import cv2
import numpy as np
import time
import win32api
import win32con
import keyboard
import mss
import mouse
import threading
import sys
import os
from datetime import datetime, timedelta
import config

class ValorantAimAssist:
    def __init__(self):
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
        self.aim_speed = config.AIM_ASSIST["aim_speed"]
        self.smoothing_factor = config.AIM_ASSIST["smoothing_factor"]
        self.max_adjustment = config.AIM_ASSIST["max_adjustment"]
        self.headshot_offset = config.AIM_ASSIST["headshot_offset"]
        self.min_contour_area = config.PERFORMANCE["minimum_contour_area"]
        
        self.scan_rate = config.PERFORMANCE["scan_rate"]
        
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
        
        # Use indirect mouse movement to avoid detection
        self.use_direct_input = False
        
        print("Aim assist initialized. Press END to exit, F2 to toggle on/off, F3 for debug mode.")

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
        cv2.putText(img, f"Aim Assist: {status}", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display the debug window
        cv2.imshow("Aim Assist Debug", img)
        cv2.waitKey(1)

    def calculate_aim_adjustment(self, target_pos):
        """Calculate the mouse movement needed to aim at target"""
        if not target_pos:
            return 0, 0
            
        # Calculate distance from crosshair to target
        dx = target_pos[0] - self.center_x
        dy = target_pos[1] - self.center_y
        
        # Calculate distance
        distance = np.sqrt(dx*dx + dy*dy)
        
        if distance <= 5:  # Already on target
            return 0, 0
        
        # Apply smoothing for more natural movement
        # Move faster when far away, slower when close
        strength = self.smoothing_factor + (1 - self.smoothing_factor) * (distance / 500)
        
        # Apply micro-adjustments to avoid detection patterns
        if distance < 50:
            # Add slight randomization for small movements
            random_factor = np.random.uniform(0.85, 1.15)
            strength *= random_factor
        
        move_x = int(dx * self.aim_speed * strength)
        move_y = int(dy * self.aim_speed * strength)
        
        # Limit maximum adjustment per frame
        if abs(move_x) > self.max_adjustment:
            move_x = self.max_adjustment if move_x > 0 else -self.max_adjustment
            
        if abs(move_y) > self.max_adjustment:
            move_y = self.max_adjustment if move_y > 0 else -self.max_adjustment
            
        return move_x, move_y

    def aim_at_target(self, target_pos):
        """Move the mouse towards the target position"""
        move_x, move_y = self.calculate_aim_adjustment(target_pos)
        
        if move_x != 0 or move_y != 0:
            # Use a different mouse movement method to avoid detection
            if self.use_direct_input:
                # Direct method - may be detected
                win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, move_x, move_y, 0, 0)
            else:
                # Indirect method - less detectable but may be less responsive
                # Break down movement into smaller steps
                steps = 3
                for _ in range(steps):
                    small_x = move_x // steps
                    small_y = move_y // steps
                    # Apply slight randomization to timing between movements
                    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, small_x, small_y, 0, 0)
                    time.sleep(np.random.uniform(0.001, 0.005))  # Randomized tiny delay

    def keyboard_listener(self):
        """Thread to listen for keyboard inputs"""
        while self.running:
            if keyboard.is_pressed(self.exit_key):
                self.running = False
                print("Exiting aim assist...")
                break
                
            if keyboard.is_pressed(self.toggle_key):
                self.aim_assist_enabled = not self.aim_assist_enabled
                state = "enabled" if self.aim_assist_enabled else "disabled"
                print(f"Aim assist {state}")
                time.sleep(0.3)  # Debounce
                
            if keyboard.is_pressed(self.debug_key):
                self.debug_mode = not self.debug_mode
                state = "enabled" if self.debug_mode else "disabled"
                print(f"Debug mode {state}")
                
                # Close debug window if debug mode is disabled
                if not self.debug_mode:
                    cv2.destroyAllWindows()
                
                time.sleep(0.3)  # Debounce
            
            # Toggle direct input mode with a hidden key combo
            if keyboard.is_pressed('ctrl+alt+d'):
                self.use_direct_input = not self.use_direct_input
                mode = "direct" if self.use_direct_input else "indirect"
                print(f"Using {mode} input mode")
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
        """Main loop of the aim assist"""
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
                    
                    # Add small random delay to avoid patterns
                    if np.random.random() < 0.1:  # 10% chance
                        time.sleep(np.random.uniform(0.001, 0.01))
        
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Clean up
            cv2.destroyAllWindows()
            print("Aim assist terminated")

if __name__ == "__main__":
    print("Starting educational aim assist program...")
    print("DISCLAIMER: This is for EDUCATIONAL PURPOSES ONLY.")
    print("Use in offline mode only. Unauthorized use in online games may violate terms of service.")
    
    # Wait for 3 seconds to give user time to read disclaimer
    time.sleep(3)
    
    aim_assist = ValorantAimAssist()
    aim_assist.run() 