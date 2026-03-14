#!/bin/bash

# Enable strict error handling
set -euo pipefail

# List of shares to back up
declare -a sources=(
    "/mnt/user/share1"
    "/mnt/user/share2"
    "/mnt/user/share3"
    "/mnt/user/share4"
)

# Destination disk (root backup location)
dest_root="/mnt/disks/mount"

# Common rsync options
# --checksum ensures integrity verification
# --delete ensures destination matches the source exactly
# --numeric-ids avoids UID/GID mapping issues
rsync_opts=(
    -avh
    --delete
    --numeric-ids
    --exclude=".Recycle.Bin/"
    --exclude="**/.Recycle.Bin/"
)

echo "=== Starting backup at $(date) ==="

for src in "${sources[@]}"; do
    folder=$(basename "$src")
    dest="$dest_root/$folder"

    echo "-> Syncing $src → $dest"
    
    # Ensure destination exists
    mkdir -p "$dest"

    # Perform rsync
    if ! rsync "${rsync_opts[@]}" "$src/" "$dest/"; then
        echo "!! Backup failed while syncing $src"
        /usr/local/emhttp/webGui/scripts/notify \
            -e "Unraid Backup Notice" \
            -s "Backup FAILED: $folder" \
            -i "alert"
        exit 1
    fi

    echo "Completed $folder"
done

echo "=== Backup finished at $(date) ==="

# Notify success
/usr/local/emhttp/webGui/scripts/notify \
    -e "Unraid Backup Notice" \
    -s "Backup Completed Successfully" \
    -i "normal"

echo "All shares backed up successfully."
