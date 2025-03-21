"""
Main launcher for Valorant Aim Assist (Educational Purposes Only)
This launches the different modes of the aim assist program.
"""

import os
import sys
import subprocess
import time

def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the program header"""
    clear_screen()
    print("=" * 70)
    print("                  VALORANT AIM ASSIST (EDUCATIONAL ONLY)")
    print("=" * 70)
    print("DISCLAIMER: This software is for EDUCATIONAL PURPOSES ONLY.")
    print("Using this in online games may violate terms of service and result in bans.")
    print("=" * 70)
    print()

def print_menu():
    """Print the main menu options"""
    print("Available Modes:")
    print("1. Standard Aim Assist")
    print("2. Triggerbot")
    print("3. Arduino Controller")
    print("4. Enhanced Aim Assist (No Arduino)")
    print("5. Color Calibration Tool")
    print("6. Exit")
    print()

def run_module(module_name, description):
    """Run a specific Python module"""
    print(f"Starting {description}...")
    time.sleep(1)
    
    try:
        # Use sys.executable to ensure the same Python interpreter is used
        subprocess.run([sys.executable, module_name])
    except KeyboardInterrupt:
        print(f"\n{description} was terminated by the user.")
    except Exception as e:
        print(f"\nError running {description}: {e}")
    
    input("\nPress Enter to return to the main menu...")

def main():
    """Main function that displays menu and handles user input"""
    while True:
        print_header()
        print_menu()
        
        choice = input("Select a mode (1-6): ").strip()
        
        if choice == "1":
            run_module("valorant.py", "Standard Aim Assist")
        elif choice == "2":
            run_module("triggerbot.py", "Triggerbot")
        elif choice == "3":
            run_module("arduino_controller.py", "Arduino Controller")
        elif choice == "4":
            run_module("enhanced_aimassist.py", "Enhanced Aim Assist")
        elif choice == "5":
            run_module("calibration.py", "Color Calibration Tool")
        elif choice == "6":
            print("\nExiting program. Thank you for using this educational tool.")
            time.sleep(1)
            break
        else:
            print("\nInvalid choice. Please enter a number between 1 and 6.")
            time.sleep(1.5)

if __name__ == "__main__":
    main() 