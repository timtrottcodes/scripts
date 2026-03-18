#!/usr/bin/env bash

set -e

# ----------------------------------------
# Sanitize image metadata and verify result
# ----------------------------------------

# Check dependency
if ! command -v exiftool >/dev/null 2>&1; then
    echo "Error: exiftool is not installed."
    echo "Install with:"
    echo "  Debian/Ubuntu: sudo apt install libimage-exiftool-perl"
    echo "  MacOS: brew install exiftool"
    exit 1
fi

echo
echo "Processing images in: $(pwd)"
echo "----------------------------------------"

EXTENSIONS=("jpg" "jpeg" "png" "tif" "tiff" "webp" "heic")

for ext in "${EXTENSIONS[@]}"; do
    find . -maxdepth 1 -type f -iname "*.${ext}" -print0 | while IFS= read -r -d '' file; do

        echo
        echo "========================================"
        echo "Image: $file"
        echo "========================================"

        echo
        echo "Stripping metadata..."
        exiftool -all= -overwrite_original "$file" >/dev/null

        echo
        echo "Remaining metadata:"
        echo "----------------------------------------"

        exiftool "$file"

        echo
    done
done

echo "Finished."
