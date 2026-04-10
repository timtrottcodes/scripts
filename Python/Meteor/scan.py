#!/usr/bin/env python3
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import sys
import re
import json
import time
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

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

RESIZE_WIDTH = 960
RESIZE_HEIGHT = 544
METDET_SENSITIVITY = "low"

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
            hour=22, minute=0, second=0
        )

        end_time = datetime.combine(base_date + timedelta(days=1), datetime.min.time()).replace(
            hour=5, minute=0, second=0
        )

    else:
        today = datetime.now().date()

        start_time = datetime.combine(today - timedelta(days=1), datetime.min.time()).replace(
            hour=22, minute=0, second=0
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
        "-vf", f"scale={width}:{height},drawbox=y=380:h=164:color=black:t=fill",
        "-pix_fmt", "yuv420p",
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
    saved_paths = []

    date_str = src_video.parents[2].name
    hour_str = src_video.parents[1].name
    original_name = src_video.name

    new_filename = f"{date_str}_{hour_str}_{original_name}"

    for cat in categories:
        if cat.upper() in IGNORE_CATEGORIES:
            continue

        out_dir = OUTPUT_DIR / date_str / cat.lower()
        out_dir.mkdir(parents=True, exist_ok=True)

        dest = out_dir / new_filename
        shutil.copy2(src_video, dest)

        saved_paths.append(dest)

    return saved_paths

def process_video(i, total_videos, vid, log_path):
    video_start = time.time()

    try:
        resized_path = resize_video_ffmpeg(vid, RESIZE_WIDTH, RESIZE_HEIGHT)

        with open(log_path, "a") as log_file:
            categories = check_objects(resized_path, log_file)

        Path(resized_path).unlink(missing_ok=True)

        saved_files = []
        if categories:
            saved_files = save_detected_video(vid, categories)

        elapsed = time.time() - video_start

        return {
            "index": i,
            "video": vid,
            "elapsed": elapsed,
            "categories": categories,
            "saved": saved_files
        }

    except Exception as e:
        return {
            "index": i,
            "video": vid,
            "elapsed": None,
            "error": str(e)
        }

# --- Main ---
def main():
    script_start = time.time()
    now = datetime.now()

    start_time, end_time = get_scan_window()

    print(f"Scanning window: {start_time} → {end_time}")

    log_path = LOG_DIR / f"metdetpy_{now.strftime('%Y%m%d-%H%M%S')}.log"

    with open(log_path, "w") as log_file:

        videos = get_video_files(start_time, end_time)
        total_videos = len(videos)

        print(f"Found {total_videos} videos to process\n")

        workers = min(4, os.cpu_count() or 1)
        print(f"Using {workers} parallel workers\n")

        completed = 0

        with ProcessPoolExecutor(max_workers=workers) as executor:

            futures = [
                executor.submit(process_video, i, total_videos, vid, log_path)
                for i, vid in enumerate(videos, start=1)
            ]

            for future in as_completed(futures):

                result = future.result()
                completed += 1

                if "error" in result:
                    print(f"Error processing {result['video']}: {result['error']}")
                    continue

                i = result["index"]
                vid = result["video"]
                elapsed = result["elapsed"]
                categories = result["categories"]
                saved = result["saved"]

                runtime = time.time() - script_start
                avg_time = runtime / completed
                remaining = total_videos - completed
                eta_seconds = remaining * avg_time
                pct = (completed / total_videos) * 100

                h, r = divmod(int(eta_seconds), 3600)
                m, s = divmod(r, 60)
                eta_str = f"{h}h{m:02d}m"

                tag_list = [c for c in categories if c.upper() not in IGNORE_CATEGORIES]

                if tag_list:
                    tags = ",".join(sorted(set(tag_list)))
                    print(
                        f"[{completed}/{total_videos} | {pct:.1f}%] "
                        f"Processed in {elapsed:.2f}s "
                        f"found {{{tags}}}, saved | ETA {eta_str}",
                        flush=True
                    )
                else:
                    print(
                        f"[{completed}/{total_videos} | {pct:.1f}%] "
                        f"Processed in {elapsed:.2f}s | ETA {eta_str}",
                        flush=True
                    )

    total_elapsed = time.time() - script_start

    print("\n================================")
    print(f"Total videos processed: {total_videos}")
    print(f"Total runtime: {total_elapsed/60:.2f} minutes ({total_elapsed:.2f} seconds)")
    print(f"MetDetPy logs saved to: {log_path}")
    print("================================")

if __name__ == "__main__":
    main()
