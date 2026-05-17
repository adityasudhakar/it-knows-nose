from __future__ import annotations

import argparse
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
from serial import Serial
from ultralytics import YOLO


PERSON_CLASS_ID = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect people from a webcam feed and trigger a 5-cycle dual-servo Arduino sweep."
    )
    parser.add_argument("--camera-index", type=int, default=0, help="Webcam device index.")
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        help="YOLO model name or path. Default is a small pretrained model.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="Minimum confidence required for a person detection.",
    )
    parser.add_argument(
        "--arduino-port",
        default="/dev/cu.usbmodem14701",
        help="Arduino serial port.",
    )
    parser.add_argument(
        "--baud-rate",
        type=int,
        default=115200,
        help="Arduino serial baud rate.",
    )
    parser.add_argument(
        "--show-window",
        action="store_true",
        help="Display the camera preview window.",
    )
    parser.add_argument(
        "--detect-frames",
        type=int,
        default=2,
        help="Consecutive person-detected frames required before triggering.",
    )
    parser.add_argument(
        "--lost-frames",
        type=int,
        default=5,
        help="Consecutive no-person frames required before stopping.",
    )
    return parser.parse_args()


def has_person(result, confidence_threshold: float) -> bool:
    if result.boxes is None:
        return False

    for box in result.boxes:
        class_id = int(box.cls[0].item())
        confidence = float(box.conf[0].item())
        if class_id == PERSON_CLASS_ID and confidence >= confidence_threshold:
            return True
    return False


def open_camera(camera_index: int) -> cv2.VideoCapture:
    if platform.system() == "Darwin":
        return cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
    return cv2.VideoCapture(camera_index)


def wait_for_frame(camera: cv2.VideoCapture, attempts: int = 20, delay: float = 0.1):
    for _ in range(attempts):
        ok, frame = camera.read()
        if ok:
            return frame
        time.sleep(delay)
    return None


class ServoController:
    def __init__(self, port: str, baud_rate: int) -> None:
        self.serial = Serial(port, baud_rate, timeout=1)
        # Arduino resets when serial opens; give it a moment to boot.
        time.sleep(2)
        self.sweeping = False

    def start_sweep(self) -> None:
        if not self.sweeping:
            self.serial.write(b"SWEEP\n")
            self.serial.flush()
            self.sweeping = True
            print(f"{datetime.now().isoformat(timespec='seconds')} person detected; dual-servo 5x sweep triggered")

    def stop_sweep(self) -> None:
        if self.sweeping:
            self.serial.write(b"STOP\n")
            self.serial.flush()
            self.sweeping = False
            print(f"{datetime.now().isoformat(timespec='seconds')} person lost; stop command sent")

    def close(self) -> None:
        try:
            self.stop_sweep()
        finally:
            self.serial.close()


def main() -> int:
    args = parse_args()

    print(f"Loading model: {args.model}")
    model = YOLO(args.model)

    print(f"Opening Arduino on {args.arduino_port}")
    servo = ServoController(args.arduino_port, args.baud_rate)

    print(f"Opening camera index {args.camera_index}")
    camera = open_camera(args.camera_index)
    if not camera.isOpened():
        print(f"Could not open camera index {args.camera_index}", file=sys.stderr)
        servo.close()
        return 1

    frame = wait_for_frame(camera)
    if frame is None:
        print(
            f"Camera index {args.camera_index} opened but did not return frames.",
            file=sys.stderr,
        )
        camera.release()
        servo.close()
        return 1

    print("Press Ctrl+C to stop.")
    if args.show_window:
        print("Press q in the preview window to stop.")

    person_present = False
    detected_frame_count = 0
    lost_frame_count = 0

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Failed to read frame from camera.", file=sys.stderr)
                return 1

            result = model.predict(frame, verbose=False)[0]
            detected = has_person(result, args.confidence)

            if detected:
                detected_frame_count += 1
                lost_frame_count = 0
            else:
                lost_frame_count += 1
                detected_frame_count = 0

            if not person_present and detected_frame_count >= args.detect_frames:
                person_present = True
                servo.start_sweep()
            elif person_present and lost_frame_count >= args.lost_frames:
                person_present = False
                servo.stop_sweep()

            if args.show_window:
                annotated = result.plot()
                cv2.imshow("YOLO Person Detection Servo Actuation", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        camera.release()
        cv2.destroyAllWindows()
        servo.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
