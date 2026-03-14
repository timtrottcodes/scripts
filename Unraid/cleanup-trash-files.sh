#!/bin/bash

# Enable strict error handling
set -euo pipefail
IFS=$'\n\t'

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Directories to scan
declare -a sources=(
    "/mnt/user/share1"
    "/mnt/user/share2"
    "/mnt/user/share3"
    "/mnt/user/share4"
)

# Junk files and folders to remove
declare -a junk_items=(
    "desktop.ini"
    "Thumbs.db"
    "pspbrwse.jbf"
    ".DS_Store"
    ".Recycle.Bin"
    "\$RECYCLE.BIN"
    ".Trash-1000"
)

total_bytes=0

log() {
    echo "[CLEANUP] $1"
}

log "Starting cleanup... (dry run = $DRY_RUN)"

for path in "${sources[@]}"; do
    if [[ ! -d "$path" ]]; then
        log "Skipping missing directory: $path"
        continue
    fi

    log "Scanning: $path"

    for item in "${junk_items[@]}"; do
        matches=$(find "$path" -depth -name "$item" 2>/dev/null)

        if [[ -n "$matches" ]]; then
            while IFS= read -r target; do

                if [[ -f "$target" ]]; then
                    size=$(stat -c%s "$target" 2>/dev/null || echo 0)
                    total_bytes=$((total_bytes + size))
                    if $DRY_RUN; then
                        log "[DRY-RUN] Would delete file ($size bytes): $target"
                    else
                        log "Deleting file: $target"
                        rm -f "$target"
                    fi

                elif [[ -d "$target" ]]; then
                    # Calculate folder size BEFORE deletion
                    dir_size=$(du -sb "$target" 2>/dev/null | awk '{print $1}')
                    total_bytes=$((total_bytes + dir_size))

                    if $DRY_RUN; then
                        log "[DRY-RUN] Would delete folder ($dir_size bytes): $target"
                    else
                        log "Deleting folder: $target"
                        rm -rf "$target"
                    fi
                fi

            done <<< "$matches"
        fi
    done
done

# Convert bytes to human readable
human_size=$(numfmt --to=iec "$total_bytes")

echo ""
log "--------------------------------------------"
log "Total space that would be freed: $human_size ($total_bytes bytes)"
log "--------------------------------------------"

log "Cleanup complete."
exit 0
