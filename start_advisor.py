#!/usr/bin/env python3

"""
Startup script for Enhanced AI Advisor
This script handles the proper way to run the Streamlit application
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    required_packages = ['streamlit', 'ollama']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print("Install them with: pip install " + " ".join(missing))
        return False
    
    return True

def check_ollama():
    """Check if Ollama is running"""
    try:
        import ollama
        models = ollama.list()
        if models.get('models'):
            print(f"✅ Ollama is running with {len(models['models'])} models")
            return True
        else:
            print("⚠️  Ollama is running but no models found")
            print("Install a model with: ollama pull llama2")
            return True
    except Exception as e:
        print("❌ Ollama not available. Please install and start Ollama:")
        print("   1. Install: https://ollama.ai/")
        print("   2. Start: ollama serve")
        print("   3. Install model: ollama pull llama2")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting Enhanced AI Advisor...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check Ollama
    check_ollama()  # Don't exit if Ollama isn't available, just warn
    
    # Check if knowledge base exists
    kb_files = [
        "data/unified_knowledge_base.json",
        "knowledge_base_final.json"
    ]
    
    kb_found = False
    for kb_file in kb_files:
        if Path(kb_file).exists():
            print(f"✅ Knowledge base found: {kb_file}")
            kb_found = True
            break
    
    if not kb_found:
        print("⚠️  No knowledge base found. The app will work but with limited content.")
    
    print("=" * 50)
    print("🌟 Starting Streamlit application...")
    print("📱 The app will open in your browser automatically")
    print("🛑 Press Ctrl+C to stop the application")
    print("=" * 50)
    
    # Start Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "enhanced_main.py",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("\n🔧 Try running manually:")
        print("   streamlit run enhanced_main.py")

if __name__ == "__main__":
    main()