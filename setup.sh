#!/bin/bash
set -e

echo "=== say-it setup ==="
echo ""

# System dependencies
echo "[1/3] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y xdotool xclip ffmpeg python3-pip python3-venv

# Python virtual environment
echo ""
echo "[2/3] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Python packages
echo ""
echo "[3/3] Installing Python packages (this may take a minute)..."
pip install --upgrade pip -q
pip install faster-whisper sounddevice numpy pynput pyperclip

echo ""
echo "=== Setup complete ==="
echo ""
echo "To run say-it:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "First run will download the Whisper large-v3 model (~3GB)."
echo "After that it loads from disk every time — no internet needed."
