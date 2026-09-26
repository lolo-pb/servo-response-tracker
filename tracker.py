"""Track pink and cyan markers from a USB webcam and show their angle."""

import math
import time

import cv2
import numpy as np


CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
MIN_BLOB_AREA = 200

# HSV ranges are OpenCV HSV values: hue 0-179, saturation/value 0-255.
# Tune these while viewing the markers under the lighting you will use.
MARKERS = {
    "pink": {
        "ranges": [((155, 80, 80), (179, 255, 255))],
        "draw_color": (255, 0, 255),  # BGR
    },
    "cyan": {
        "ranges": [((80, 80, 80), (105, 255, 255))],
        "draw_color": (255, 255, 0),  # BGR
    },
}


def find_marker(hsv_frame, marker):
    """Return the centre of the largest sufficiently large marker blob."""
    mask = np.zeros(hsv_frame.shape[:2], dtype=np.uint8)
    for lower, upper in marker["ranges"]:
        mask |= cv2.inRange(hsv_frame, np.array(lower), np.array(upper))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_contours = [contour for contour in contours if cv2.contourArea(contour) >= MIN_BLOB_AREA]
    if not valid_contours:
        return None

    contour = max(valid_contours, key=cv2.contourArea)
    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        return None

    return int(moments["m10"] / moments["m00"]), int(moments["m01"] / moments["m00"])


def draw_marker(frame, name, point, color):
    cv2.circle(frame, point, 7, color, -1)
    cv2.putText(frame, name, (point[0] + 10, point[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def main():
    camera = cv2.VideoCapture(CAMERA_INDEX)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not camera.isOpened():
        raise RuntimeError(f"Could not open camera {CAMERA_INDEX}.")

    last_frame_time = time.perf_counter()
    while True:
        ok, frame = camera.read()
        if not ok:
            print("Could not read a frame from the camera.")
            break

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        points = {name: find_marker(hsv_frame, marker) for name, marker in MARKERS.items()}

        for name, marker in MARKERS.items():
            if points[name] is not None:
                draw_marker(frame, name, points[name], marker["draw_color"])

        pink, cyan = points["pink"], points["cyan"]
        if pink is not None and cyan is not None:
            cv2.line(frame, pink, cyan, (255, 255, 255), 2)
            # Negate y because image coordinates increase downwards; counter-clockwise is positive.
            angle = math.degrees(math.atan2(-(cyan[1] - pink[1]), cyan[0] - pink[0]))
            cv2.putText(frame, f"angle: {angle:+.1f} deg", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        else:
            missing = ", ".join(name for name, point in points.items() if point is None)
            cv2.putText(frame, f"marker missing: {missing}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        now = time.perf_counter()
        fps = 1 / (now - last_frame_time)
        last_frame_time = now
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("Marker angle tracker", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
