# Water Gun Project Notes

## Project Overview

The project is split into two phases:

### Step 1: Detection + Logging

Build a local prototype that uses a Mac camera feed to detect a person and perform a software-only logging action.

Goals:
- Detect a human in the camera feed.
- Record a timestamped log entry.
- Avoid any hardware control at this stage.

### Step 2: Detection + Water Shooting Hardware

Extend the same detection pipeline by replacing the software-only action with hardware control and safety checks.

Goals:
- Keep the detection pipeline from step 1.
- Add hardware actuation later.
- Require safety checks before actuation.

## Step 1 Objective

Build a local prototype that:
- Uses the Mac camera.
- Runs the model locally.
- Detects the label `person` or `human`.
- Writes detections to a log file or terminal.
- Does not use servos, pumps, relays, or other hardware.

## Step 1 Implementation Plan

1. Create a small Python app that reads frames from the Mac camera.
2. Run a local image detection model on each frame.
3. Check whether a person is detected above a confidence threshold.
4. Debounce repeated detections so the log does not spam every frame.
5. Write a timestamped log entry when a new detection event occurs.
6. Add simple configuration for camera index, labels, threshold, and cooldown.
7. Test in normal room lighting with one person entering and leaving frame.

## Recommended Model Direction

Start with a standard person detector rather than open-vocabulary detection.

Reason:
- Faster and simpler on an 8GB Mac.
- Better for a first end-to-end prototype.
- Easier to swap later if needed.

Candidate model choices:
- First pass: YOLO person detection.
- Second pass if needed: open-vocabulary zero-shot detection with OWLv2 or similar.

## Step 1 Success Criteria

- The app opens the Mac camera.
- It detects a person in view.
- It logs a single event per detection window instead of spamming.
- It runs locally without extra hardware.

## Current Step 1 Files

- `detect_and_log.py`: webcam detection app.
- `requirements.txt`: Python dependencies.
- `detections.log`: created at runtime.

## Current Run Instructions

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Run `python3 detect_and_log.py`.

Example:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 detect_and_log.py
```
