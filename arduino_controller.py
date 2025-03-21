"""
Arduino Controller for Valorant - Educational purposes only
This script interfaces with an Arduino to control mouse movements and clicks.
It bypasses software input detection by using hardware inputs through Arduino.
"""

import serial
import time
import numpy as np
import threading
import keyboard
import cv2
import mss
import config
import utils
from datetime import datetime, timedelta
import os
import sys

class ArduinoController:
    def __init__(self, port='COM3', baud_rate=115200):
        # Arduino communication settings
        self.port = port
        self.baud_rate = baud_rate
        self.arduino = None
        self.connected = False
        
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
        
        self.scan_region_size = config.PERFORMANCE["scan_region_size"]
        self.aim_speed = config.AIM_ASSIST["aim_speed"]
        self.smoothing_factor = config.AIM_ASSIST["smoothing_factor"]
        self.max_adjustment = config.AIM_ASSIST["max_adjustment"]
        self.headshot_offset = config.AIM_ASSIST["headshot_offset"]
        self.min_contour_area = config.PERFORMANCE["minimum_contour_area"]
        
        # Keybinds
        self.aim_lock_key = config.KEYBINDS["aim_lock_key"]
        self.exit_key = config.KEYBINDS["exit_key"]
        self.toggle_key = config.KEYBINDS["toggle_key"]
        self.debug_key = config.KEYBINDS["debug_key"]
        
        # States
        self.running = True
        self.aim_assist_enabled = True
        self.debug_mode = config.DEBUG["enabled"]
        self.last_scan_time = datetime.now()
        self.cooldown = timedelta(milliseconds=1000 / config.PERFORMANCE["scan_rate"])
        
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
            
        # Arduino command queue
        self.command_queue = []
        self.queue_lock = threading.Lock()
        
        # Arduino commands
        self.CMD_MOVE = 'M'      # Move mouse: M,dx,dy
        self.CMD_CLICK = 'C'     # Click mouse: C,duration_ms
        self.CMD_RIGHTCLICK = 'R'  # Right click: R
        self.CMD_PING = 'P'      # Ping to check connection: P
        
        print("Arduino controller initialized. Connect Arduino and press Enter to continue.")
        
    def connect_to_arduino(self):
        """Attempt to connect to the Arduino"""
        try:
            self.arduino = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            
            # Test connection with ping
            self.arduino.write(f"{self.CMD_PING}\n".encode())
            response = self.arduino.readline().decode().strip()
            
            if response == "PONG":
                self.connected = True
                print(f"Successfully connected to Arduino on {self.port}")
                return True
            else:
                print(f"Arduino responded with unexpected message: {response}")
                self.arduino.close()
                return False
                
        except Exception as e:
            print(f"Failed to connect to Arduino: {e}")
            if self.arduino and self.arduino.is_open:
                self.arduino.close()
            return False
    
    def send_command(self, command):
        """Send a command to the Arduino"""
        if not self.connected or not self.arduino:
            print("Arduino not connected. Cannot send command.")
            return False
            
        try:
            self.arduino.write(f"{command}\n".encode())
            # Wait for acknowledgment
            response = self.arduino.readline().decode().strip()
            return response == "OK"
        except Exception as e:
            print(f"Error sending command to Arduino: {e}")
            self.connected = False
            return False
            
    def queue_command(self, command):
        """Add a command to the queue"""
        with self.queue_lock:
            self.command_queue.append(command)
            
    def process_command_queue(self):
        """Process the command queue in a separate thread"""
        while self.running:
            commands_to_process = []
            
            # Get commands from queue with lock
            with self.queue_lock:
                if self.command_queue:
                    commands_to_process = self.command_queue.copy()
                    self.command_queue.clear()
            
            # Process each command
            for cmd in commands_to_process:
                self.send_command(cmd)
                # Small delay between commands
                time.sleep(0.01)
                
            # Sleep to avoid hogging CPU
            time.sleep(0.01)
            
    def move_mouse(self, dx, dy):
        """Queue a mouse movement command"""
        # Clamp movement values
        dx = max(-127, min(127, dx))
        dy = max(-127, min(127, dy))
        
        # Queue the command
        self.queue_command(f"{self.CMD_MOVE},{dx},{dy}")
        
    def click_mouse(self, duration_ms=50):
        """Queue a mouse click command"""
        self.queue_command(f"{self.CMD_CLICK},{duration_ms}")
        
    def right_click_mouse(self):
        """Queue a right mouse click command"""
        self.queue_command(self.CMD_RIGHTCLICK)
        
    def update_scan_region(self):
        """Update the scanning region to be centered around the crosshair"""
        # In Arduino mode, we assume the crosshair is in the center of the screen
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
        cv2.putText(img, f"Arduino Aim: {status}", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
        # Show connection status
        conn_status = "CONNECTED" if self.connected else "DISCONNECTED"
        cv2.putText(img, f"Arduino: {conn_status}", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if self.connected else (0, 0, 255), 2)
        
        # Display the debug window
        cv2.imshow("Arduino Aim Assist Debug", img)
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
        """Move the mouse towards the target position using Arduino"""
        move_x, move_y = self.calculate_aim_adjustment(target_pos)
        
        if move_x != 0 or move_y != 0:
            # Queue mouse movement via Arduino
            self.move_mouse(move_x, move_y)

    def keyboard_listener(self):
        """Thread to listen for keyboard inputs"""
        while self.running:
            if keyboard.is_pressed(self.exit_key):
                self.running = False
                print("Exiting Arduino controller...")
                break
                
            if keyboard.is_pressed(self.toggle_key):
                self.aim_assist_enabled = not self.aim_assist_enabled
                state = "enabled" if self.aim_assist_enabled else "disabled"
                print(f"Arduino aim assist {state}")
                time.sleep(0.3)  # Debounce
                
            if keyboard.is_pressed(self.debug_key):
                self.debug_mode = not self.debug_mode
                state = "enabled" if self.debug_mode else "disabled"
                print(f"Debug mode {state}")
                
                # Close debug window if debug mode is disabled
                if not self.debug_mode:
                    cv2.destroyAllWindows()
                
                time.sleep(0.3)  # Debounce
                
            # Test right-click with numpad *
            if keyboard.is_pressed('num*') and self.connected:
                print("Sending right-click test")
                self.right_click_mouse()
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
        """Main loop of the Arduino controller"""
        # Start command processing thread
        command_thread = threading.Thread(target=self.process_command_queue)
        command_thread.daemon = True
        command_thread.start()
        
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
                
                # Update scan region around center of screen
                self.update_scan_region()
                
                # Capture screen region
                screenshot = np.array(self.sct.grab(self.monitor))
                
                # Process the frame to find enemies
                target_pos, _ = self.process_frame(screenshot)
                
                # Only assist when the aim key is pressed and assist is enabled
                if keyboard.is_pressed(self.aim_lock_key) and self.aim_assist_enabled and target_pos and self.connected:
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
            if self.arduino and self.arduino.is_open:
                self.arduino.close()
            print("Arduino controller terminated")

if __name__ == "__main__":
    print("Starting Arduino controller for educational aim assist...")
    print("DISCLAIMER: This is for EDUCATIONAL PURPOSES ONLY.")
    print("Use in offline mode only. Unauthorized use in online games may violate terms of service.")
    
    # Give instructions for Arduino setup
    print("\nARDUINO SETUP INSTRUCTIONS:")
    print("1. Connect an Arduino Leonardo or Arduino Pro Micro to your computer")
    print("2. Upload the following Arduino sketch to your board:\n")
    print("""
    #include <Mouse.h>
    
    void setup() {
      Serial.begin(115200);
      Mouse.begin();
      delay(1000);
    }
    
    void loop() {
      if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\\n');
        
        // Process command
        if (command.startsWith("M")) {  // Move: M,dx,dy
          command.remove(0, 2);  // Remove "M,"
          int commaIndex = command.indexOf(',');
          if (commaIndex > 0) {
            int dx = command.substring(0, commaIndex).toInt();
            int dy = command.substring(commaIndex + 1).toInt();
            Mouse.move(dx, dy, 0);
            Serial.println("OK");
          }
        }
        else if (command.startsWith("C")) {  // Click: C,duration
          command.remove(0, 2);  // Remove "C,"
          int duration = command.toInt();
          if (duration <= 0) duration = 50;  // Default duration
          
          Mouse.press(MOUSE_LEFT);
          delay(duration);
          Mouse.release(MOUSE_LEFT);
          Serial.println("OK");
        }
        else if (command.startsWith("R")) {  // Right click
          Mouse.press(MOUSE_RIGHT);
          delay(50);
          Mouse.release(MOUSE_RIGHT);
          Serial.println("OK");
        }
        else if (command.startsWith("P")) {  // Ping
          Serial.println("PONG");
        }
        else {
          Serial.println("UNKNOWN");
        }
      }
      delay(1);
    }
    """)
    
    print("\n3. After uploading, specify the correct COM port below")
    
    # Get the COM port from the user
    port = input("\nEnter the Arduino COM port (e.g., COM3): ").strip()
    if not port:
        port = "COM3"  # Default
        print(f"Using default port: {port}")
    
    # Create and run the controller
    arduino_controller = ArduinoController(port=port)
    
    # Connect to Arduino
    if arduino_controller.connect_to_arduino():
        print("\nStarting aim assist with Arduino control...")
        time.sleep(2)
        arduino_controller.run()
    else:
        print("\nFailed to connect to Arduino. Please check your connection and try again.")
        input("Press Enter to exit...") 