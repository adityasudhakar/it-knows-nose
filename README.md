# It Knows Nose

It Knows Nose is a small computer-vision and robotics prototype. A webcam detects a person's nose with Ultralytics YOLO pose estimation, then a Python script converts that nose position into pan/tilt commands for two Arduino-controlled SG90 servos.

The project started as person detection and servo sweep experiments, then evolved into a nose-tracking pan/tilt pointer.

## What It Does

- Captures webcam frames on a Mac.
- Uses `yolov8n-pose.pt` to find the nose keypoint.
- Smooths the detected nose position.
- Converts camera pixel error into servo angle commands.
- Sends compact serial commands like `87,35` to an Arduino.
- Drives two servos:
  - pin 9: pan, `0..180`
  - pin 10: tilt, clamped to `10..90`

## Demo Videos

- [Robot greeter demo 1](docs/videos/robot-greeter-demo-1.mov)
- [Robot greeter demo 2](docs/videos/robot-greeter-demo-2.mov)

## Hardware

- Mac with webcam
- Arduino Uno
- Two SG90 servos
- Pan/tilt pointer mechanism
- External servo power recommended

## Software

- `track_nose_to_servos.py`: live nose tracking to pan/tilt servo commands
- `arduino/dual_servo_position_serial/`: Arduino sketch that accepts `pan,tilt`
- `detect_and_log.py`: earlier person-detection logger
- `detect_and_actuate.py`: earlier detection-triggered servo sweep

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Upload the Arduino sketch:

```bash
arduino-cli compile --fqbn arduino:avr:uno arduino/dual_servo_position_serial
arduino-cli upload -p /dev/cu.usbmodem14701 --fqbn arduino:avr:uno arduino/dual_servo_position_serial
```

Run the tracker:

```bash
./.venv/bin/python track_nose_to_servos.py --camera-index 0 --arduino-port /dev/cu.usbmodem14701
```

More responsive tuning used during testing:

```bash
./.venv/bin/python track_nose_to_servos.py \
  --camera-index 0 \
  --arduino-port /dev/cu.usbmodem14701 \
  --pan-gain -0.08 \
  --tilt-gain -0.08 \
  --deadband-px 15 \
  --max-step 8 \
  --smooth-alpha 0.35 \
  --update-hz 20
```

## Notes

The YOLO model files are downloaded at runtime and ignored by Git. The project keeps the Arduino simple: it receives final servo angles, while Python handles vision, smoothing, limits, and tuning.

## Demo

Nose-tracking pan/tilt servo prototype demo:

[Watch the demo video](assets/nose-tracking-demo-2026-06-03.mp4)

