#!/usr/bin/env python3
"""
Comprehensive Test Runner

Runs all unit tests for the AI Advisor system.
"""

import sys
import subprocess
from pathlib import Path


def run_test_file(test_file: str, description: str) -> bool:
    """Run a specific test file and return success status."""
    print(f"\n🧪 {description}")
    print("=" * 80)
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=60)
        
        # Print stdout
        if result.stdout:
            print(result.stdout)
        
        # Print stderr if there are errors
        if result.stderr and result.returncode != 0:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def run_system_verification():
    """Run system verification checks."""
    print("\n🔍 System Verification Checks")
    print("=" * 80)
    
    checks_passed = 0
    total_checks = 0
    
    # Check 1: Knowledge base file exists
    total_checks += 1
    kb_file = Path("data/unified_knowledge_base.json")
    if kb_file.exists():
        print("✅ Knowledge base file exists")
        checks_passed += 1
    else:
        print("❌ Knowledge base file missing")
    
    # Check 2: Knowledge base has content
    total_checks += 1
    try:
        import json
        with open(kb_file, 'r') as f:
            kb = json.load(f)
        
        if len(kb) > 0:
            print(f"✅ Knowledge base has {len(kb)} items")
            checks_passed += 1
        else:
            print("❌ Knowledge base is empty")
    except Exception as e:
        print(f"❌ Cannot load knowledge base: {e}")
    
    # Check 3: Knowledge base has YouTube videos
    total_checks += 1
    try:
        youtube_count = 0
        for item in kb.values():
            if 'metadata' in item and item['metadata'].get('source_type') == 'video':
                youtube_count += 1
        
        if youtube_count > 0:
            print(f"✅ Knowledge base has {youtube_count} YouTube videos")
            checks_passed += 1
        else:
            print("❌ No YouTube videos found in knowledge base")
    except:
        print("❌ Cannot check YouTube videos")
    
    # Check 4: Knowledge base has Daily.dev articles
    total_checks += 1
    try:
        dailydev_count = 0
        for item in kb.values():
            if 'metadata' in item and 'daily.dev' in item['metadata'].get('tags', []):
                dailydev_count += 1
        
        if dailydev_count > 0:
            print(f"✅ Knowledge base has {dailydev_count} Daily.dev articles")
            checks_passed += 1
        else:
            print("❌ No Daily.dev articles found in knowledge base")
    except:
        print("❌ Cannot check Daily.dev articles")
    
    # Check 5: Required Python modules available
    total_checks += 1
    required_modules = ['requests', 'json', 'streamlit', 'ollama']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if not missing_modules:
        print("✅ All required Python modules available")
        checks_passed += 1
    else:
        print(f"❌ Missing Python modules: {missing_modules}")
    
    # Check 6: Daily.dev cookies file (optional)
    total_checks += 1
    cookie_file = Path("daily_dev_cookies.json")
    if cookie_file.exists():
        print("✅ Daily.dev cookies file exists (authenticated scraping available)")
        checks_passed += 1
    else:
        print("⚠️ Daily.dev cookies file missing (only public scraping available)")
        checks_passed += 1  # Not required for basic functionality
    
    print(f"\n📊 System Verification: {checks_passed}/{total_checks} checks passed")
    return checks_passed == total_checks


def main():
    """Main test runner function."""
    print("🚀 AI Advisor Comprehensive Test Suite")
    print("=" * 80)
    print("Testing YouTube videos and Daily.dev integration only")
    print()
    
    all_tests_passed = True
    test_results = {}
    
    # Test 1: YouTube Knowledge Base
    success = run_test_file("test_youtube_knowledge_base.py", 
                           "Testing YouTube Video Knowledge Base")
    test_results["YouTube Knowledge Base"] = success
    all_tests_passed = all_tests_passed and success
    
    # Test 2: Daily.dev Scraper
    success = run_test_file("test_dailydev_scraper.py", 
                           "Testing Daily.dev Scraper Functionality")
    test_results["Daily.dev Scraper"] = success
    all_tests_passed = all_tests_passed and success
    
    # Test 3: System Verification
    success = run_system_verification()
    test_results["System Verification"] = success
    all_tests_passed = all_tests_passed and success
    
    # Print final summary
    print("\n" + "=" * 80)
    print("🎯 FINAL TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name:<30} {status}")
    
    print(f"\nOverall Status: {'🎉 ALL TESTS PASSED' if all_tests_passed else '⚠️ SOME TESTS FAILED'}")
    
    if all_tests_passed:
        print("\n✅ Your AI Advisor system is working correctly!")
        print("   - YouTube videos are loaded and searchable")
        print("   - Daily.dev scraping is functional")
        print("   - Knowledge base integration works")
        print("   - System is ready to use")
    else:
        print("\n⚠️ Some issues found. Please check the test output above.")
    
    return all_tests_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)