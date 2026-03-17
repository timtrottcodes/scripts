#!/usr/bin/env python3
import os
import hashlib
import re
from collections import defaultdict

VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}

EPISODE_REGEX = re.compile(r"(s\d{1,2}e\d{1,2})", re.IGNORECASE)

TV_PATH_KEYWORDS = [
    "/tv/",
    "/shows/",
    "/series/",
    "/episodes/",
    "/season/"
]

MOVIE_PATH_KEYWORDS = [
    "/movies/",
    "/films/",
    "/cinema/"
]


def sha256(path, block_size=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(block_size):
            h.update(chunk)
    return h.hexdigest()


def is_video(file):
    return os.path.splitext(file)[1].lower() in VIDEO_EXTS


def classify_path(path):
    p = path.lower()

    if any(k in p for k in TV_PATH_KEYWORDS):
        return "tv"

    if any(k in p for k in MOVIE_PATH_KEYWORDS):
        return "movie"

    return "other"


def scan(root):
    file_info = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if is_video(f):
                full = os.path.join(dirpath, f)
                size = os.path.getsize(full)
                file_info.append((full, size))
    return file_info


def main(root):
    print(f"Scanning: {root}\n")

    files = scan(root)

    tv_files = []
    movie_files = []
    other_files = []

    for path, size in files:
        category = classify_path(path)

        if category == "tv":
            tv_files.append((path, size))
        elif category == "movie":
            movie_files.append((path, size))
        else:
            other_files.append((path, size))

    # ------------------------
    # 1. True duplicates (all files)
    # ------------------------
    print("=== TRUE DUPLICATES (hash-based) ===")

    size_map = defaultdict(list)
    for path, size in files:
        size_map[size].append(path)

    hash_map = defaultdict(list)

    for size, paths in size_map.items():
        if len(paths) > 1:
            for p in paths:
                h = sha256(p)
                hash_map[h].append(p)

    for h, paths in hash_map.items():
        if len(paths) > 1:
            print("\nDuplicate group:")
            for p in paths:
                print(" ", p)

    # ------------------------
    # 2. Episode duplicates (TV only)
    # ------------------------
    print("\n=== EPISODE DUPLICATES (TV folders) ===")

    episode_map = defaultdict(list)

    for path, _ in tv_files:
        folder = os.path.dirname(path)
        name = os.path.basename(path)

        m = EPISODE_REGEX.search(name)
        if m:
            episode = m.group(1).lower()
            key = (folder, episode)
            episode_map[key].append(path)

    for (folder, episode), paths in episode_map.items():
        if len(paths) > 1:
            print(f"\nFolder: {folder}")
            print(f"Episode: {episode}")
            for p in paths:
                print(" ", p)

    # ------------------------
    # 3. Movie folder violations (movies only)
    # ------------------------
    print("\n=== MOVIE FOLDER VIOLATIONS ===")

    folder_map = defaultdict(list)

    for path, _ in movie_files:
        folder = os.path.dirname(path)
        folder_map[folder].append(path)

    for folder, paths in folder_map.items():
        if len(paths) > 1:
            if not any(EPISODE_REGEX.search(os.path.basename(p)) for p in paths):
                print(f"\nFolder: {folder}")
                print("Contains multiple video files:")
                for p in paths:
                    print(" ", p)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: media_audit.py /path/to/media")
        sys.exit(1)

    main(sys.argv[1])
