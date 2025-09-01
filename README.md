# Drone Human Detection System

A comprehensive real-time human detection system for drone operations using YOLOv8 computer vision model. The system processes live camera feeds from drones to detect and identify human figures, with laptop camera fallback for development and testing.

## System Architecture Overview

This system is designed as a modular, fault-tolerant application with comprehensive error handling and recovery mechanisms. It follows a multi-component architecture where each component has specific responsibilities and communicates through well-defined interfaces.

### Core Components

1. **MainController**: Central orchestration hub that manages all components
2. **CameraManager**: Handles camera input from drone receivers or laptop cameras
3. **HumanDetector**: YOLOv8-based computer vision for human detection
4. **DisplayManager**: Video output and user interface management
5. **PerformanceMonitor**: Real-time performance tracking and optimization

## System Flow Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│   Application   │    │   Command Line   │    │   Configuration    │
│   Entry Point   │───▶│   Argument       │───▶│   Parsing &        │
│   (main.py)     │    │   Processing     │    │   Validation       │
└─────────────────┘    └──────────────────┘    └────────────────────┘
         │                                                │
         ▼                                                ▼
┌─────────────────┐                              ┌────────────────────┐
│  MainController │                              │   Camera Config    │
│  Initialization │◀─────────────────────────────│   Setup (Drone/    │
│                 │                              │   Laptop)          │
└─────────────────┘                              └────────────────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│   Component     │    │   Camera         │    │   Human Detector   │
│   Initialization│───▶│   Manager        │───▶│   (YOLOv8)         │
│                 │    │   Setup          │    │   Initialization   │
└─────────────────┘    └──────────────────┘    └────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│   Display       │    │   Performance    │    │   Error Handling   │
│   Manager       │    │   Monitor        │    │   & Recovery       │
│   Setup         │    │   Setup          │    │   System Setup     │
└─────────────────┘    └──────────────────┘    └────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        MAIN PROCESSING LOOP                        │
│                                                                     │
│  ┌───────────────┐    ┌──────────────┐    ┌─────────────────────┐  │
│  │ Performance   │───▶│ Frame Skip   │───▶│ Camera Connection   │  │
│  │ Check         │    │ Decision     │    │ Verification        │  │
│  └───────────────┘    └──────────────┘    └─────────────────────┘  │
│           │                 │                        │             │
│           ▼                 ▼                        ▼             │
│  ┌───────────────┐    ┌──────────────┐    ┌─────────────────────┐  │
│  │ Continue      │    │ Skip Frame   │    │ Frame Capture       │  │
│  │ Processing    │    │ & Record     │    │ from Camera         │  │
│  └───────────────┘    └──────────────┘    └─────────────────────┘  │
│           │                 │                        │             │
│           ▼                 ▼                        ▼             │
│  ┌───────────────┐    ┌──────────────┐    ┌─────────────────────┐  │
│  │ Human         │    │ Performance  │    │ Error Recovery      │  │
│  │ Detection     │    │ Tracking     │    │ (if frame is null)  │  │
│  │ (YOLOv8)      │    │              │    │                     │  │
│  └───────────────┘    └──────────────┘    └─────────────────────┘  │
│           │                                         │             │
│           ▼                                         ▼             │
│  ┌───────────────┐    ┌──────────────┐    ┌─────────────────────┐  │
│  │ Bounding Box  │    │ Display      │    │ Camera Switch/      │  │
│  │ Calculation   │    │ Frame with   │    │ Component Restart   │  │
│  │ & Confidence  │    │ Detections   │    │ Recovery Actions    │  │
│  └───────────────┘    └──────────────┘    └─────────────────────┘  │
│           │                 │                        │             │
│           ▼                 ▼                        ▼             │
│  ┌───────────────┐    ┌──────────────┐    ┌─────────────────────┐  │
│  │ FPS Counter   │    │ Keyboard     │    │ Error Counter       │  │
│  │ Update        │    │ Input Check  │    │ & Recovery Attempt  │  │
│  │               │    │ (q/ESC/c)    │    │ Tracking            │  │
│  └───────────────┘    └──────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│   Continue      │    │   Camera Switch  │    │   Graceful         │
│   Loop          │    │   (c key)        │    │   Shutdown         │
│                 │    │                  │    │   (q/ESC key)      │
└─────────────────┘    └──────────────────┘    └────────────────────┘
```

## Detailed Step-by-Step Process Explanation

### Phase 1: Application Initialization

1. **Command Line Processing** (`main.py`)
   - Parse command-line arguments (camera source, resolution, confidence, FPS, GUI options)
   - Validate resolution format (WxH) and convert to tuple
   - Set up logging configuration with timestamps and severity levels

2. **Dependency Validation**
   - Check for OpenCV availability (critical dependency)
   - Validate GUI components if Tkinter display is requested
   - Exit gracefully with error messages if dependencies are missing

3. **Controller Setup**
   - Initialize MainController instance as central coordinator
   - Configure camera configurations for both drone and laptop sources
   - Set up error handling with exponential backoff and recovery strategies

### Phase 2: Component Initialization

4. **Camera Manager Setup** (`CameraManager`)
   - Initialize camera connections based on source priority (auto/drone/laptop)
   - Configure camera parameters (resolution, FPS, timeout values)
   - Test camera connections and establish fallback mechanisms

5. **Human Detector Setup** (`HumanDetector`)
   - Load YOLOv8 model for human detection
   - Set confidence threshold from command line arguments
   - Initialize detection parameters and optimize for real-time processing

6. **Display Manager Setup** (`DisplayManager` or `TkDisplayManager`)
   - Initialize display window for video output
   - Set up keyboard input handling for user controls
   - Configure display parameters and FPS calculation

7. **Performance Monitor Setup** (`PerformanceMonitor`)
   - Initialize performance tracking with target FPS (15 FPS minimum)
   - Set up frame skipping logic for performance optimization
   - Configure memory usage monitoring and optimization suggestions

### Phase 3: Main Processing Loop

8. **Performance Check & Frame Skipping**
   - Check if current performance requires frame skipping
   - Record skipped frames for performance statistics
   - Continue to next iteration if frame should be skipped

9. **Camera Frame Capture**
   - Verify camera connection status
   - Capture frame from active camera source
   - Handle camera disconnection with automatic fallback

10. **Human Detection Processing**
    - Check if detection is enabled and detector is available
    - Apply performance-based quality scaling if needed
    - Run YOLOv8 inference on captured frame
    - Extract bounding boxes, confidence scores, and class information

11. **Display and User Interface**
    - Overlay bounding boxes and confidence scores on frame
    - Display processed frame in window
    - Calculate and display current FPS
    - Check for keyboard input (q/ESC for quit, c for camera switch)

12. **Performance Monitoring**
    - Record frame processing times (capture, detection, display)
    - Update FPS calculations and performance metrics
    - Trigger optimization suggestions if performance degrades

### Phase 4: Error Handling and Recovery

13. **Error Detection and Classification**
    - Monitor for camera connection failures
    - Detect model loading errors
    - Track frame processing failures
    - Identify display system errors
    - Monitor memory usage issues

14. **Recovery Strategies**
    - **Camera Failures**: Automatic switch between drone and laptop cameras
    - **Detection Errors**: Continue with display-only mode
    - **Display Failures**: Attempt display manager restart
    - **Memory Issues**: Trigger garbage collection and optimization
    - **Consecutive Errors**: Escalate to component restart or graceful shutdown

15. **Logging and Diagnostics**
    - Exponential backoff logging to prevent log flooding
    - Per-error-type rate limiting for repeated errors
    - Comprehensive error tracking with timestamps
    - Recovery attempt monitoring with maximum retry limits

### Phase 5: Shutdown and Cleanup

16. **Graceful Shutdown Process**
    - Stop performance monitoring threads
    - Release camera resources
    - Close display windows
    - Clean up detection model memory
    - Log shutdown completion

## Error Recovery Flow

```
Error Detected
      │
      ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Log Error     │────▶│   Increment      │────▶│   Check Error   │
│   with Backoff  │     │   Error Counter  │     │   Type & Count  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                        ┌──────────────────┐              ▼
                        │   Camera Error   │     ┌─────────────────┐
                        │   → Try Switch   │◀────│   Determine     │
                        └──────────────────┘     │   Recovery      │
                        ┌──────────────────┐     │   Strategy      │
                        │   Model Error    │◀────│                 │
                        │   → Restart      │     └─────────────────┘
                        │   Component      │              │
                        └──────────────────┘              ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │   Display Error  │◀────│   Execute       │
                        │   → Restart      │     │   Recovery      │
                        │   Display        │     │   Action        │
                        └──────────────────┘     └─────────────────┘
                        ┌──────────────────┐              │
                        │   Max Errors     │              ▼
                        │   → Graceful     │     ┌─────────────────┐
                        │   Shutdown       │◀────│   Recovery      │
                        └──────────────────┘     │   Success?      │
                                                 └─────────────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │   Continue      │
                                                 │   Processing    │
                                                 └─────────────────┘
```

## Features

- Real-time human detection using YOLOv8 with 15+ FPS performance
- Automatic camera source switching (drone receiver ↔ laptop camera)
- Comprehensive error handling with exponential backoff logging
- Performance monitoring with adaptive frame skipping
- Visual feedback with bounding boxes and confidence scores
- Configurable detection parameters and resolution settings
- Memory usage optimization and cleanup strategies
- Graceful shutdown and resource management

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd drone-fpv-detection
```

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
python main.py --camera-source laptop --confidence 0.6 --resolution 1280x720 --fps 30
```

Run with Tkinter GUI display:
```bash
python main.py --gui --camera-source auto --resolution 640x480
```

## Command Line Options

- `--camera-source`: Camera source selection
  - `auto` (default): Automatic detection with drone priority, laptop fallback
  - `laptop`: Force laptop/webcam usage
  - `drone`: Force drone receiver usage
- `--device-id`: Camera device ID (default: 0)
- `--confidence`: Detection confidence threshold (0.0-1.0, default: 0.5)
- `--resolution`: Camera resolution in WxH format (default: 640x480)
- `--fps`: Target frames per second (default: 30)
- `--gui`: Enable Tkinter-based GUI display (optional)

## Runtime Controls

- **'q' or ESC**: Quit the application gracefully
- **'c'**: Switch camera sources (drone ↔ laptop) when both are available

## Performance Optimization

The system includes several performance optimization features:

1. **Adaptive Frame Skipping**: Automatically skips frames when processing falls below 15 FPS
2. **Quality Scaling**: Reduces detection frame resolution when performance is poor
3. **Memory Management**: Automatic garbage collection and memory usage monitoring
4. **Error Recovery**: Intelligent recovery strategies for various failure scenarios

## Quick Start Examples

### Basic laptop camera detection:
```bash
python3 main.py --camera-source laptop --resolution 640x480 --confidence 0.5
```

### High-resolution drone detection:
```bash
python3 main.py --camera-source drone --resolution 1280x720 --confidence 0.7 --fps 30
```

### Auto-detection with GUI:
```bash
python3 main.py --gui --resolution 800x600 --confidence 0.6
```

### Development testing:
```bash
python3 main.py --camera-source auto --confidence 0.3 --fps 15
```

## System Requirements

### Hardware Requirements:
- **CPU**: Multi-core processor (Intel i5/AMD Ryzen 5 or better recommended)
- **RAM**: Minimum 4GB, 8GB+ recommended for optimal performance
- **Camera**: USB webcam or drone receiver with video output capability
- **Display**: Monitor for real-time video display

### Software Requirements:
- **Python**: 3.8+ (Python 3.12+ recommended for best performance)
- **OpenCV**: 4.8+ for computer vision operations
- **YOLOv8**: Latest ultralytics package for human detection
- **NumPy**: For numerical array operations
- **PyTorch**: Backend for YOLOv8 model inference
- **Tkinter**: Optional, for GUI display mode (usually included with Python)

## Project Structure

```
drone-fpv-detection/
├── main.py                          # Application entry point and CLI handling
├── requirements.txt                 # Python package dependencies
├── README.md                        # This comprehensive documentation
├── drone_detection/                 # Core detection package
│   ├── __init__.py                  # Package initialization
│   ├── models.py                    # Data models and configurations
│   ├── main_controller.py           # Central orchestration and error handling
│   ├── camera_manager.py            # Camera input management and fallback
│   ├── human_detector.py            # YOLOv8 detection logic and inference
│   ├── display_manager.py           # OpenCV-based video display and UI
│   ├── tk_display_manager.py        # Tkinter-based GUI display (optional)
│   └── performance_monitor.py       # Performance tracking and optimization
├── test_*.py                        # Comprehensive test suite
└── logs/                            # Application logs (created at runtime)
```

## Component Details

### MainController (`main_controller.py`)
- **Central orchestration hub** managing all system components
- **Error handling** with exponential backoff and recovery strategies  
- **Performance monitoring** integration with adaptive optimization
- **Signal handling** for graceful shutdown on interrupts
- **Resource management** ensuring proper cleanup on exit

### CameraManager (`camera_manager.py`)
- **Multi-source support** for drone receivers and laptop cameras
- **Automatic fallback** when primary camera source fails
- **Connection testing** with configurable timeout periods
- **Resolution and FPS configuration** with validation
- **Hot-swapping** capability for runtime camera switching

### HumanDetector (`human_detector.py`)
- **YOLOv8 integration** for state-of-the-art human detection
- **Confidence threshold** configuration for accuracy tuning
- **Batch processing** optimization for multiple detections
- **Model caching** to avoid repeated loading overhead
- **Performance scaling** with quality-based frame reduction

### DisplayManager (`display_manager.py`)
- **Real-time video display** with OpenCV backend
- **Bounding box overlay** with confidence scores
- **FPS calculation** and performance indicators
- **Keyboard input handling** for user controls
- **Window management** with proper resource cleanup

### PerformanceMonitor (`performance_monitor.py`)
- **Real-time FPS tracking** with rolling averages
- **Frame skip logic** to maintain target performance (15+ FPS)
- **Memory usage monitoring** with cleanup recommendations
- **Processing time analysis** for bottleneck identification
- **Adaptive quality control** for performance optimization

## Troubleshooting

### Common Issues:

1. **Camera not detected**:
   - Check USB connections and camera permissions
   - Try different `--device-id` values (0, 1, 2, etc.)
   - Use `--camera-source laptop` to force webcam usage

2. **Low FPS performance**:
   - Reduce resolution: `--resolution 320x240`
   - Lower confidence threshold: `--confidence 0.3`
   - Enable automatic frame skipping (enabled by default)

3. **Model loading errors**:
   - Ensure internet connection for initial YOLOv8 download
   - Check available disk space (models require ~50MB)
   - Verify PyTorch installation

4. **Display issues**:
   - Install OpenCV with GUI support: `pip install opencv-python`
   - For headless systems, consider using `--gui` flag with X11 forwarding
   - Check display environment variables on Linux systems

### Debug Mode:
Enable verbose logging by setting environment variable:
```bash
export PYTHONPATH=$PYTHONPATH:. 
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python main.py --camera-source laptop
```

## Development and Testing

The project includes a comprehensive test suite covering:
- **Unit tests** for individual components
- **Integration tests** for complete pipeline testing
- **Error recovery tests** for failure scenario validation
- **Performance tests** for FPS and optimization validation

Run the test suite:
```bash
python -m pytest test_*.py -v
```

## License and Contributing

This project is designed for educational and research purposes. Contributions are welcome through pull requests with comprehensive test coverage.