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
METDET_SENSITIVITY = "medium"

# Categories to ignore
IGNORE_CATEGORIES = ["BUGS", "DROPPED"]

# --- Functions ---

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
        "--sensitivity", METDET_SENSITIVITY
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Log everything
    log_file.write(f"==== Video: {video_path.name} ====\n")
    log_file.write(result.stdout + "\n")
    log_file.write(result.stderr + "\n")
    log_file.write("="*50 + "\n\n")
    log_file.flush()

    # Robust JSON extraction
    categories = []
    for line in result.stdout.splitlines():
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

    # Time window: 8pm previous day → 6am today
    start_time = (now - timedelta(days=1)).replace(hour=20, minute=0, second=0)
    end_time   = now.replace(hour=6, minute=0, second=0)

    print(f"Scanning window: {start_time} → {end_time}")

    log_path = LOG_DIR / f"metdetpy_{now.strftime('%Y%m%d-%H%M%S')}.log"
    with open(log_path, "w") as log_file:

        for vid in FRIGATE_ROOT.rglob(f"*/{CAMERA}/*.mp4"):
            mtime = datetime.fromtimestamp(vid.stat().st_mtime)
            if not (start_time <= mtime <= end_time):
                continue

            print(f"Processing {vid}")

            resized_path = resize_video_ffmpeg(vid, RESIZE_WIDTH, RESIZE_HEIGHT)

            categories = check_objects(resized_path, log_file)

            Path(resized_path).unlink(missing_ok=True)

            if categories:
                saved_files = save_detected_video(vid, categories)
                for f in saved_files:
                    print(f"Saved {f}")

    print(f"MetDetPy logs saved to: {log_path}")


if __name__ == "__main__":
    main()
