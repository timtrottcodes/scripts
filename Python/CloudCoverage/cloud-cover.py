#!/usr/bin/env python3
"""
Night Sky Cloud Coverage Estimator (Brightness Method)
Reads the first video from the midnight hour for a given camera in Frigate recordings,
calculates average brightness (excluding very bright areas like the moon),
and outputs a cloud coverage score (0 = clear, 100 = fully cloudy).

Author: Tim Trott
Date: 2026-02-26
"""

import os
import cv2
import numpy as np
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.rest import ApiException

# ---------------- CONFIG ---------------- #
FRIGATE_RECORDINGS_DIR = "/mnt/frigate/"
CAMERA_NAME = "space"  # camera name folder
HOUR_DIR = "00"        # the hour to analyze (midnight)
MIN_BRIGHTNESS = 25    # calibration: darkest sky (0 cloud coverage)
MAX_BRIGHTNESS = 43    # calibration: brightest sky (100 cloud coverage)
MOON_THRESHOLD = 240   # brightness threshold to ignore moon pixels

INFLUX_URL = "http://<ip>:8086"          # InfluxDB URL
INFLUX_TOKEN = "<token>>"             # API token
INFLUX_ORG = "<org>>"                 # Org name
INFLUX_BUCKET = "<bucket>>"                    # Bucket name
INFLUX_MEASUREMENT = "cloud_coverage"        # Measurement name

# Optional test date in format "YYYY-MM-DD"
# Leave blank to use yesterday automatically
TEST_DATE = ""
# ---------------------------------------- #

def get_target_date():
    """Return the date string to use: TEST_DATE or today"""
    if TEST_DATE:
        return TEST_DATE
    # Use today's date (midnight video) if TEST_DATE is blank
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")

def find_first_video(base_dir, date_str, hour, camera):
    """Find the first mp4 in the given date/hour/camera folder"""
    target_dir = os.path.join(base_dir, date_str, hour, camera)
    if not os.path.isdir(target_dir):
        raise FileNotFoundError(f"Directory does not exist: {target_dir}")
    # List mp4 files and sort (just to be consistent)
    files = [f for f in os.listdir(target_dir) if f.lower().endswith(".mp4")]
    if not files:
        raise FileNotFoundError(f"No mp4 files found in {target_dir}")
    files.sort()
    return os.path.join(target_dir, files[0])

def calculate_cloud_coverage(frame):
    """Estimate cloud coverage using brightness and contrast"""

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Flatten array
    flat = gray.flatten()

    # Remove brightest pixels (moon, lights)
    threshold = np.percentile(flat, 90)
    filtered = flat[flat < threshold]

    if len(filtered) == 0:
        filtered = flat

    avg_brightness = filtered.mean()

    # Measure sky contrast
    sky_std = filtered.std()

    brightness_cloud = 100 * (avg_brightness - MIN_BRIGHTNESS) / (MAX_BRIGHTNESS - MIN_BRIGHTNESS)
    brightness_cloud = np.clip(brightness_cloud, 0, 100)

    # variance calibration based on observed data
    VAR_CLEAR = 45
    VAR_CLOUD = 5

    contrast_score = (sky_std - VAR_CLOUD) / (VAR_CLEAR - VAR_CLOUD)
    contrast_score = np.clip(contrast_score, 0, 1)

    # invert because high variance = clear sky
    contrast_modifier = 1 - contrast_score

    cloud_coverage = brightness_cloud * contrast_modifier

    return cloud_coverage, avg_brightness, sky_std

def write_to_influx(cloud_coverage, target_date, hour):
    """Write the cloud coverage value to InfluxDB with debug output"""

    print("\n--- INFLUX DEBUG INFO ---")
    print(f"URL: {INFLUX_URL}")
    print(f"Org: {INFLUX_ORG}")
    print(f"Bucket: {INFLUX_BUCKET}")
    print(f"Measurement: {INFLUX_MEASUREMENT}")
    print(f"Camera tag: {CAMERA_NAME}")
    print(f"Timestamp: {target_date}T{hour}:00:00Z")
    print(f"Cloud percent: {cloud_coverage}")
    print(f"Token (first 8 chars): {INFLUX_TOKEN[:8]}...")
    print("-------------------------\n")

    try:
        with InfluxDBClient(
            url=INFLUX_URL,
            token=INFLUX_TOKEN,
            org=INFLUX_ORG,
            debug=True  # enables HTTP debug logging
        ) as client:

            write_api = client.write_api(
                write_options=WriteOptions(write_type="synchronous")
            )

            point = (
                Point(INFLUX_MEASUREMENT)
                .tag("camera", CAMERA_NAME)
                .field("cloud_percent", float(cloud_coverage))
                .time(f"{target_date}T{hour}:00:00Z")
            )

            write_api.write(
                bucket=INFLUX_BUCKET,
                org=INFLUX_ORG,
                record=point
            )

            print("Write successful.")

    except ApiException as e:
        print("InfluxDB API Exception:")
        print(f"Status: {e.status}")
        print(f"Reason: {e.reason}")
        print(f"Body: {e.body}")

def main():
    print("-------------------------\n")
    target_date = get_target_date()
    print(f"Using date: {target_date}")

    try:
        video_path = find_first_video(FRIGATE_RECORDINGS_DIR, target_date, HOUR_DIR, CAMERA_NAME)
        print(f"Processing video: {video_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("Error: Could not read first frame of video.")
        return

    cloud_coverage, avg_brightness, sky_std = calculate_cloud_coverage(frame)

    print(f"Filtered brightness: {avg_brightness:.2f}")
    print(f"Sky contrast (std dev): {sky_std:.2f}")
    print(f"Estimated cloud coverage: {cloud_coverage:.1f}%")

    # write_to_influx(cloud_coverage, target_date, HOUR_DIR)

if __name__ == "__main__":
