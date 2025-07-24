#!/usr/bin/env python3

"""
Test script for enhanced_main.py to verify it works correctly
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work correctly"""
    try:
        import enhanced_main
        print("✅ Enhanced main imports successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_knowledge_base():
    """Test knowledge base functionality"""
    try:
        from enhanced_main import SimpleKnowledgeBase
        kb = SimpleKnowledgeBase()
        stats = kb.get_stats()
        
        print(f"✅ Knowledge base loaded:")
        print(f"   - Total resources: {stats['total_resources']}")
        print(f"   - Total chunks: {stats['total_chunks']}")
        print(f"   - YouTube videos: {stats['by_source']['youtube']['count']}")
        print(f"   - Daily.dev articles: {stats['by_source']['dailydev']['count']}")
        
        return True
    except Exception as e:
        print(f"❌ Knowledge base error: {e}")
        return False

def test_search():
    """Test search functionality"""
    try:
        from enhanced_main import SimpleKnowledgeBase
        kb = SimpleKnowledgeBase()
        results = kb.search_knowledge("machine learning", 3)
        
        print(f"✅ Search test:")
        print(f"   - Found {len(results)} results for 'machine learning'")
        
        if results:
            for i, result in enumerate(results[:2], 1):
                title = result['metadata']['title'][:50]
                print(f"   - Result {i}: {title}...")
        
        return True
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Enhanced AI Advisor...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_knowledge_base, 
        test_search
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! The application should work correctly.")
        print("\n🚀 To run the application:")
        print("   streamlit run enhanced_main.py")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()