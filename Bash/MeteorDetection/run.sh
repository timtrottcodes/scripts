#!/bin/bash
# ----------------------------------------
# run.sh - Run scan.py using MetDetPy Python package
# ----------------------------------------

# Get the directory of this script (works anywhere)
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$BASE_DIR/metdet-env"
PACKAGE_DIR="$BASE_DIR/MetDetPy"
SCRIPT_NAME="$BASE_DIR/scan.py"
PACKAGE_REPO="https://github.com/LilacMeteorObservatory/MetDetPy.git"

# -----------------------------
# Clone the MetDetPy repo if it doesn't exist
# -----------------------------
if [ ! -d "$PACKAGE_DIR" ]; then
    echo "Cloning MetDetPy repository..."
    git clone "$PACKAGE_REPO" "$PACKAGE_DIR" || { echo "Failed to clone repository"; exit 1; }
else
    echo "MetDetPy repo already exists, pulling latest changes..."
    git -C "$PACKAGE_DIR" pull || echo "Warning: Failed to pull latest changes"
fi

# -----------------------------
# Create the virtual environment if it doesn't exist
# -----------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR" || { echo "Failed to create virtual environment"; exit 1; }
fi

# -----------------------------
# Activate the virtual environment
# -----------------------------
source "$VENV_DIR/bin/activate" || { echo "Failed to activate virtual environment"; exit 1; }

# -----------------------------
# Install MetDetPy package if not already installed
# -----------------------------
PACKAGE_NAME="MetDetPy"
if ! pip show "$PACKAGE_NAME" &>/dev/null; then
    echo "Installing MetDetPy package from local repo..."
    pip install -e "$PACKAGE_DIR" || { echo "Failed to install MetDetPy"; exit 1; }
else
    echo "MetDetPy is already installed."
fi

# -----------------------------
# Run the main Python script
# -----------------------------
echo "Running $SCRIPT_NAME..."
python3 "$SCRIPT_NAME" || { echo "Python script failed"; exit 1; }

# -----------------------------
# Deactivate virtual environment
# -----------------------------
deactivate
echo "Done."
