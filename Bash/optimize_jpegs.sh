#!/usr/bin/env bash

########################
# CONFIG
########################

START_DIR="/media/ttrott/Data-SSD/FolderWithLargeJpegs/"
MAX_DIMENSION=2500
JPEG_QUALITY=85
PROGRESSIVE=true
MIN_IMPROVEMENT_PERCENT=5   # Only replace if >= this %
TMP_DIR="/tmp/jpeg_optimize"
EXTENSIONS=("jpg" "jpeg" "JPG" "JPEG")

########################

mkdir -p "$TMP_DIR"

LOGFILE="$TMP_DIR/run.log"
BADFILE="$TMP_DIR/bad_images.log"

echo "" > "$LOGFILE"
echo "" > "$BADFILE"

# Build find args
FIND_ARGS=()
for ext in "${EXTENSIONS[@]}"; do
  FIND_ARGS+=(-iname "*.${ext}")
  FIND_ARGS+=(-o)
done
unset 'FIND_ARGS[${#FIND_ARGS[@]}-1]'

# Count total files first
TOTAL_FILES=$(find "$START_DIR" -type f \( "${FIND_ARGS[@]}" \) | wc -l)
CURRENT=0

TOTAL_BEFORE=0
TOTAL_AFTER=0
REPLACED_COUNT=0
SKIPPED_COUNT=0
FAILED_COUNT=0

echo "Scanning: $START_DIR"
echo "Found $TOTAL_FILES images"
echo

while IFS= read -r -d '' file; do
  CURRENT=$((CURRENT + 1))
  PERCENT=$(( CURRENT * 100 / TOTAL_FILES ))

  before=$(stat -c%s "$file")
  TOTAL_BEFORE=$((TOTAL_BEFORE + before))

  base=$(basename "$file")
  ppm="$TMP_DIR/${base%.*}.ppm"
  newjpg="$TMP_DIR/${base%.*}.new.jpg"

  # Decode + resize
  if ! magick "$file" -resize "${MAX_DIMENSION}x${MAX_DIMENSION}>" "$ppm" 2>>"$LOGFILE"; then
    echo "DECODE FAILED: $file"
    echo "$file" >> "$BADFILE"
    FAILED_COUNT=$((FAILED_COUNT + 1))
    continue
  fi

  # Encode
  jpeg_opts=(-quality "$JPEG_QUALITY")
  if [ "$PROGRESSIVE" = true ]; then
    jpeg_opts+=(-progressive)
  fi

  if ! cjpeg "${jpeg_opts[@]}" -outfile "$newjpg" "$ppm" 2>>"$LOGFILE"; then
    echo "ENCODE FAILED: $file"
    echo "$file" >> "$BADFILE"
    rm -f "$ppm"
    FAILED_COUNT=$((FAILED_COUNT + 1))
    continue
  fi

  # Final optimize temp file
  jpegoptim --strip-all --quiet "$newjpg"

  after=$(stat -c%s "$newjpg")

  saved=$((before - after))
  percent_saved=$(( saved * 100 / before ))

  before_h=$(numfmt --to=iec --suffix=B "$before")
  after_h=$(numfmt --to=iec --suffix=B "$after")
  saved_h=$(numfmt --to=iec --suffix=B "$saved")

  # Decide whether to replace
  if [ "$percent_saved" -ge "$MIN_IMPROVEMENT_PERCENT" ]; then
    mv "$newjpg" "$file"
    TOTAL_AFTER=$((TOTAL_AFTER + after))
    REPLACED_COUNT=$((REPLACED_COUNT + 1))

    echo "$PERCENT% ($CURRENT/$TOTAL_FILES) - $file was $before_h now $after_h saving $saved_h (-${percent_saved}%)"

  else
    TOTAL_AFTER=$((TOTAL_AFTER + before))
    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))

    echo "$PERCENT% ($CURRENT/$TOTAL_FILES) - $file unchanged (only -${percent_saved}%)"
  fi

  rm -f "$ppm" "$newjpg"

done < <(find "$START_DIR" -type f \( "${FIND_ARGS[@]}" \) -print0)

echo
echo "==================== SUMMARY ===================="
TOTAL_SAVED=$((TOTAL_BEFORE - TOTAL_AFTER))
TOTAL_PERCENT=$(( TOTAL_SAVED * 100 / TOTAL_BEFORE ))

echo "Files found      : $TOTAL_FILES"
echo "Files replaced   : $REPLACED_COUNT"
echo "Files skipped    : $SKIPPED_COUNT"
echo "Files failed     : $FAILED_COUNT"
echo
echo "Total before     : $(numfmt --to=iec --suffix=B "$TOTAL_BEFORE")"
echo "Total after      : $(numfmt --to=iec --suffix=B "$TOTAL_AFTER")"
echo "Total saved      : $(numfmt --to=iec --suffix=B "$TOTAL_SAVED")"
echo "Overall saving   : -${TOTAL_PERCENT}%"
echo
echo "Corrupt images logged to: $BADFILE"
