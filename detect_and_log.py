from __future__ import annotations

import argparse
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
from ultralytics import YOLO


PERSON_CLASS_ID = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect people from a webcam feed and log new detection events."
    )
    parser.add_argument("--camera-index", type=int, default=1, help="Webcam device index.")
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
        "--cooldown",
        type=float,
        default=5.0,
        help="Seconds to wait before logging another event while a person is still around.",
    )
    parser.add_argument(
        "--log-file",
        default="detections.log",
        help="Path to the log file.",
    )
    parser.add_argument(
        "--show-window",
        action="store_true",
        help="Display the camera preview window.",
    )
    return parser.parse_args()


def append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


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
    # AVFoundation is the native macOS backend and is more reliable here than
    # letting OpenCV choose a backend implicitly.
    if platform.system() == "Darwin":
        return cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
    return cv2.VideoCapture(camera_index)


def wait_for_frame(camera: cv2.VideoCapture, attempts: int = 20, delay: float = 0.1):
    for attempt in range(1, attempts + 1):
        ok, frame = camera.read()
        if ok:
            return frame
        time.sleep(delay)
    return None


def main() -> int:
    args = parse_args()
    log_path = Path(args.log_file).resolve()

    print(f"Loading model: {args.model}")
    model = YOLO(args.model)

    print(f"Opening camera index {args.camera_index}")
    camera = open_camera(args.camera_index)
    if not camera.isOpened():
        print(f"Could not open camera index {args.camera_index}", file=sys.stderr)
        return 1

    frame = wait_for_frame(camera)
    if frame is None:
        print(
            f"Camera index {args.camera_index} opened but did not return frames.",
            file=sys.stderr,
        )
        return 1

    last_logged_at = 0.0
    person_present = False

    print("Press Ctrl+C to stop.")
    if args.show_window:
        print("Press q in the preview window to stop.")

    try:
        while True:
            ok, next_frame = camera.read()
            if not ok:
                print("Failed to read frame from camera.", file=sys.stderr)
                return 1
            frame = next_frame

            result = model.predict(frame, verbose=False)[0]
            detected = has_person(result, args.confidence)
            now = time.time()

            if detected and (not person_present or now - last_logged_at >= args.cooldown):
                timestamp = datetime.now().isoformat(timespec="seconds")
                message = f"{timestamp} detected person"
                print(message)
                append_log(log_path, message)
                last_logged_at = now

            person_present = detected

            if args.show_window:
                annotated = result.plot()
                cv2.imshow("Water Gun Step 1", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        camera.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
