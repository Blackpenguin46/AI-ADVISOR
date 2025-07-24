#!/usr/bin/env python3
"""
Setup Authentication Guide

This script provides step-by-step instructions for setting up Daily.dev authentication.
"""

import sys
from pathlib import Path

def print_setup_guide():
    """Print the setup guide."""
    print("🔐 DAILY.DEV AUTHENTICATION SETUP GUIDE")
    print("=" * 60)
    print()
    print("To scrape thousands of articles from your Daily.dev account, you need to:")
    print()
    print("STEP 1: Run the authentication script")
    print("=" * 40)
    print("In a new terminal window, run:")
    print("   cd /Users/samoakes/Desktop/AI_ADVISOR")
    print("   python secure_github_dailydev_auth.py")
    print()
    print("STEP 2: Enter your GitHub credentials")
    print("=" * 40)
    print("When prompted, enter:")
    print("   • Your GitHub username or email")
    print("   • Your GitHub password")
    print()
    print("🔒 These will be encrypted and stored locally only!")
    print()
    print("STEP 3: Browser authentication")
    print("=" * 40)
    print("The script will:")
    print("   • Open Chrome browser")
    print("   • Navigate to Daily.dev")
    print("   • Click 'Sign in with GitHub'")
    print("   • Enter your GitHub credentials")
    print("   • Handle 2FA if you have it enabled")
    print("   • Save the authenticated session")
    print()
    print("STEP 4: Run comprehensive scraping")
    print("=" * 40)
    print("After authentication succeeds, run:")
    print("   python authenticated_comprehensive_scraper.py --target 3000")
    print()
    print("This will scrape 3,000+ articles from your Daily.dev account!")
    print()
    print("🎯 EXPECTED RESULTS:")
    print("   • 3,000+ Daily.dev articles (vs current 203)")
    print("   • Your personalized feed content")
    print("   • Bookmarked articles")
    print("   • All integrated into AI Advisor RAG system")
    print()
    print("💡 TROUBLESHOOTING:")
    print("   • Make sure Chrome is installed")
    print("   • Ensure you have a Daily.dev account linked to GitHub")
    print("   • If 2FA is enabled, have your phone ready")
    print()
    print("🚀 Ready to start? Run the authentication script in a new terminal!")

def check_prerequisites():
    """Check if prerequisites are met."""
    print("\n🔍 CHECKING PREREQUISITES...")
    print("=" * 30)
    
    # Check if Chrome is available
    import shutil
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser"
    ]
    
    chrome_found = False
    for chrome_path in chrome_paths:
        if Path(chrome_path).exists():
            chrome_found = True
            print(f"✅ Chrome found at: {chrome_path}")
            break
    
    if not chrome_found:
        print("❌ Chrome not found. Please install Google Chrome first.")
        print("   Download from: https://www.google.com/chrome/")
        return False
    
    # Check Python packages
    try:
        import selenium
        print("✅ Selenium package available")
    except ImportError:
        print("❌ Selenium not installed")
        return False
    
    try:
        import cryptography
        print("✅ Cryptography package available")
    except ImportError:
        print("❌ Cryptography not installed")
        return False
    
    print("✅ All prerequisites met!")
    return True

def main():
    """Main function."""
    print_setup_guide()
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install missing components.")
        return
    
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS:")
    print("1. Open a new terminal window")
    print("2. Navigate to this directory:")
    print("   cd /Users/samoakes/Desktop/AI_ADVISOR")
    print("3. Run the authentication script:")
    print("   python secure_github_dailydev_auth.py")
    print("4. Follow the prompts to enter your GitHub credentials")
    print("5. Complete the browser authentication")
    print("6. Run the comprehensive scraper when authentication is complete")
    print()
    print("🔐 Your credentials will be encrypted and stored securely!")

if __name__ == "__main__":
    main()