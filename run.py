#!/usr/bin/env python3
"""
AI Advisor - Simple Startup Script
Run with: python run.py
"""

import sys
import subprocess
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    required = [
        'streamlit', 'ollama', 'plotly', 'PyPDF2', 
        'python-docx', 'beautifulsoup4', 'markdown'
    ]
    
    missing = []
    for package in required:
        try:
            if package == 'python-docx':
                import docx
            elif package == 'PyPDF2':
                import PyPDF2
            else:
                __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

def install_dependencies(packages):
    """Install missing dependencies."""
    print("Installing missing dependencies...")
    cmd = [sys.executable, '-m', 'pip', 'install'] + packages
    subprocess.run(cmd, check=True)

def main():
    """Main startup function."""
    print("🚀 Starting AI Advisor...")
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        try:
            install_dependencies(missing)
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies. Please run manually:")
            print(f"pip install {' '.join(missing)}")
            return
    
    # Check if main file exists
    main_file = Path("enhanced_main.py")
    if not main_file.exists():
        print("❌ enhanced_main.py not found!")
        return
    
    # Start Streamlit
    print("🌟 Launching AI Advisor interface...")
    print("📱 Your browser should open automatically")
    print("🔗 If not, go to: http://localhost:8501")
    print("\n⏹️  Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            'enhanced_main.py', '--browser.serverAddress=localhost'
        ])
    except KeyboardInterrupt:
        print("\n👋 AI Advisor stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting AI Advisor: {e}")

if __name__ == "__main__":
    main()