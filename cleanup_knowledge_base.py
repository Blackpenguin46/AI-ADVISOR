#!/usr/bin/env python3
"""
Clean up Knowledge Base

Keep only YouTube videos and Daily.dev articles, remove everything else.
"""

import json
from pathlib import Path
from datetime import datetime


def clean_knowledge_base():
    """Clean the knowledge base to only keep YouTube videos and Daily.dev articles."""
    print("🧹 Cleaning knowledge base - keeping only YouTube videos and Daily.dev articles")
    
    # Load current knowledge base
    kb_file = Path("data/unified_knowledge_base.json")
    if not kb_file.exists():
        print("❌ Knowledge base file not found")
        return
    
    with open(kb_file, 'r', encoding='utf-8') as f:
        kb = json.load(f)
    
    print(f"📊 Original knowledge base: {len(kb)} items")
    
    # Filter to keep only YouTube videos and Daily.dev articles
    cleaned_kb = {}
    youtube_count = 0
    dailydev_count = 0
    
    for item_id, item_data in kb.items():
        if 'metadata' in item_data:
            metadata = item_data['metadata']
            source_type = metadata.get('source_type', '')
            author = metadata.get('author', '')
            tags = metadata.get('tags', [])
            source_url = metadata.get('source_url', '')
            
            # Keep YouTube videos (original knowledge base)
            if (source_type == 'video' or 
                'youtube.com' in source_url or 
                'IBM Technology' in author or
                'Google for Developers' in author or
                'codebasics' in author or
                'AssemblyAI' in author or
                'ByteByteGo' in author or
                'Neo4j' in author or
                'Microsoft Developer' in author or
                'Google Cloud Tech' in author or
                'Warp' in author or
                'Clover Park Technical College' in author):
                
                cleaned_kb[item_id] = item_data
                youtube_count += 1
                print(f"✅ Kept YouTube video: {metadata.get('title', 'Unknown')[:50]}...")
            
            # Keep Daily.dev articles
            elif (author == 'Daily.dev' or 
                  'daily.dev' in tags or 
                  'daily.dev' in str(tags).lower()):
                
                cleaned_kb[item_id] = item_data
                dailydev_count += 1
                print(f"✅ Kept Daily.dev article: {metadata.get('title', 'Unknown')[:50]}...")
            
            else:
                print(f"🗑️  Removed {author}: {metadata.get('title', 'Unknown')[:50]}...")
    
    print(f"\n📊 Cleanup Results:")
    print(f"   YouTube videos kept: {youtube_count}")
    print(f"   Daily.dev articles kept: {dailydev_count}")
    print(f"   Total items kept: {len(cleaned_kb)}")
    print(f"   Items removed: {len(kb) - len(cleaned_kb)}")
    
    # Backup original knowledge base
    backup_file = Path("data/unified_knowledge_base_backup.json")
    print(f"💾 Creating backup at {backup_file}")
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)
    
    # Save cleaned knowledge base
    print(f"💾 Saving cleaned knowledge base")
    with open(kb_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_kb, f, indent=2, ensure_ascii=False)
    
    print("✅ Knowledge base cleanup complete!")
    return youtube_count, dailydev_count


if __name__ == "__main__":
    clean_knowledge_base()