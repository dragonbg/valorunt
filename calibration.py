"""
Calibration tool for the Valorant aim assist program.
This helps users find the optimal color settings for enemy detection.
"""

import cv2
import numpy as np
import mss
import time
import keyboard
import win32api
import os
from datetime import datetime
import config
import utils

class ColorCalibrationTool:
    def __init__(self):
        # Create output directory for calibration images
        self.output_dir = "calibration_data"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Screen capture setup
        self.sct = mss.mss()
        self.monitor = {
            "top": 0, 
            "left": 0, 
            "width": config.GAME_RESOLUTION["width"], 
            "height": config.GAME_RESOLUTION["height"]
        }
        
        # Initial color ranges from config
        self.current_lower_red1 = config.TARGET_COLOR["lower_red1"].copy()
        self.current_upper_red1 = config.TARGET_COLOR["upper_red1"].copy()
        
        # Control variables
        self.running = True
        self.color_component = 0  # 0=H, 1=S, 2=V
        self.is_lower = True  # Adjusting lower or upper bound
        self.range_index = 0  # 0=red1, 1=red2
        
        # Key bindings for calibration
        self.exit_key = 'esc'
        self.capture_key = 'c'
        self.toggle_component_key = 'tab'
        self.toggle_bound_key = 'space'
        self.toggle_range_key = 'r'
        
        # Windows
        self.main_window = "Color Calibration Tool"
        self.mask_window = "Detection Mask"
        
        # Instructions
        self.instructions = [
            "ESC: Exit calibration",
            "C: Capture screenshot",
            "TAB: Toggle component (H/S/V)",
            "SPACE: Toggle bound (lower/upper)",
            "R: Toggle color range",
            "Up/Down arrows: Adjust value",
            "Left/Right arrows: Change adjustment step"
        ]
        
        # Adjustment step
        self.adjustment_step = 5
        
        print("Color calibration tool initialized.")
        print("Position enemies in view and adjust values to optimize detection.")

    def capture_full_screen(self):
        """Capture the full screen for calibration"""
        return np.array(self.sct.grab(self.monitor))

    def create_hsv_mask(self, img, lower1, upper1, lower2=None, upper2=None):
        """Create a mask based on the current HSV ranges"""
        # Convert to HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Create mask for the main color range
        mask1 = cv2.inRange(hsv, lower1, upper1)
        
        # If second range is provided, add it to the mask
        if lower2 is not None and upper2 is not None:
            mask2 = cv2.inRange(hsv, lower2, upper2)
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = mask1
        
        # Apply morphological operations to reduce noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask

    def apply_mask(self, img, mask):
        """Apply mask to the image to show the detected areas"""
        return cv2.bitwise_and(img, img, mask=mask)

    def save_calibration_data(self):
        """Save the current calibration settings"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save the current image with mask
        img = self.capture_full_screen()
        
        # Create mask with current settings
        lower2 = config.TARGET_COLOR["lower_red2"]
        upper2 = config.TARGET_COLOR["upper_red2"]
        
        if self.range_index == 1:
            lower1 = config.TARGET_COLOR["lower_red1"]
            upper1 = config.TARGET_COLOR["upper_red1"]
            lower2 = self.current_lower_red1
            upper2 = self.current_upper_red1
        else:
            lower1 = self.current_lower_red1
            upper1 = self.current_upper_red1
        
        mask = self.create_hsv_mask(img, lower1, upper1, lower2, upper2)
        masked_img = self.apply_mask(img, mask)
        
        # Save images
        cv2.imwrite(os.path.join(self.output_dir, f"original_{timestamp}.jpg"), img)
        cv2.imwrite(os.path.join(self.output_dir, f"mask_{timestamp}.jpg"), mask)
        cv2.imwrite(os.path.join(self.output_dir, f"masked_{timestamp}.jpg"), masked_img)
        
        # Save settings to text file
        with open(os.path.join(self.output_dir, f"settings_{timestamp}.txt"), 'w') as f:
            f.write(f"# Calibration settings saved on {timestamp}\n")
            
            if self.range_index == 0:
                f.write("\n# Main red range (lower_red1, upper_red1):\n")
                f.write(f"lower_red1 = np.array([{self.current_lower_red1[0]}, {self.current_lower_red1[1]}, {self.current_lower_red1[2]}])\n")
                f.write(f"upper_red1 = np.array([{self.current_upper_red1[0]}, {self.current_upper_red1[1]}, {self.current_upper_red1[2]}])\n")
                f.write("\n# Secondary red range (unchanged):\n")
                f.write(f"lower_red2 = np.array([{lower2[0]}, {lower2[1]}, {lower2[2]}])\n")
                f.write(f"upper_red2 = np.array([{upper2[0]}, {upper2[1]}, {upper2[2]}])\n")
            else:
                f.write("\n# Main red range (unchanged):\n")
                f.write(f"lower_red1 = np.array([{lower1[0]}, {lower1[1]}, {lower1[2]}])\n")
                f.write(f"upper_red1 = np.array([{upper1[0]}, {upper1[1]}, {upper1[2]}])\n")
                f.write("\n# Secondary red range (lower_red2, upper_red2):\n")
                f.write(f"lower_red2 = np.array([{self.current_lower_red1[0]}, {self.current_lower_red1[1]}, {self.current_lower_red1[2]}])\n")
                f.write(f"upper_red2 = np.array([{self.current_upper_red1[0]}, {self.current_upper_red1[1]}, {self.current_upper_red1[2]}])\n")
        
        print(f"Calibration data saved to {self.output_dir}/ with timestamp {timestamp}")

    def update_display(self, img):
        """Update the display with the current calibration view"""
        # Create a copy for drawing on
        display_img = img.copy()
        
        # Show which color range we're editing
        range_name = "Red Range 1" if self.range_index == 0 else "Red Range 2"
        
        # Get the right values for the current range
        if self.range_index == 0:
            lower = self.current_lower_red1
            upper = self.current_upper_red1
            lower2 = config.TARGET_COLOR["lower_red2"]
            upper2 = config.TARGET_COLOR["upper_red2"]
        else:
            lower = self.current_lower_red1
            upper = self.current_upper_red1
            lower2 = config.TARGET_COLOR["lower_red1"]
            upper2 = config.TARGET_COLOR["upper_red1"]
        
        # Create mask with current settings
        mask = self.create_hsv_mask(img, lower, upper, lower2, upper2)
        masked_img = self.apply_mask(img, mask)
        
        # Display component being adjusted
        component_names = ["Hue", "Saturation", "Value"]
        bound_names = ["Lower", "Upper"]
        component = component_names[self.color_component]
        bound = bound_names[0 if self.is_lower else 1]
        
        # Draw status information on the image
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(display_img, f"Editing: {range_name}", (10, 30), font, 1, (0, 255, 255), 2)
        cv2.putText(display_img, f"Component: {component} | Bound: {bound}", (10, 70), font, 1, (0, 255, 255), 2)
        
        # Display current values
        cv2.putText(display_img, f"H: {lower[0]}-{upper[0]}", (10, 110), font, 0.7, (0, 255, 255) if self.color_component == 0 else (255, 255, 255), 2)
        cv2.putText(display_img, f"S: {lower[1]}-{upper[1]}", (10, 140), font, 0.7, (0, 255, 255) if self.color_component == 1 else (255, 255, 255), 2)
        cv2.putText(display_img, f"V: {lower[2]}-{upper[2]}", (10, 170), font, 0.7, (0, 255, 255) if self.color_component == 2 else (255, 255, 255), 2)
        
        # Display adjustment step
        cv2.putText(display_img, f"Step: {self.adjustment_step}", (10, 200), font, 0.7, (0, 255, 255), 2)
        
        # Display instructions
        y_offset = 240
        for instruction in self.instructions:
            cv2.putText(display_img, instruction, (10, y_offset), font, 0.5, (255, 255, 255), 1)
            y_offset += 25
        
        # Display the images
        cv2.imshow(self.main_window, display_img)
        cv2.imshow(self.mask_window, masked_img)

    def adjust_value(self, increase):
        """Adjust the current HSV value"""
        if self.is_lower:
            current_values = self.current_lower_red1
        else:
            current_values = self.current_upper_red1
        
        change = self.adjustment_step if increase else -self.adjustment_step
        
        # Adjust the appropriate component
        current_values[self.color_component] = max(0, min(255, current_values[self.color_component] + change))
        
        # Special case for Hue which is 0-179 in OpenCV
        if self.color_component == 0:
            current_values[self.color_component] = max(0, min(179, current_values[self.color_component]))

    def toggle_component(self):
        """Toggle between H, S, and V"""
        self.color_component = (self.color_component + 1) % 3

    def toggle_bound(self):
        """Toggle between lower and upper bound"""
        self.is_lower = not self.is_lower

    def toggle_range(self):
        """Toggle between color ranges"""
        self.range_index = (self.range_index + 1) % 2
        
        # Reset to working with range 1's values
        if self.range_index == 0:
            self.current_lower_red1 = config.TARGET_COLOR["lower_red1"].copy()
            self.current_upper_red1 = config.TARGET_COLOR["upper_red1"].copy()
        else:
            self.current_lower_red1 = config.TARGET_COLOR["lower_red2"].copy()
            self.current_upper_red1 = config.TARGET_COLOR["upper_red2"].copy()

    def handle_keyboard(self):
        """Handle keyboard input for calibration"""
        if keyboard.is_pressed(self.exit_key):
            self.running = False
            return True
            
        if keyboard.is_pressed(self.capture_key):
            self.save_calibration_data()
            time.sleep(0.3)  # Debounce
            
        if keyboard.is_pressed(self.toggle_component_key):
            self.toggle_component()
            time.sleep(0.3)  # Debounce
            
        if keyboard.is_pressed(self.toggle_bound_key):
            self.toggle_bound()
            time.sleep(0.3)  # Debounce
            
        if keyboard.is_pressed(self.toggle_range_key):
            self.toggle_range()
            time.sleep(0.3)  # Debounce
            
        if keyboard.is_pressed('up'):
            self.adjust_value(True)
            time.sleep(0.05)  # Allow holding for continuous adjustment
            
        if keyboard.is_pressed('down'):
            self.adjust_value(False)
            time.sleep(0.05)  # Allow holding for continuous adjustment
            
        if keyboard.is_pressed('right'):
            self.adjustment_step = min(20, self.adjustment_step + 1)
            time.sleep(0.1)  # Debounce
            
        if keyboard.is_pressed('left'):
            self.adjustment_step = max(1, self.adjustment_step - 1)
            time.sleep(0.1)  # Debounce
            
        return False

    def run(self):
        """Run the calibration tool"""
        print("Starting color calibration. Position game window with enemies visible.")
        print("Press ESC to exit calibration.")
        
        cv2.namedWindow(self.main_window, cv2.WINDOW_NORMAL)
        cv2.namedWindow(self.mask_window, cv2.WINDOW_NORMAL)
        
        try:
            while self.running:
                # Capture screen
                img = self.capture_full_screen()
                
                # Update the display
                self.update_display(img)
                
                # Handle keyboard input
                if self.handle_keyboard():
                    break
                    
                # Small delay to avoid high CPU usage
                if cv2.waitKey(1) & 0xFF == 27:  # ESC key
                    break
                    
        except Exception as e:
            print(f"Error in calibration tool: {e}")
        finally:
            cv2.destroyAllWindows()
            print("Calibration tool closed")
            
            # Return the best values found
            if self.range_index == 0:
                return {
                    "lower_red1": self.current_lower_red1,
                    "upper_red1": self.current_upper_red1
                }
            else:
                return {
                    "lower_red2": self.current_lower_red1,
                    "upper_red2": self.current_upper_red1
                }

if __name__ == "__main__":
    print("Starting color calibration tool...")
    print("This tool will help you find the optimal color settings for enemy detection.")
    print("Make sure your game is running and enemies are visible on screen.")
    
    calibration_tool = ColorCalibrationTool()
    best_values = calibration_tool.run()
    
    print("\nCalibration complete!")
    print("Best values found:")
    for key, value in best_values.items():
        print(f"{key} = {value}")
    
    print("\nYou can update these values in config.py to improve detection accuracy.") 