"""Measure pink-to-cyan marker angles in every video in a folder."""

import argparse
import csv
import math
import os
from pathlib import Path

import cv2
import numpy as np


SUPPORTED_VIDEO_EXTENSIONS = {".avi", ".mkv", ".mov", ".mp4"}
MIN_BLOB_AREA = 5

# OpenCV HSV values: hue 0-179, saturation/value 0-255.
MARKERS = {
    "pink": {
        # Target #a0608c is approximately HSV (159, 102, 160).
        "ranges": [((150, 45, 60), (168, 180, 220))],
        "draw_color": (255, 0, 255),  # BGR
    },
    "cyan": {
        # Target #056a7d is approximately HSV (95, 245, 125).
        "ranges": [((90, 60, 40), (108, 255, 200))],
        "draw_color": (255, 255, 0),  # BGR
    },
}


def find_marker(hsv_frame, marker, min_blob_area):
    """Return the centre of the largest sufficiently large marker blob."""
    mask = np.zeros(hsv_frame.shape[:2], dtype=np.uint8)
    for lower, upper in marker["ranges"]:
        mask |= cv2.inRange(hsv_frame, np.array(lower), np.array(upper))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid = [contour for contour in contours if cv2.contourArea(contour) >= min_blob_area]
    if not valid:
        return None

    moments = cv2.moments(max(valid, key=cv2.contourArea))
    if moments["m00"] == 0:
        return None
    return int(moments["m10"] / moments["m00"]), int(moments["m01"] / moments["m00"])


def marker_angle(pink, cyan):
    """Return the pink-to-cyan angle, with counter-clockwise positive."""
    return math.degrees(math.atan2(-(cyan[1] - pink[1]), cyan[0] - pink[0]))


def draw_marker(frame, name, point, color, scale):
    radius = max(4, round(7 * scale))
    thickness = max(1, round(2 * scale))
    cv2.circle(frame, point, radius, color, -1)
    cv2.putText(
        frame,
        name,
        (point[0] + radius + 3, point[1] - radius),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6 * scale,
        color,
        thickness,
    )


def draw_dotted_line(frame, start, end, scale):
    """Draw a dotted yellow line between two points."""
    distance = math.dist(start, end)
    if distance == 0:
        return

    dot_count = max(1, int(distance / max(6, round(10 * scale))))
    radius = max(1, round(2 * scale))
    for index in range(dot_count + 1):
        fraction = index / dot_count
        point = (
            round(start[0] + (end[0] - start[0]) * fraction),
            round(start[1] + (end[1] - start[1]) * fraction),
        )
        cv2.circle(frame, point, radius, (0, 255, 255), -1)


def put_status(frame, text, line, color, scale):
    margin = max(10, round(20 * scale))
    line_height = max(22, round(30 * scale))
    cv2.putText(
        frame,
        text,
        (margin, margin + line * line_height),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7 * scale,
        color,
        max(1, round(2 * scale)),
    )


def process_video(video_path, output_folder, overwrite):
    csv_path = output_folder / f"{video_path.stem}-angles.csv"
    overlay_path = output_folder / f"{video_path.stem}-overlay.mp4"
    existing = [path for path in (csv_path, overlay_path) if path.exists()]
    if existing and not overwrite:
        names = ", ".join(path.name for path in existing)
        print(f"Skipping {video_path.name}: output exists ({names}). Use --overwrite to replace it.")
        return False

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        print(f"Skipping {video_path.name}: could not open the video.")
        return False

    fps = capture.get(cv2.CAP_PROP_FPS)
    if not math.isfinite(fps) or fps <= 0:
        fps = 30.0
        print(f"{video_path.name}: invalid source FPS; using 30 FPS.")

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    ok, frame = capture.read()
    if not ok:
        capture.release()
        print(f"Skipping {video_path.name}: no readable frames.")
        return False

    height, width = frame.shape[:2]
    scale = max(0.6, min(width, height) / 480)
    temp_csv = csv_path.with_name(f"{csv_path.stem}.tmp{csv_path.suffix}")
    temp_overlay = overlay_path.with_name(f"{overlay_path.stem}.tmp{overlay_path.suffix}")
    writer = cv2.VideoWriter(
        str(temp_overlay), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    if not writer.isOpened():
        capture.release()
        raise RuntimeError(f"Could not create {overlay_path}.")

    frame_index = 0
    initial_angle = None
    previous_angle = None
    relative_angle = 0.0
    initial_direction = None

    try:
        with temp_csv.open("w", newline="", encoding="utf-8") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(
                ["frame", "time_seconds", "angle_degrees", "pink_detected", "cyan_detected"]
            )

            while True:
                hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                points = {
                    name: find_marker(hsv_frame, marker, MIN_BLOB_AREA)
                    for name, marker in MARKERS.items()
                }
                for name, marker in MARKERS.items():
                    if points[name] is not None:
                        draw_marker(frame, name, points[name], marker["draw_color"], scale)

                pink, cyan = points["pink"], points["cyan"]
                csv_angle = ""
                if pink is not None and cyan is not None:
                    current_angle = marker_angle(pink, cyan)
                    if initial_angle is None:
                        initial_angle = current_angle
                        previous_angle = current_angle
                        initial_radians = math.radians(initial_angle)
                        initial_direction = (math.cos(initial_radians), -math.sin(initial_radians))
                    else:
                        delta = (current_angle - previous_angle + 180) % 360 - 180
                        relative_angle += delta
                        previous_angle = current_angle

                    csv_angle = f"{relative_angle:.6f}"
                    cv2.line(frame, pink, cyan, (255, 255, 255), max(1, round(2 * scale)))
                    current_length = math.dist(pink, cyan)
                    reference_end = (
                        round(cyan[0] - current_length * initial_direction[0]),
                        round(cyan[1] - current_length * initial_direction[1]),
                    )
                    draw_dotted_line(frame, cyan, reference_end, scale)
                    put_status(
                        frame,
                        f"relative angle: {relative_angle:+.1f} deg",
                        1,
                        (255, 255, 255),
                        scale,
                    )
                else:
                    missing = ", ".join(name for name, point in points.items() if point is None)
                    put_status(frame, f"marker missing: {missing}", 1, (0, 0, 255), scale)

                time_seconds = frame_index / fps
                put_status(
                    frame,
                    f"frame: {frame_index}   time: {time_seconds:.3f} s",
                    2,
                    (255, 255, 255),
                    scale,
                )
                writer.write(frame)
                csv_writer.writerow(
                    [frame_index, f"{time_seconds:.6f}", csv_angle, int(pink is not None), int(cyan is not None)]
                )

                frame_index += 1
                if frame_index % 100 == 0:
                    total = str(total_frames) if total_frames > 0 else "?"
                    print(f"{video_path.name}: {frame_index}/{total} frames")
                ok, frame = capture.read()
                if not ok:
                    break

        capture.release()
        writer.release()
        os.replace(temp_csv, csv_path)
        os.replace(temp_overlay, overlay_path)
    except Exception:
        capture.release()
        writer.release()
        temp_csv.unlink(missing_ok=True)
        temp_overlay.unlink(missing_ok=True)
        raise

    if initial_angle is None:
        print(f"{video_path.name}: completed {frame_index} frames; both markers were never found together.")
    else:
        print(f"{video_path.name}: completed {frame_index} frames -> {csv_path.name}, {overlay_path.name}")
    return True


def parse_args():
    parser = argparse.ArgumentParser(description="Measure marker angles in every video in a folder.")
    parser.add_argument(
        "input_folder",
        nargs="?",
        type=Path,
        help="Video folder (default: a videos folder beside this script).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing CSV and overlay outputs.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.input_folder is None:
        input_folder = Path(__file__).resolve().parent / "videos"
        input_folder.mkdir(exist_ok=True)
    else:
        input_folder = args.input_folder.resolve()

    if not input_folder.is_dir():
        raise SystemExit(f"Input folder does not exist: {input_folder}")

    videos = sorted(
        (
            path
            for path in input_folder.iterdir()
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
            and not path.stem.lower().endswith("-overlay")
        ),
        key=lambda path: path.name.lower(),
    )
    if not videos:
        raise SystemExit(f"No supported videos found in {input_folder}")

    output_folder = input_folder / "output"
    output_folder.mkdir(exist_ok=True)
    completed = sum(process_video(video, output_folder, args.overwrite) for video in videos)
    print(f"Finished: {completed}/{len(videos)} videos processed.")


if __name__ == "__main__":
    main()
