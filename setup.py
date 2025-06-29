#!/usr/bin/env python3
"""
Setup script for Drowsiness Detection System
Handles model download and environment setup
"""

import os
import urllib.request
import sys
import subprocess
import zipfile
from pathlib import Path

def download_file(url, filename):
    """Download file with progress bar"""
    def progress_hook(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        sys.stdout.write(f"\rDownloading {filename}: {percent}%")
        sys.stdout.flush()
    
    urllib.request.urlretrieve(url, filename, progress_hook)
    print(f"\n✅ Downloaded {filename}")

def setup_directories():
    """Create necessary directories"""
    directories = ['models', 'logs', 'sample_videos']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def download_models():
    """Download required model files"""
    model_url = "https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2"
    model_path = "models/shape_predictor_68_face_landmarks.dat.bz2"
    
    if not os.path.exists("models/shape_predictor_68_face_landmarks.dat"):
        print("📥 Downloading facial landmark model...")
        try:
            download_file(model_url, model_path)
            
            # Extract bz2 file
            import bz2
            with bz2.BZ2File(model_path, 'rb') as f_in:
                with open("models/shape_predictor_68_face_landmarks.dat", 'wb') as f_out:
                    f_out.write(f_in.read())
            
            os.remove(model_path)  # Remove compressed file
            print("✅ Model extracted successfully")
            
        except Exception as e:
            print(f"❌ Error downloading model: {e}")
            print("Please download manually from: https://github.com/davisking/dlib-models")
            return False
    else:
        print("✅ Model file already exists")
    
    return True

def create_sample_audio():
    """Create a sample alert sound"""
    if not os.path.exists("music.wav"):
        print("🎵 Creating sample alert sound...")
        try:
            # Create a simple beep sound
            import numpy as np
            from scipy.io.wavfile import write
            
            sample_rate = 44100
            duration = 2.0
            frequency = 800
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio = np.sin(2 * np.pi * frequency * t) * 0.5
            
            # Add fade in/out
            fade_samples = int(0.1 * sample_rate)
            audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
            audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            write("music.wav", sample_rate, (audio * 32767).astype(np.int16))
            print("✅ Sample alert sound created")
            
        except Exception as e:
            print(f"⚠️  Could not create sample audio: {e}")
            print("Please add your own 'music.wav' file for alerts")

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def create_run_scripts():
    """Create convenient run scripts"""
    
    # Streamlit run script
    streamlit_script = """#!/bin/bash
echo "🚀 Starting Drowsiness Detection Web App..."
streamlit run streamlit_app.py --server.port 8501 --server.address localhost
"""
    
    with open("run_webapp.sh", "w") as f:
        f.write(streamlit_script)
    
    # Real-time detection script
    realtime_script = """#!/bin/bash
echo "🎥 Starting Real-time Drowsiness Detection..."
python realtime_detector.py "$@"
"""
    
    with open("run_realtime.sh", "w") as f:
        f.write(realtime_script)
    
    # Make scripts executable on Unix systems
    if os.name != 'nt':
        os.chmod("run_webapp.sh", 0o755)
        os.chmod("run_realtime.sh", 0o755)
    
    # Windows batch files
    with open("run_webapp.bat", "w") as f:
        f.write("@echo off\necho Starting Web App...\nstreamlit run streamlit_app.py\npause")
    
    with open("run_realtime.bat", "w") as f:
        f.write("@echo off\necho Starting Real-time Detection...\npython realtime_detector.py %*\npause")
    
    print("✅ Run scripts created")

def main():
    print("="*60)
    print("🎯 DROWSINESS DETECTION SYSTEM SETUP")
    print("="*60)
    
    print("\n1️⃣  Setting up directories...")
    setup_directories()
    
    print("\n2️⃣  Installing requirements...")
    if not install_requirements():
        print("❌ Setup failed at requirements installation")
        return False
    
    print("\n3️⃣  Downloading models...")
    if not download_models():
        print("❌ Setup failed at model download")
        return False
    
    print("\n4️⃣  Creating sample audio...")
    create_sample_audio()
    
    print("\n5️⃣  Creating run scripts...")
    create_run_scripts()
    
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nNext steps:")
    print("1. For web interface: python -m streamlit run streamlit_app.py")
    print("2. For real-time detection: python realtime_detector.py")
    print("3. For video analysis: python realtime_detector.py --video your_video.mp4")
    print("\nFor hackathon demo:")
    print("- Use sample videos in the Streamlit app")
    print("- Show real-time detection locally")
    print("- Present analytics dashboard")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)