#!/usr/bin/env python3
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Frigate directory and camera name
FRIGATE_ROOT = Path("/mnt/sentinel/frigate/media/frigate/recordings")
CAMERA = "space"

# Where you cloned MetDetPy
METDET_ROOT = Path("/home/ttrott/Documents/Meteor/MetDetPy/")
PYTHON_EXE = Path.home() / "metdet-env/bin/python"

# Output folder
OUTPUT_DIR = Path("/home/ttrott/Documents/Meteor/Found/")
OUTPUT_DIR.mkdir(exist_ok=True)

def check_meteor(video):
    cmd = [
        str(PYTHON_EXE),
        str(METDET_ROOT / "MetDetPy.py"),
        str(video),
        "--mode", "backend",
        "--save-path", "/tmp",
        "--sensitivity", "high"
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    out = result.stdout.lower()
    return "meteor" in out   # adjust if needed

def output_name(video):
    ts = datetime.fromtimestamp(video.stat().st_mtime)
    return ts.strftime("%Y%m%d-%H%M%S") + ".mp4"

def main():
    now = datetime.now()

    # Time window:
    start_time = (now - timedelta(days=1)).replace(hour=20, minute=0, second=0)
    end_time   = now.replace(hour=6, minute=0, second=0)

    print(f"Scanning window: {start_time} → {end_time}")

    for vid in FRIGATE_ROOT.rglob(f"*/{CAMERA}/*.mp4"):
        mtime = datetime.fromtimestamp(vid.stat().st_mtime)

        if not (start_time <= mtime <= end_time):
            continue

        print(f"Scanning {vid}")

        if check_meteor(vid):
            dest = OUTPUT_DIR / output_name(vid)
            print(f"Detected meteor → {dest.name}")
            shutil.copy2(vid, dest)

if __name__ == "__main__":
    main()
