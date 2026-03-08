#!/usr/bin/env bash
#
# flac_to_mp3.sh
#
# Recursively convert FLAC files to MP3 using ffmpeg.
# Designed for media server usage with configurable encoding settings,
# logging, metadata preservation, and safe file handling.
#
# Author: Tim Trott
# Date: 2026-03-07

set -euo pipefail
IFS=$'\n\t'

########################################
# Configuration
########################################

# Input directory containing FLAC files
INPUT_DIR="/home/ttrott/Documents/Flac2Mp3/in"

# Output directory for MP3 files
OUTPUT_DIR="/home/ttrott/Documents/Flac2Mp3/out"

# Logging
LOG_FILE="/home/ttrott/Documents/Flac2Mp3/flac_to_mp3.log"

# Encoder settings
ENCODER="libmp3lame"

# Encoding mode: cbr | vbr
ENCODE_MODE="vbr"

# CBR bitrate (used if ENCODE_MODE=cbr)
BITRATE="320k"

# VBR quality scale (0=best, 9=worst)
VBR_QUALITY="0"

# Channel configuration
# Options: copy | mono | stereo
CHANNEL_MODE="copy"

# Sample rate (empty = keep original)
SAMPLE_RATE=""

# Overwrite existing files
OVERWRITE=false

# Number of parallel conversions
PARALLEL_JOBS=2


########################################
# Functions
########################################

log() {
    local level="$1"
    local message="$2"
    if [[ -n "${LOG_FILE:-}" ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" | tee -a "$LOG_FILE"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message"
    fi
}

check_dependencies() {
    if ! command -v ffmpeg >/dev/null 2>&1; then
        log "ERROR" "ffmpeg is not installed"
        exit 1
    fi
}

build_audio_options() {

    AUDIO_OPTS=()

    if [[ "$ENCODE_MODE" == "cbr" ]]; then
        AUDIO_OPTS+=("-b:a" "$BITRATE")
    else
        AUDIO_OPTS+=("-qscale:a" "$VBR_QUALITY")
    fi

    case "$CHANNEL_MODE" in
        mono)
            AUDIO_OPTS+=("-ac" "1")
            ;;
        stereo)
            AUDIO_OPTS+=("-ac" "2")
            ;;
        copy)
            ;;
        *)
            log "ERROR" "Invalid CHANNEL_MODE: $CHANNEL_MODE"
            exit 1
            ;;
    esac

    if [[ -n "$SAMPLE_RATE" ]]; then
        AUDIO_OPTS+=("-ar" "$SAMPLE_RATE")
    fi
}

convert_file() {

    local input="$1"

    rel_path="${input#$INPUT_DIR/}"
    output="$OUTPUT_DIR/${rel_path%.flac}.mp3"

    mkdir -p "$(dirname "$output")"

    if [[ -f "$output" && "$OVERWRITE" = false ]]; then
        log "SKIP" "Exists: $output"
        return
    fi

    log "INFO" "Converting: $input"

    if ffmpeg -loglevel error -hide_banner \
        -i "$input" \
        -map_metadata 0 \
        -vn \
        -c:a "$ENCODER" \
        "${AUDIO_OPTS[@]}" \
        "$output"; then

        log "SUCCESS" "$output"

    else
        log "ERROR" "Failed: $input"
    fi
}

export -f convert_file
export -f log

export INPUT_DIR
export OUTPUT_DIR
export LOG_FILE
export ENCODER
export ENCODE_MODE
export BITRATE
export VBR_QUALITY
export CHANNEL_MODE
export SAMPLE_RATE
export OVERWRITE

########################################
# Main
########################################

check_dependencies
build_audio_options

log "INFO" "Starting FLAC → MP3 conversion"
log "INFO" "Input: $INPUT_DIR"
log "INFO" "Output: $OUTPUT_DIR"

find "$INPUT_DIR" -type f -iname "*.flac" -print0 |
    xargs -0 -n1 -P "$PARALLEL_JOBS" -I{} bash -c 'convert_file "$@"' _ {}

log "INFO" "Conversion completed"
