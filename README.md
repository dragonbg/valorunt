# Valorant Aim Assist (Educational Purposes Only)

This is an educational project demonstrating computer vision techniques for detecting and tracking targets in a game environment. This program is designed for **offline use only** and should not be used in online competitive environments as it may violate terms of service.

## Features

- Real-time screen capture and analysis
- Color-based enemy detection (looks for red highlight colors)
- Aim smoothing for natural movement
- Multiple modes of operation
- Adjustable settings
- Toggle functionality

## Modes of Operation

1. **Standard Aim Assist** (`valorant.py`): Assists with aiming by detecting enemies and moving the crosshair
2. **Triggerbot** (`triggerbot.py`): Automatically fires when an enemy is detected under the crosshair
3. **Arduino Control** (`arduino_controller.py`): Uses an Arduino microcontroller to control mouse input, bypassing software input detection
4. **Enhanced Aim Assist** (`enhanced_aimassist.py`): Advanced aim assist with multiple input methods to bypass detection without requiring Arduino hardware

## Requirements

- Python 3.7+
- The following Python packages (included in requirements.txt):
  - opencv-python
  - numpy
  - pywin32
  - mss (screen capture)
  - keyboard
  - mouse
  - pyserial (for Arduino mode)
- For Arduino mode: Arduino Leonardo or Pro Micro with Mouse library support

## Installation

1. Clone or download this repository
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. For Arduino mode, upload the sketch provided in `arduino_controller.py` to your Arduino board

## Usage

### Standard Aim Assist
```
python valorant.py
```
Controls:
- Hold SHIFT to activate aim assistance
- Press F2 to toggle aim assist on/off
- Press F3 to toggle debug visualization
- Press END to exit the program
- Press CTRL+ALT+D to toggle between direct/indirect mouse input

### Triggerbot
```
python triggerbot.py
```
Controls:
- Press F2 to toggle triggerbot on/off
- Press F3 to toggle debug visualization
- Press END to exit the program
- NUMPAD+/- to adjust detection sensitivity

### Arduino Control Mode
```
python arduino_controller.py
```
Controls:
- Follow the setup instructions to prepare your Arduino
- Hold SHIFT to activate aim assistance
- Press F2 to toggle aim assist on/off
- Press F3 to toggle debug visualization
- Press END to exit the program

### Enhanced Aim Assist (No Arduino)
```
python enhanced_aimassist.py
```
Controls:
- Hold SHIFT to activate aim assistance
- Press F2 to toggle aim assist on/off
- Press F3 to toggle debug visualization
- Press END to exit the program
- Press CTRL+ALT+M to cycle through input methods
- Press CTRL+ALT+H to toggle movement humanization
- Press CTRL+ALT+S to toggle movement stagger
- Press CTRL+ALT+P to cycle through movement patterns

## Calibration

To calibrate the color detection for optimal performance:
```
python calibration.py
```

This will help you find the best HSV color ranges for detecting enemies in your specific game settings.

## Customization

You can modify settings in the `config.py` file:

- Color detection ranges
- Performance settings
- Input sensitivity
- Keybindings
- Debug options

## Why Enhanced Aim Assist?

The Enhanced Aim Assist mode (`enhanced_aimassist.py`) uses several advanced techniques to bypass anti-cheat detection without requiring Arduino hardware:

- Multiple input methods (direct, SendInput, SetCursorPos, events)
- Human-like movement patterns with acceleration and deceleration
- Simulated mouse inertia and natural movement jitter
- Intermittent assistance to avoid detection patterns
- Movement staggering to mimic human hand movements
- Window focus detection for Valorant

This provides a powerful alternative for users who don't have access to an Arduino but still want effective aim assistance with anti-detection features.

## Why Arduino Mode?

Some games implement anti-cheat systems that detect direct input manipulation through software. The Arduino approach uses hardware input instead, making it harder to detect. This method is provided for educational purposes to demonstrate the concept of hardware-based input control.

## Disclaimer

This software is provided for **EDUCATIONAL PURPOSES ONLY**. The creators do not endorse or encourage cheating in online games. Use of this software in online multiplayer environments may violate terms of service and could result in your account being banned. Use responsibly and at your own risk.

## Educational Value

This project demonstrates:
- Computer vision techniques with OpenCV
- Color detection and tracking
- Multi-threading in Python
- User input handling
- Screen capture methods
- Hardware-software interaction (Arduino mode)
- Anti-detection techniques 