# Daily.dev MCP Integration Setup Guide

This guide will help you set up the Daily.dev MCP integration to scrape articles from your Daily.dev account and add them to your AI Advisor's knowledge base.

## Prerequisites

1. A Daily.dev account (https://daily.dev)
2. Chrome browser (for cookie extraction)
3. The Enhanced AI Advisor system running

## Step 1: Extract Daily.dev Cookies

### Method 1: Using Browser Developer Tools

1. **Open Daily.dev in Chrome**
   - Go to https://app.daily.dev
   - Make sure you're logged in

2. **Open Developer Tools**
   - Press `F12` or right-click and select "Inspect"
   - Go to the "Application" tab
   - In the left sidebar, expand "Storage" → "Cookies"
   - Click on "https://app.daily.dev"

3. **Copy Important Cookies**
   Look for these cookies and copy their values:
   - `__session` or `session`
   - `auth-token` or `auth`
   - `user-id` or `uid`
   - Any other authentication-related cookies

### Method 2: Using the Cookie Extractor Script

```python
# Run this script to extract cookies automatically
python daily_dev_cookie_extractor.py
```

## Step 2: Configure the Daily.dev MCP Integration

Create a configuration file or update your existing config:

```python
# Example configuration
dailydev_config = {
    "cookies": {
        "__session": "your_session_cookie_value",
        "auth-token": "your_auth_token_value",
        "user-id": "your_user_id_value"
        # Add other cookies as needed
    },
    "headers": {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://app.daily.dev/"
    },
    "sync_interval_hours": 24,  # How often to sync
    "max_articles_per_sync": 100
}
```

## Step 3: Initialize and Use the Integration

```python
from src.integrations.dailydev_mcp import DailyDevMCP
from src.managers.vector_database import HybridKnowledgeBase

# Initialize knowledge base
knowledge_base = HybridKnowledgeBase("./data/vector_db", "./knowledge_base_final.json")

# Initialize Daily.dev MCP
dailydev_mcp = DailyDevMCP()

# Configure with your cookies
if dailydev_mcp.initialize(dailydev_config):
    print("Daily.dev MCP initialized successfully!")
    
    # Sync popular articles
    result = dailydev_mcp.sync_articles(
        knowledge_base, 
        max_articles=50, 
        feed_types=["popular", "recent"]
    )
    print(f"Sync result: {result}")
    
    # Sync your bookmarks
    bookmark_result = dailydev_mcp.sync_bookmarks(knowledge_base)
    print(f"Bookmark sync: {bookmark_result}")
    
    # Search for specific topics
    search_result = dailydev_mcp.search_and_add(
        knowledge_base, 
        "machine learning", 
        limit=20
    )
    print(f"Search result: {search_result}")
else:
    print("Failed to initialize Daily.dev MCP")
```

## Step 4: Automated Syncing

You can set up automated syncing by creating a scheduled task:

```python
import schedule
import time

def sync_dailydev():
    """Automated sync function."""
    if dailydev_mcp.is_available():
        result = dailydev_mcp.sync_articles(knowledge_base, max_articles=50)
        print(f"Automated sync completed: {result}")

# Schedule sync every 6 hours
schedule.every(6).hours.do(sync_dailydev)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

## Step 5: Integration with Main Application

Add Daily.dev integration to your main AI Advisor:

```python
# In your main application
from src.app import create_app

app = create_app()

# Add Daily.dev integration
dailydev_integration = DailyDevMCP()
if dailydev_integration.initialize(dailydev_config):
    # Add to app components
    app.components['dailydev_mcp'] = dailydev_integration
    
    # Enable real-time processing feature
    app.config_manager.enable_feature('real_time_video_processing')
    
    print("Daily.dev integration added to AI Advisor!")
```

## Available Features

### 1. Feed Syncing
- **Popular articles**: Most upvoted content
- **Recent articles**: Latest published content
- **Trending articles**: Currently trending topics

### 2. Bookmark Syncing
- Sync your personally bookmarked articles
- Automatically tagged as "bookmarked"
- Higher quality score due to personal curation

### 3. Search and Add
- Search Daily.dev for specific topics
- Add search results to knowledge base
- Tagged with search query for easy filtering

### 4. Content Enhancement
- Automatic quality scoring based on engagement
- Tag extraction and categorization
- Metadata preservation (author, source, etc.)

## Troubleshooting

### Common Issues

**"Failed to connect to Daily.dev"**
- Check that your cookies are valid and not expired
- Make sure you're logged into Daily.dev in your browser
- Try refreshing your session and extracting cookies again

**"405 Method Not Allowed"**
- Daily.dev may have changed their API endpoints
- Check if you need additional headers or authentication
- Try using different GraphQL queries

**"Rate limiting errors"**
- The scraper includes built-in rate limiting (1 second between requests)
- If you get rate limited, increase the delay in the scraper
- Consider reducing the number of articles per sync

### Cookie Expiration

Daily.dev cookies typically expire after some time. Signs of expired cookies:
- Authentication errors
- Empty results from API calls
- 401/403 HTTP status codes

**Solution**: Re-extract cookies from your browser and update the configuration.

### Advanced Configuration

```python
# Advanced configuration options
advanced_config = {
    "cookies": {
        # Your cookies here
    },
    "rate_limit_delay": 2.0,  # Increase delay between requests
    "retry_attempts": 3,      # Number of retry attempts
    "timeout_seconds": 30,    # Request timeout
    "user_agent": "Custom User Agent String",
    "proxy": {                # Optional proxy configuration
        "http": "http://proxy:port",
        "https": "https://proxy:port"
    }
}
```

## Privacy and Ethics

- **Respect Daily.dev's Terms of Service**: Only scrape content you have legitimate access to
- **Rate Limiting**: The integration includes rate limiting to avoid overwhelming Daily.dev's servers
- **Personal Use**: This integration is designed for personal knowledge base enhancement
- **Content Attribution**: All scraped content maintains proper attribution to original sources

## Next Steps

1. **Set up the integration** with your Daily.dev cookies
2. **Test the sync** with a small number of articles first
3. **Configure automated syncing** for regular updates
4. **Integrate with your AI Advisor** for enhanced consultation capabilities
5. **Monitor and maintain** the integration for optimal performance

The Daily.dev integration will significantly expand your AI Advisor's knowledge base with the latest tech articles, trends, and insights from the developer community!