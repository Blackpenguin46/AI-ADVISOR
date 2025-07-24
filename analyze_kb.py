#!/usr/bin/env python3
"""
Analyze the current knowledge base to see what Daily.dev content we actually have.
"""

import json
from datetime import datetime

def analyze_knowledge_base():
    """Analyze the current knowledge base."""
    with open('data/unified_knowledge_base.json', 'r') as f:
        kb = json.load(f)

    print('🔍 DETAILED KNOWLEDGE BASE ANALYSIS')
    print('=' * 60)

    # Analyze Daily.dev articles by date
    dailydev_articles = []
    youtube_videos = 0
    other_sources = {}

    for item in kb.values():
        if 'metadata' in item:
            metadata = item['metadata']
            source_type = metadata.get('source_type', 'unknown')
            author = metadata.get('author', 'Unknown')
            tags = metadata.get('tags', [])
            
            if source_type == 'video':
                youtube_videos += 1
            elif 'daily.dev' in tags or author == 'Daily.dev':
                dailydev_articles.append({
                    'title': metadata.get('title', 'No title'),
                    'date_added': metadata.get('date_added', 'Unknown'),
                    'original_source': metadata.get('original_source', 'Unknown'),
                    'url': metadata.get('source_url', 'No URL'),
                    'tags': tags
                })
            else:
                other_sources[author] = other_sources.get(author, 0) + 1

    print(f'📺 YouTube videos: {youtube_videos}')
    print(f'📰 Daily.dev articles: {len(dailydev_articles)}')
    print(f'🔍 Other sources: {sum(other_sources.values())}')

    if other_sources:
        print('\n❌ Found non-Daily.dev/YouTube sources:')
        for source, count in other_sources.items():
            print(f'   {source}: {count} articles')

    print('\n📅 Daily.dev articles by date:')
    date_counts = {}
    for article in dailydev_articles:
        date = article['date_added'][:10] if article['date_added'] != 'Unknown' else 'Unknown'
        date_counts[date] = date_counts.get(date, 0) + 1

    for date, count in sorted(date_counts.items(), reverse=True):
        print(f'   {date}: {count} articles')

    print('\n🔗 Recent Daily.dev articles (first 10):')
    for i, article in enumerate(dailydev_articles[:10]):
        print(f'   {i+1}. {article["title"][:70]}...')
        print(f'      Source: {article["original_source"]}')
        print(f'      Tags: {", ".join(article["tags"][:3])}...' if len(article["tags"]) > 3 else f'      Tags: {", ".join(article["tags"])}')
        print()

    # Check if we have recent Daily.dev content
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = datetime.now().replace(day=datetime.now().day-1).strftime('%Y-%m-%d')
    
    recent_count = sum(1 for article in dailydev_articles if article['date_added'].startswith(today) or article['date_added'].startswith(yesterday))
    
    print(f'\n📊 ANALYSIS SUMMARY:')
    print(f'   Total Daily.dev articles: {len(dailydev_articles)}')
    print(f'   Recent articles (today/yesterday): {recent_count}')
    print(f'   This is likely CACHED/OLD data - not comprehensive scraping!')
    print(f'   Expected: 1,000+ articles from full Daily.dev account')
    print(f'   Actual: {len(dailydev_articles)} articles')
    
    return len(dailydev_articles) < 1000

if __name__ == "__main__":
    needs_full_scraping = analyze_knowledge_base()
    if needs_full_scraping:
        print('\n🚨 RECOMMENDATION: Run comprehensive Daily.dev scraping to get thousands of articles!')