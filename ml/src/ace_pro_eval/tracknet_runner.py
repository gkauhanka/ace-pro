"""Compatibility runner executed inside the upstream TrackNetV4 environment.

This file intentionally only imports third-party inference dependencies after it has
added the pinned upstream repository to sys.path. The parent Ace Pro CLI itself has
no TensorFlow or OpenCV dependency.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import deque
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path, required=True)
    parser.add_argument("--video-output", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    sys.path.insert(0, str(args.repository / "src"))
    import cv2  # type: ignore[import-not-found]
    import numpy as np  # type: ignore[import-not-found]
    from models.TrackNetV4 import FusionLayerTypeA, FusionLayerTypeB, MotionPromptLayer
    from tensorflow.keras import backend as keras_backend  # type: ignore[import-not-found]
    from tensorflow.keras.models import load_model  # type: ignore[import-not-found]
    from tensorflow.keras.preprocessing.image import array_to_img, img_to_array

    def custom_loss(y_true, y_pred):
        epsilon = keras_backend.epsilon()
        positive = keras_backend.square(1 - y_pred) * y_true * keras_backend.log(
            keras_backend.clip(y_pred, epsilon, 1)
        )
        negative = keras_backend.square(y_pred) * (1 - y_true) * keras_backend.log(
            keras_backend.clip(1 - y_pred, epsilon, 1)
        )
        return -(positive + negative)

    model = load_model(
        args.weights,
        custom_objects={
            "custom_loss": custom_loss,
            "MotionPromptLayer": MotionPromptLayer,
            "FusionLayerTypeA": FusionLayerTypeA,
            "FusionLayerTypeB": FusionLayerTypeB,
        },
    )
    capture = cv2.VideoCapture(str(args.video))
    if not capture.isOpened():
        raise RuntimeError(f"cannot open video: {args.video}")
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if fps <= 0 or width <= 0 or height <= 0:
        raise RuntimeError("video has invalid FPS or dimensions")
    writer = cv2.VideoWriter(
        str(args.video_output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    if not writer.isOpened():
        raise RuntimeError(f"cannot create overlay video: {args.video_output}")

    args.csv_output.parent.mkdir(parents=True, exist_ok=True)
    trail = deque(maxlen=5)
    frame_index = 0
    try:
        with args.csv_output.open("w", newline="", encoding="utf-8") as handle:
            csv_writer = csv.writer(handle)
            csv_writer.writerow(["Frame", "Visibility", "X", "Y", "Confidence"])
            while True:
                frames = []
                for _ in range(3):
                    ok, frame = capture.read()
                    if ok:
                        frames.append(frame)
                if not frames:
                    break
                real_frame_count = len(frames)
                while len(frames) < 3:
                    frames.append(frames[-1])
                batch = np.concatenate(
                    [
                        np.moveaxis(
                            img_to_array(array_to_img(frame[..., ::-1]).resize((512, 288))),
                            -1,
                            0,
                        )
                        for frame in frames
                    ],
                    axis=0,
                )[None, ...].astype("float32") / 255.0
                predictions = model.predict(batch, batch_size=1, verbose=0)[0]
                for offset in range(real_frame_count):
                    probability_map = predictions[offset]
                    binary = (probability_map > args.threshold).astype("uint8") * 255
                    contours, _ = cv2.findContours(
                        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                    )
                    rendered = frames[offset].copy()
                    if contours:
                        contour = max(contours, key=cv2.contourArea)
                        x, y, box_width, box_height = cv2.boundingRect(contour)
                        x_px = (x + box_width / 2) * width / 512
                        y_px = (y + box_height / 2) * height / 288
                        confidence = float(probability_map[binary > 0].max())
                        point = (round(x_px), round(y_px))
                        trail.append(point)
                        for trail_point in trail:
                            cv2.circle(rendered, trail_point, 5, (0, 255, 0), 2)
                        cv2.circle(rendered, point, 5, (0, 0, 255), -1)
                        csv_writer.writerow([frame_index, 1, x_px, y_px, confidence])
                    else:
                        csv_writer.writerow([frame_index, 0, 0, 0, 0])
                    writer.write(rendered)
                    frame_index += 1
    finally:
        capture.release()
        writer.release()


if __name__ == "__main__":
    main()
