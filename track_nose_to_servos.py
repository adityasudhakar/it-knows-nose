from __future__ import annotations

import argparse
import platform
import sys
import time
from datetime import datetime

import cv2
from serial import Serial
from ultralytics import YOLO


NOSE_KEYPOINT_INDEX = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Track the YOLO pose nose keypoint and send pan,tilt angles to Arduino."
    )
    parser.add_argument("--camera-index", type=int, default=1, help="Webcam device index.")
    parser.add_argument(
        "--model",
        default="yolov8n-pose.pt",
        help="YOLO pose model name or path.",
    )
    parser.add_argument("--arduino-port", default="/dev/cu.usbmodem14701", help="Arduino serial port.")
    parser.add_argument("--baud-rate", type=int, default=115200, help="Arduino serial baud rate.")
    parser.add_argument("--confidence", type=float, default=0.5, help="Minimum person box confidence.")
    parser.add_argument("--keypoint-confidence", type=float, default=0.5, help="Minimum nose confidence.")
    parser.add_argument("--show-window", action="store_true", help="Display the camera preview window.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without opening serial.")
    parser.add_argument("--update-hz", type=float, default=15.0, help="Maximum serial commands per second.")
    parser.add_argument("--pan-center", type=int, default=90, help="Centered pan angle.")
    parser.add_argument("--tilt-center", type=int, default=45, help="Centered tilt angle.")
    parser.add_argument("--pan-min", type=int, default=0, help="Minimum pan angle.")
    parser.add_argument("--pan-max", type=int, default=180, help="Maximum pan angle.")
    parser.add_argument("--tilt-min", type=int, default=10, help="Minimum tilt angle.")
    parser.add_argument("--tilt-max", type=int, default=90, help="Maximum tilt angle.")
    parser.add_argument("--pan-gain", type=float, default=-0.035, help="Pan degrees per pixel of x error.")
    parser.add_argument("--tilt-gain", type=float, default=-0.035, help="Tilt degrees per pixel of y error.")
    parser.add_argument("--deadband-px", type=float, default=35.0, help="Ignore errors smaller than this.")
    parser.add_argument("--smooth-alpha", type=float, default=0.25, help="0..1; higher reacts faster.")
    parser.add_argument("--max-step", type=float, default=4.0, help="Maximum angle change per command.")
    return parser.parse_args()


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def step_toward(current: float, target: float, max_step: float) -> float:
    delta = target - current
    if abs(delta) <= max_step:
        return target
    if delta > 0:
        return current + max_step
    return current - max_step


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


def best_nose(result, confidence_threshold: float, keypoint_confidence_threshold: float):
    if result.boxes is None or result.keypoints is None:
        return None

    best = None
    for index, box in enumerate(result.boxes):
        confidence = float(box.conf[0].item())
        if confidence < confidence_threshold:
            continue

        xy = result.keypoints.xy[index][NOSE_KEYPOINT_INDEX]
        x = float(xy[0].item())
        y = float(xy[1].item())

        nose_confidence = confidence
        if result.keypoints.conf is not None:
            nose_confidence = float(result.keypoints.conf[index][NOSE_KEYPOINT_INDEX].item())
            if nose_confidence < keypoint_confidence_threshold:
                continue

        candidate = (confidence, nose_confidence, x, y)
        if best is None or candidate[0] > best[0]:
            best = candidate

    if best is None:
        return None
    return best[2], best[3], best[0], best[1]


class ServoSerial:
    def __init__(self, port: str, baud_rate: int, dry_run: bool) -> None:
        self.dry_run = dry_run
        self.serial = None
        if not dry_run:
            self.serial = Serial(port, baud_rate, timeout=1)
            time.sleep(2)
            ready = self.serial.readline().decode(errors="replace").strip()
            if ready:
                print(ready)

    def send(self, pan: int, tilt: int) -> None:
        command = f"{pan},{tilt}\n"
        if self.dry_run:
            print(command.strip())
            return
        assert self.serial is not None
        self.serial.write(command.encode("ascii"))
        self.serial.flush()

    def close(self) -> None:
        if self.serial is not None:
            self.serial.close()


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)
    args = parse_args()
    update_interval = 1.0 / args.update_hz

    print(f"Loading model: {args.model}")
    model = YOLO(args.model)

    print(f"Opening camera index {args.camera_index}")
    camera = open_camera(args.camera_index)
    if not camera.isOpened():
        print(f"Could not open camera index {args.camera_index}", file=sys.stderr)
        return 1

    frame = wait_for_frame(camera)
    if frame is None:
        print(f"Camera index {args.camera_index} opened but did not return frames.", file=sys.stderr)
        camera.release()
        return 1

    print("Opening Arduino" if not args.dry_run else "Dry run; not opening Arduino")
    servo = ServoSerial(args.arduino_port, args.baud_rate, args.dry_run)

    smooth_x = None
    smooth_y = None
    pan = float(args.pan_center)
    tilt = float(args.tilt_center)
    last_sent_at = 0.0
    last_waiting_log_at = 0.0

    print("Press Ctrl+C to stop.")
    if args.show_window:
        print("Press q in the preview window to stop.")

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Failed to read frame from camera.", file=sys.stderr)
                return 1

            result = model.predict(frame, verbose=False)[0]
            nose = best_nose(result, args.confidence, args.keypoint_confidence)

            if nose is not None:
                x, y, box_confidence, nose_confidence = nose
                if smooth_x is None:
                    smooth_x = x
                    smooth_y = y
                else:
                    smooth_x = smooth_x * (1.0 - args.smooth_alpha) + x * args.smooth_alpha
                    smooth_y = smooth_y * (1.0 - args.smooth_alpha) + y * args.smooth_alpha

                frame_height, frame_width = frame.shape[:2]
                error_x = smooth_x - frame_width / 2
                error_y = smooth_y - frame_height / 2

                if abs(error_x) < args.deadband_px:
                    error_x = 0
                if abs(error_y) < args.deadband_px:
                    error_y = 0

                target_pan = args.pan_center + error_x * args.pan_gain
                target_tilt = args.tilt_center + error_y * args.tilt_gain
                target_pan = clamp(target_pan, args.pan_min, args.pan_max)
                target_tilt = clamp(target_tilt, args.tilt_min, args.tilt_max)

                now = time.time()
                if now - last_sent_at >= update_interval:
                    pan = step_toward(pan, target_pan, args.max_step)
                    tilt = step_toward(tilt, target_tilt, args.max_step)
                    pan_command = round(clamp(pan, args.pan_min, args.pan_max))
                    tilt_command = round(clamp(tilt, args.tilt_min, args.tilt_max))
                    servo.send(pan_command, tilt_command)
                    print(
                        f"{datetime.now().isoformat(timespec='seconds')} "
                        f"nose x={x:.1f} y={y:.1f} conf={box_confidence:.3f} "
                        f"nose_conf={nose_confidence:.3f} servo={pan_command},{tilt_command}"
                    )
                    last_sent_at = now
            else:
                now = time.time()
                if now - last_waiting_log_at >= 2.0:
                    print(f"{datetime.now().isoformat(timespec='seconds')} waiting for nose")
                    last_waiting_log_at = now

            if args.show_window:
                annotated = result.plot()
                cv2.imshow("Nose Tracking Servo Control", annotated)
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
