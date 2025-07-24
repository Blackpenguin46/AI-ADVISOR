#!/usr/bin/env python3
"""
AI Advisor Setup Script
Installs all dependencies and prepares the system.
"""

import sys
import subprocess
import os
from pathlib import Path

def install_core_dependencies():
    """Install core dependencies for AI Advisor."""
    core_deps = [
        'streamlit>=1.29.0',
        'ollama>=0.1.7', 
        'plotly>=5.17.0',
        'PyPDF2>=3.0.0',
        'python-docx>=0.8.11',
        'beautifulsoup4>=4.12.2',
        'markdown>=3.5.0',
        'pandas>=2.1.4',
        'numpy>=1.24.3',
        'requests>=2.31.0'
    ]
    
    print("📦 Installing core dependencies...")
    cmd = [sys.executable, '-m', 'pip', 'install'] + core_deps
    subprocess.run(cmd, check=True)
    print("✅ Core dependencies installed!")

def install_daily_dev_dependencies():
    """Install Daily.dev integration dependencies."""
    daily_dev_deps = [
        'mcp>=1.0.0',
        'selenium>=4.15.0',
        'webdriver-manager>=4.0.0',
        'fastmcp>=0.3.0',
        'httpx>=0.25.0'
    ]
    
    print("📰 Installing Daily.dev integration dependencies...")
    try:
        cmd = [sys.executable, '-m', 'pip', 'install'] + daily_dev_deps
        subprocess.run(cmd, check=True)
        print("✅ Daily.dev dependencies installed!")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Failed to install Daily.dev dependencies (optional features)")
        return False

def check_chrome():
    """Check if Chrome is installed for Selenium."""
    chrome_paths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS
        '/usr/bin/google-chrome',  # Linux
        '/usr/bin/chromium-browser',  # Linux (Chromium)
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',  # Windows
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'  # Windows
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print("✅ Chrome browser found")
            return True
    
    print("⚠️  Chrome browser not found (needed for Daily.dev scraping)")
    print("   Install Chrome from: https://www.google.com/chrome/")
    return False

def create_data_directory():
    """Create data directory structure."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    subdirs = ["backups", "custom_models", "vector_db"]
    for subdir in subdirs:
        (data_dir / subdir).mkdir(exist_ok=True)
    
    print("✅ Data directories created")

def check_ollama():
    """Check if Ollama is installed and running."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is installed and accessible")
            
            # Check for models
            if 'llama' in result.stdout.lower() or 'mistral' in result.stdout.lower():
                print("✅ AI model found")
            else:
                print("⚠️  No AI models found. Install one with:")
                print("   ollama pull llama2")
            return True
        else:
            print("❌ Ollama not accessible")
            return False
    except FileNotFoundError:
        print("❌ Ollama not installed")
        print("   Download from: https://ollama.ai")
        return False

def main():
    """Main setup function."""
    print("🔧 AI Advisor Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    try:
        # Install core dependencies
        install_core_dependencies()
        
        # Install Daily.dev dependencies (optional)
        daily_dev_ok = install_daily_dev_dependencies()
        
        # Check Chrome for Daily.dev features
        if daily_dev_ok:
            check_chrome()
        
        # Create data directories
        create_data_directory()
        
        # Check Ollama
        ollama_ok = check_ollama()
        
        print("\n" + "=" * 40)
        print("📋 SETUP SUMMARY")
        print("=" * 40)
        
        print("✅ Core AI Advisor: Ready")
        print("✅ Multi-format resources: Ready")
        
        if daily_dev_ok:
            print("✅ Daily.dev integration: Ready")
        else:
            print("⚠️  Daily.dev integration: Limited (optional)")
        
        if ollama_ok:
            print("✅ AI consultation: Ready")
        else:
            print("❌ AI consultation: Needs Ollama setup")
        
        print("\n🚀 Start AI Advisor with: python run.py")
        
        if not ollama_ok:
            print("\n⚠️  First install Ollama and a model:")
            print("   1. Download Ollama: https://ollama.ai")
            print("   2. Install a model: ollama pull llama2")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Setup failed: {e}")
        print("Try running: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()