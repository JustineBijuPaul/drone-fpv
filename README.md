# Drone Human Detection System

A real-time human detection system for drone operations using YOLOv8 computer vision model. The system processes live camera feeds from drones to detect and identify human figures, with laptop camera fallback for development and testing.

## Features

- Real-time human detection using YOLOv8
- Support for drone receiver feeds and laptop camera
- Automatic camera source switching and fallback
- Visual feedback with bounding boxes and confidence scores
- Configurable detection parameters
- Error handling and recovery mechanisms

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the system with default settings:
```bash
python main.py
```

Specify camera source and parameters:
```bash
python main.py --camera-source laptop --confidence 0.6 --resolution 1280x720
```

## Command Line Options

- `--camera-source`: Camera source (auto, laptop, drone) - default: auto
- `--device-id`: Camera device ID - default: 0
- `--confidence`: Detection confidence threshold - default: 0.5
- `--resolution`: Camera resolution (WxH) - default: 640x480

## Controls

- Press 'q' or ESC to quit the application
- Press 'c' to switch camera sources (when available)

## Quick start

Run the application with Python 3.12+:

```bash
python3 main.py --camera-source laptop --resolution 640x480 --confidence 0.5
```

Keyboard controls while running:
- 'q' or ESC: quit the application
- 'c': switch camera source (drone <-> laptop)

## Requirements

- Python 3.8+
- OpenCV 4.8+
- YOLOv8 (ultralytics)
- NumPy
- PyTorch

## Project Structure

```
drone_detection/
├── __init__.py          # Package initialization
├── models.py            # Data models and configurations
├── camera_manager.py    # Camera input management
├── human_detector.py    # YOLOv8 detection logic
└── display_manager.py   # Video display and UI
main.py                  # Application entry point
requirements.txt         # Python dependencies
```