#!/bin/bash

# Configuration Variables
SOURCE_DIR="/mnt/user/domains"   # Directory containing VMs
BACKUP_DIR="/mnt/disks/share" # Backup destination directory
RETENTION_DAYS=14                 # Number of days to retain backups

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Get the current timestamp
TIMESTAMP=$(date +"%Y%m%d-%H%M")

# Backup each VM directory
for VM_DIR in "$SOURCE_DIR"/*; do
  if [ -d "$VM_DIR" ]; then
    # Extract directory name and format it
    VM_NAME=$(basename "$VM_DIR")
    VM_NAME_FORMATTED=$(echo "$VM_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

    # Create backup file name
    BACKUP_FILE="$BACKUP_DIR/$VM_NAME_FORMATTED-$TIMESTAMP.zip"

    # Create zip archive
    echo "Backing up $VM_DIR to $BACKUP_FILE"
    zip -r "$BACKUP_FILE" "$VM_DIR" >/dev/null 2>&1

    if [ $? -eq 0 ]; then
      echo "Backup successful: $BACKUP_FILE"
    else
      echo "Backup failed for $VM_DIR" >&2
      continue
    fi

    # Clean up old backups if retention is enabled
    if [ "$RETENTION_DAYS" -gt 0 ]; then
      echo "Cleaning up old backups for $VM_NAME_FORMATTED"
      find "$BACKUP_DIR" -type f -name "$VM_NAME_FORMATTED-*.zip" \
        -mtime +$RETENTION_DAYS -exec rm -v {} \;
    fi
  fi
done

# Completion message
echo "Backup process completed."