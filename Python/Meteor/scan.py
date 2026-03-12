#!/usr/bin/env python3
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import sys
import re
import json

# --- Configuration ---
CWD = Path.cwd()

FRIGATE_ROOT = Path("/mnt/sentinel/frigate/media/frigate/recordings")
CAMERA = "space"

METDET_ROOT = CWD / "MetDetPy"
PYTHON_EXE = Path(sys.executable)  # Use current Python (activated venv)
OUTPUT_DIR = CWD / "Found"
OUTPUT_DIR.mkdir(exist_ok=True)

LOG_DIR = CWD / "Logs"
LOG_DIR.mkdir(exist_ok=True)

RESIZE_WIDTH = 1024
RESIZE_HEIGHT = 768
METDET_SENSITIVITY = "normal"

# Categories to ignore
IGNORE_CATEGORIES = ["BUGS", "DROPPED"]
SCAN_DATE = None  # Example: "2026-03-08" or None for automatic mode

# --- Functions ---

def get_scan_window():
    """
    Determine the time window for scanning recordings.

    If SCAN_DATE is set (YYYY-MM-DD):
        scan 20:00 on that date → 05:00 next day.

    If SCAN_DATE is None:
        scan 20:00 yesterday → 05:00 today.
    """

    if SCAN_DATE:
        base_date = datetime.strptime(SCAN_DATE, "%Y-%m-%d").date()

        start_time = datetime.combine(base_date, datetime.min.time()).replace(
            hour=20, minute=0, second=0
        )

        end_time = datetime.combine(base_date + timedelta(days=1), datetime.min.time()).replace(
            hour=5, minute=0, second=0
        )

    else:
        today = datetime.now().date()

        start_time = datetime.combine(today - timedelta(days=1), datetime.min.time()).replace(
            hour=20, minute=0, second=0
        )

        end_time = datetime.combine(today, datetime.min.time()).replace(
            hour=5, minute=0, second=0
        )

    return start_time, end_time

def get_video_files(start_time, end_time):
    """
    Retrieve Frigate recordings within the scan window.

    Only scans the necessary date directories to avoid
    traversing the entire recordings tree.
    """

    start_date = start_time.date().strftime("%Y-%m-%d")
    end_date = end_time.date().strftime("%Y-%m-%d")

    search_dirs = [
        FRIGATE_ROOT / start_date,
        FRIGATE_ROOT / end_date
    ]

    videos = []

    for directory in search_dirs:

        if not directory.exists():
            continue

        for vid in directory.rglob(f"{CAMERA}/*.mp4"):

            mtime = datetime.fromtimestamp(vid.stat().st_mtime)

            if start_time <= mtime <= end_time:
                videos.append(vid)

    videos.sort()

    return videos

def resize_video_ffmpeg(input_path, width, height):
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
    Path(tmp_path).unlink()  # ffmpeg will create it

    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", f"scale={width}:{height}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        tmp_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return Path(tmp_path)

def check_objects(video_path, log_file):
    video_path = Path(video_path)
    cmd = [
        str(PYTHON_EXE),
        str(METDET_ROOT / "MetDetPy.py"),
        str(video_path),
        "--mode", "backend",
        "--save-path", "/tmp",
        "--sensitivity", METDET_SENSITIVITY,
        "--mask", str(CWD / "mask.png")
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    stdout = result.stdout
    stderr = result.stderr

    # Explicitly free buffers
    result.stdout = None
    result.stderr = None

    # Log everything
    log_file.write(f"==== Video: {video_path.name} ====\n")
    log_file.write(stdout + "\n")
    log_file.write(stderr + "\n")
    log_file.write("="*50 + "\n\n")
    log_file.flush()

    # Robust JSON extraction
    categories = []
    for line in stdout.splitlines():
        if line.strip().startswith("Meteor:"):
            try:
                json_text = line.strip()[7:].strip()  # remove 'Meteor: '
                data = json.loads(json_text)
                for target in data.get("target", []):
                    cat = target.get("category", "UNKNOWN")
                    categories.append(cat)
            except json.JSONDecodeError:
                print(f"Warning: Skipping unparsable JSON line: {line[:100]}...")
    return categories

def save_detected_video(src_video, categories):
    ts = datetime.fromtimestamp(src_video.stat().st_mtime)
    date_str = ts.strftime("%Y-%m-%d")
    time_str = ts.strftime("%H%M%S")
    saved_paths = []

    for cat in categories:
        if cat.upper() in IGNORE_CATEGORIES:
            continue

        out_dir = OUTPUT_DIR / date_str / cat.lower()
        out_dir.mkdir(parents=True, exist_ok=True)
        ext = src_video.suffix if src_video.suffix else ".mp4"
        dest = out_dir / f"{time_str}{ext}"
        shutil.copy2(src_video, dest)
        saved_paths.append(dest)
    return saved_paths

# --- Main ---
def main():
    now = datetime.now()

    start_time, end_time = get_scan_window()

    print(f"Scanning window: {start_time} → {end_time}")

    log_path = LOG_DIR / f"metdetpy_{now.strftime('%Y%m%d-%H%M%S')}.log"

    with open(log_path, "w") as log_file:

        videos = get_video_files(start_time, end_time)
        total_videos = len(videos)

        print(f"Found {total_videos} videos to process\n")

        for i, vid in enumerate(videos, start=1):
            try:
                print(f"Processing video {i} of {total_videos}: {vid}")

                resized_path = resize_video_ffmpeg(vid, RESIZE_WIDTH, RESIZE_HEIGHT)

                categories = check_objects(resized_path, log_file)

                Path(resized_path).unlink(missing_ok=True)

                if categories:
                    saved_files = save_detected_video(vid, categories)
                    for f in saved_files:
                        print(f"Saved {f}")
            except Exception as e:
                print(f"Error processing {vid}: {e}")
                continue

    print(f"\nMetDetPy logs saved to: {log_path}")


if __name__ == "__main__":
    main()
