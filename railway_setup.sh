#!/bin/bash

# Install system dependencies for audio/video conversion
apt-get update
apt-get install -y ffmpeg libavcodec-extra

# Install Python dependencies
pip install -r requirements.txt

echo "✅ Dependencies installed successfully"