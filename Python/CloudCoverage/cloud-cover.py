#!/usr/bin/env python3
"""
Advanced Night Sky Cloud Coverage Estimator

Features:
- Moon masking
- Star detection
- Star loss estimation
- Cloud motion detection
- Region sampling
- Multi-frame averaging

Designed for Frigate recordings.

Author: Tim Trott
Updated: 2026
"""

import os
import cv2
import numpy as np
from datetime import datetime, timedelta

# ---------------- CONFIG ---------------- #

FRIGATE_RECORDINGS_DIR = "/mnt/frigate/"
CAMERA_NAME = "space"
HOUR_DIR = "00"

TEST_DATE = "2026-03-08"   # blank for automatic

FRAME_SAMPLE_COUNT = 25
FRAME_STEP = 5

GRID_SIZE = 4

MIN_BRIGHTNESS = 25
MAX_BRIGHTNESS = 120

STAR_THRESHOLD = 200
STAR_AREA_MIN = 2
STAR_AREA_MAX = 25

MOON_MASK_THRESHOLD = 240

# ----------------------------------------


def get_target_date():
    if TEST_DATE:
        return TEST_DATE

    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def find_first_video(base_dir, date_str, hour, camera):

    target_dir = os.path.join(base_dir, date_str, hour, camera)

    if not os.path.isdir(target_dir):
        raise FileNotFoundError(target_dir)

    files = [f for f in os.listdir(target_dir) if f.endswith(".mp4")]
    files.sort()

    if not files:
        raise FileNotFoundError("No video files")

    return os.path.join(target_dir, files[0])


# ---------------- Moon Mask ---------------- #

def mask_moon(gray):

    mask = gray < np.percentile(gray, 99.7)
    return gray * mask


# ---------------- Star Detection ---------------- #

def count_stars(gray):

    mean = np.mean(gray)
    std = np.std(gray)

    threshold = mean + (2.2 * std)

    _, thresh = cv2.threshold(
        gray,
        threshold,
        255,
        cv2.THRESH_BINARY
    )

    contours,_ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    stars = 0

    for c in contours:

        area = cv2.contourArea(c)

        if STAR_AREA_MIN < area < STAR_AREA_MAX:
            stars += 1

    return stars


# ---------------- Region Sampling ---------------- #

def regional_star_counts(gray):

    h,w = gray.shape

    tile_h = h // GRID_SIZE
    tile_w = w // GRID_SIZE

    counts = []

    for y in range(GRID_SIZE):

        for x in range(GRID_SIZE):

            region = gray[
                y*tile_h:(y+1)*tile_h,
                x*tile_w:(x+1)*tile_w
            ]

            counts.append(count_stars(region))

    return np.array(counts)

# ---------------- Motion Detection ---------------- #

def motion_score(frames):

    diffs = []

    for i in range(1,len(frames)):

        diff = cv2.absdiff(frames[i-1], frames[i])

        diffs.append(np.mean(diff))

    return np.mean(diffs)


# ---------------- Main Estimator ---------------- #

def analyze_video(video_path):

    cap = cv2.VideoCapture(video_path)

    frames = []
    star_counts = []
    brightness_values = []
    contrast_values = []

    frame_index = 0

    while len(frames) < FRAME_SAMPLE_COUNT:

        ret, frame = cap.read()

        if not ret:
            break

        if frame_index % FRAME_STEP == 0:

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            gray = cv2.resize(
                gray,
                (1024, 768),
                interpolation=cv2.INTER_AREA
            )

            gray = mask_moon(gray)

            frames.append(gray)

            brightness_values.append(np.mean(gray))
            contrast_values.append(np.std(gray))

            star_counts.append(count_stars(gray))

        frame_index += 1

    cap.release()

    frames = np.array(frames)

    avg_brightness = np.mean(brightness_values)
    avg_contrast = np.mean(contrast_values)

    avg_stars = np.mean(star_counts)

    # motion score
    motion = motion_score(frames)

    # normalize brightness
    brightness_score = (avg_brightness - MIN_BRIGHTNESS) / (MAX_BRIGHTNESS - MIN_BRIGHTNESS)
    brightness_score = np.clip(brightness_score,0,1)

    # contrast score
    contrast_score = 1 - np.clip(avg_contrast / 60,0,1)

    # star loss estimate
    expected_stars = np.percentile(star_counts, 90)
    star_loss = 1 - (avg_stars / expected_stars if expected_stars else 0)

    star_loss = np.clip(star_loss,0,1)

    # motion normalization
    motion_norm = np.clip(motion / 25,0,1)

    # weighted fusion
    cloud_score = (
        brightness_score * 0.35 +
        contrast_score * 0.25 +
        star_loss * 0.30 +
        motion_norm * 0.10
    )

    cloud_percent = np.clip(cloud_score * 100,0,100)

    return {
        "brightness": avg_brightness,
        "contrast": avg_contrast,
        "stars": avg_stars,
        "motion": motion,
        "cloud_percent": cloud_percent
    }


# ---------------- MAIN ---------------- #

def main():

    print("\n--- Cloud Detection ---\n")

    date = get_target_date()

    print("Using date:", date)

    video = find_first_video(
        FRIGATE_RECORDINGS_DIR,
        date,
        HOUR_DIR,
        CAMERA_NAME
    )

    print("Video:", video)

    result = analyze_video(video)

    print("\nResults\n")

    print(f"Average brightness : {result['brightness']:.2f}")
    print(f"Sky contrast       : {result['contrast']:.2f}")
    print(f"Star count         : {result['stars']:.1f}")
    print(f"Cloud motion       : {result['motion']:.2f}")
    print(f"\nEstimated clouds   : {result['cloud_percent']:.1f}%\n")


if __name__ == "__main__":
    main()
