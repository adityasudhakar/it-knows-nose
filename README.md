# Person Detection With Ultralytics YOLO

This project is a local prototype that uses a Mac camera and Ultralytics YOLO to detect when a person is in frame, then optionally trigger Arduino-controlled servo motion.

The story is staged deliberately:
- Phase 1 proved the "eyes": live camera person detection and timestamped logging.
- Phase 2, **Robot Greeter**, connects those eyes to motion by sending serial commands to an Arduino that drives servos.

## Current Scope

The repo now supports two modes:
- Software-only detection and logging.
- Person detection with Arduino serial actuation.

What Phase 1 does:
- Opens a local camera feed on macOS.
- Runs a pre-trained Ultralytics YOLO model locally.
- Detects the `person` class above a confidence threshold.
- Logs detection events with timestamps.

What Phase 2 adds:
- Opens an Arduino serial connection.
- Requires a person to be detected for multiple consecutive frames before triggering.
- Sends `SWEEP` when a person is confirmed.
- Sends `STOP` when the person is lost for multiple frames.
- Drives one-servo and dual-servo Arduino sweep sketches.

This is still a prototype. It currently demonstrates detection-driven servo movement, not a finished autonomous water system.

## Phase 2: Robot Greeter

Robot Greeter is the hardware-actuation phase. The same YOLO detector from Phase 1 now controls physical motion through an Arduino.

The current dual-servo demo performs a 5-cycle sweep when a person is detected. This keeps the hardware behavior bounded while validating that camera detection can trigger repeatable physical movement.

Demo videos:

- [Robot Greeter demo 1](docs/videos/robot-greeter-demo-1.mov)
- [Robot Greeter demo 2](docs/videos/robot-greeter-demo-2.mov)

## Why This Design

The project starts with a standard person detector rather than an open-vocabulary model.

Reasons:
- It is simpler to get working end to end on a Mac.
- It is lighter-weight for a first prototype.
- It gives a stable baseline before introducing hardware or more flexible vision models.

YOLO was chosen for the first pass because it is fast, well-supported, and already strong enough for the narrow requirement here: "is there a person in frame or not?"

## Implementation Notes

The software-only app is `detect_and_log.py`.

It currently supports:
- configurable camera index
- configurable confidence threshold
- configurable cooldown between logged events
- optional preview window with bounding boxes

The hardware actuation app is `detect_and_actuate.py`.

It currently supports:
- configurable camera index
- configurable confidence threshold
- configurable Arduino serial port
- configurable serial baud rate
- configurable consecutive detected-frame threshold
- configurable consecutive lost-frame threshold
- optional preview window with bounding boxes

The camera index is configurable because different machines can expose different video devices.

## Repository Layout

- `detect_and_log.py`: webcam detection app
- `detect_and_actuate.py`: webcam detection plus Arduino serial actuation app
- `arduino/servo2_sweep_serial/`: one-servo serial sweep sketch
- `arduino/dual_servo_sweep_serial/`: dual-servo bounded sweep sketch
- `requirements.txt`: Python dependencies
- `notes.md`: consolidated local project notes and planning
- `docs/videos/`: demo videos

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Phase 1: Detection and Logging

Default run:

```bash
./.venv/bin/python detect_and_log.py
```

Run with preview window:

```bash
./.venv/bin/python detect_and_log.py --show-window
```

Useful options:

```bash
./.venv/bin/python detect_and_log.py --camera-index 0
./.venv/bin/python detect_and_log.py --confidence 0.5
./.venv/bin/python detect_and_log.py --cooldown 5
```

## Run Phase 2: Robot Greeter

1. Upload an Arduino sketch from `arduino/` to the connected board.
2. Confirm the Arduino serial port.
3. Run the actuation app:

```bash
./.venv/bin/python detect_and_actuate.py --arduino-port /dev/cu.usbmodem14701 --show-window
```

Useful options:

```bash
./.venv/bin/python detect_and_actuate.py --camera-index 0
./.venv/bin/python detect_and_actuate.py --confidence 0.5
./.venv/bin/python detect_and_actuate.py --detect-frames 2
./.venv/bin/python detect_and_actuate.py --lost-frames 5
```

## Expected Behavior

In Phase 1, when the app sees a person, it prints and logs a line like:

```text
2026-05-17T00:01:01 detected person
```

Runtime logs are written to `detections.log` when detections occur.

In Phase 2, when the app confirms a person, it sends `SWEEP` to the Arduino and prints a line like:

```text
2026-05-17T00:01:01 person detected; dual-servo 5x sweep triggered
```

When the person is lost for the configured number of frames, it sends `STOP`.

## Current Detection Screenshot

This screenshot was captured from the live preview while testing in a dim room:

![YOLO person detection demo](docs/camera-detection-demo.png)

## Validation So Far

The prototype has already been validated locally with:
- live webcam activation
- person detection in a dim room
- timestamped detection logging
- repeated detection tests by covering and uncovering the camera
- Arduino serial commands from Python
- one-servo sweep testing
- dual-servo 5-cycle sweep testing
- detection-triggered servo motion shown in the Robot Greeter demo videos

## Behavioral Notes

One behavioral note from testing: the current cooldown logic can retrigger while a person remains continuously present after the cooldown expires. That is acceptable for a first pass, but not ideal if the intended behavior is "log only when a person disappears and reappears."

## Future Plan

### Later: Detection + Water Shooting Hardware

Robot Greeter validates detection-triggered motion. A later phase can decide whether to add pump, relay, or water actuation hardware.

Planned additions:
- safety checks before actuation
- retention of the same detection pipeline from step 1

## Notes

The fuller working notes for this prototype are in `notes.md`.
