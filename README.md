# Valorant Aim Assist (Educational Purposes Only)

This is an educational project demonstrating computer vision techniques for detecting and tracking targets in a game environment. This program is designed for **offline use only** and should not be used in online competitive environments as it may violate terms of service.

## Features

- Real-time screen capture and analysis
- Color-based enemy detection (looks for red highlight colors)
- Aim smoothing for natural movement
- Adjustable settings
- Toggle functionality

## Requirements

- Python 3.7+
- The following Python packages (included in requirements.txt):
  - opencv-python
  - numpy
  - pywin32
  - mss (screen capture)
  - keyboard
  - mouse

## Installation

1. Clone or download this repository
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Launch the game in windowed mode
2. Run the aim assist program:
   ```
   python start.py
   ```
3. Controls:
   - Hold SHIFT to activate aim assistance
   - Press F2 to toggle aim assist on/off
   - Press END to exit the program

## Customization

You can modify the following settings in the `start.py` file:

- `color_lower` and `color_upper`: HSV color range for enemy detection
- `aim_lock_key`: Key to hold for activating aim
- `toggle_key`: Key to toggle aim assist on/off
- `exit_key`: Key to exit the program
- `scan_region_size`: Size of screen region to scan (lower = better performance)
- `aim_speed`: How quickly the crosshair moves to the target

## Disclaimer

This software is provided for **EDUCATIONAL PURPOSES ONLY**. The creators do not endorse or encourage cheating in online games. Use of this software in online multiplayer environments may violate terms of service and could result in your account being banned. Use responsibly and at your own risk.

## Educational Value

This project demonstrates:
- Computer vision techniques with OpenCV
- Color detection and tracking
- Multi-threading in Python
- User input handling
- Screen capture methods 