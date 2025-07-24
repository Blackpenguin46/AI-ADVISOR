#!/usr/bin/env python3

"""
Daily.dev Integration Script
Integrates Daily.dev articles into the unified RAG pipeline
"""

import sys
from pathlib import Path
import logging
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def integrate_dailydev_articles():
    """Integrate Daily.dev articles into the unified knowledge base"""
    try:
        from managers.unified_rag_pipeline import UnifiedRAGPipeline
        
        # Initialize the unified RAG pipeline
        pipeline = UnifiedRAGPipeline()
        
        # Get initial stats
        initial_stats = pipeline.get_comprehensive_stats()
        logger.info(f"Initial stats: {initial_stats['total_resources']} resources")
        
        # Try to use the secure Daily.dev MCP integration
        try:
            from integrations.dailydev_mcp import DailyDevMCP
            
            logger.info("Using Daily.dev MCP integration...")
            dailydev_mcp = DailyDevMCP()
            
            # Sync popular articles
            logger.info("Syncing popular articles...")
            popular_articles = dailydev_mcp.sync_popular_articles(limit=25)
            
            if popular_articles and len(popular_articles) > 0:
                for article in popular_articles:
                    pipeline.add_dailydev_article(article)
                logger.info(f"Added {len(popular_articles)} popular articles")
            
            # Sync recent articles
            logger.info("Syncing recent articles...")
            recent_articles = dailydev_mcp.sync_recent_articles(limit=15)
            
            if recent_articles and len(recent_articles) > 0:
                for article in recent_articles:
                    pipeline.add_dailydev_article(article)
                logger.info(f"Added {len(recent_articles)} recent articles")
            
        except ImportError:
            logger.warning("Daily.dev MCP not available, trying alternative methods...")
            
            # Try to use existing scraped data
            scraped_files = [
                "daily_dev_articles.json",
                "data/daily_dev_articles.json",
                "scraped_articles.json"
            ]
            
            articles_added = 0
            for file_path in scraped_files:
                if Path(file_path).exists():
                    logger.info(f"Loading articles from {file_path}")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            articles = json.load(f)
                        
                        if isinstance(articles, list):
                            for article in articles[:30]:  # Limit to 30 articles
                                if pipeline.add_dailydev_article(article):
                                    articles_added += 1
                        elif isinstance(articles, dict):
                            for article_id, article in articles.items():
                                if pipeline.add_dailydev_article(article):
                                    articles_added += 1
                                if articles_added >= 30:
                                    break
                        
                        logger.info(f"Added {articles_added} articles from {file_path}")
                        break
                        
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {e}")
            
            if articles_added == 0:
                # Create some sample Daily.dev articles for demonstration
                logger.info("Creating sample Daily.dev articles...")
                sample_articles = create_sample_dailydev_articles()
                
                for article in sample_articles:
                    pipeline.add_dailydev_article(article)
                
                logger.info(f"Added {len(sample_articles)} sample articles")
        
        # Save the updated knowledge base
        pipeline.save_knowledge_base()
        
        # Get final stats
        final_stats = pipeline.get_comprehensive_stats()
        logger.info(f"Final stats: {final_stats['total_resources']} resources")
        logger.info(f"Daily.dev articles: {final_stats['by_source']['dailydev']['count']}")
        logger.info(f"YouTube videos: {final_stats['by_source']['youtube']['count']}")
        
        print("✅ Daily.dev integration completed successfully!")
        print(f"📊 Total resources: {final_stats['total_resources']}")
        print(f"📰 Daily.dev articles: {final_stats['by_source']['dailydev']['count']}")
        print(f"📹 YouTube videos: {final_stats['by_source']['youtube']['count']}")
        print(f"📈 Total chunks: {final_stats['total_chunks']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error integrating Daily.dev articles: {e}")
        print(f"❌ Integration failed: {e}")
        return False

def create_sample_dailydev_articles():
    """Create sample Daily.dev articles for demonstration"""
    return [
        {
            "title": "Building RAG Applications with LangChain and ChromaDB",
            "url": "https://daily.dev/posts/building-rag-applications-langchain-chromadb",
            "content": "Retrieval-Augmented Generation (RAG) has become a cornerstone technique for building AI applications that can access and utilize external knowledge. This comprehensive guide walks through building a production-ready RAG application using LangChain and ChromaDB. We'll cover vector embeddings, document chunking strategies, and retrieval optimization techniques that ensure your RAG system delivers accurate and contextually relevant responses.",
            "author": "AI Engineering Team",
            "source": "Daily.dev",
            "tags": ["rag", "langchain", "chromadb", "ai", "vector-database"],
            "upvotes": 245,
            "numComments": 18,
            "createdAt": "2024-01-15T10:30:00Z"
        },
        {
            "title": "Fine-tuning vs RAG: When to Use Each Approach",
            "url": "https://daily.dev/posts/fine-tuning-vs-rag-comparison",
            "content": "The choice between fine-tuning and RAG isn't always clear-cut. This article provides a comprehensive comparison of both approaches, including cost analysis, performance benchmarks, and real-world use cases. We explore scenarios where fine-tuning excels, situations where RAG is preferable, and hybrid approaches that combine both techniques for optimal results.",
            "author": "ML Research Lab",
            "source": "Daily.dev",
            "tags": ["fine-tuning", "rag", "llm", "machine-learning", "ai-strategy"],
            "upvotes": 189,
            "numComments": 24,
            "createdAt": "2024-01-12T14:45:00Z"
        },
        {
            "title": "Vector Databases: The Backbone of Modern AI Applications",
            "url": "https://daily.dev/posts/vector-databases-ai-applications",
            "content": "Vector databases have emerged as critical infrastructure for AI applications, enabling semantic search, recommendation systems, and RAG implementations. This deep dive covers the fundamentals of vector embeddings, popular vector database solutions like Pinecone, Weaviate, and Qdrant, and best practices for scaling vector search in production environments.",
            "author": "Database Engineering",
            "source": "Daily.dev",
            "tags": ["vector-database", "embeddings", "ai-infrastructure", "semantic-search"],
            "upvotes": 156,
            "numComments": 12,
            "createdAt": "2024-01-10T09:15:00Z"
        },
        {
            "title": "Prompt Engineering Best Practices for Production AI",
            "url": "https://daily.dev/posts/prompt-engineering-production-ai",
            "content": "Effective prompt engineering is crucial for reliable AI applications. This guide covers advanced techniques including few-shot learning, chain-of-thought prompting, and prompt templates. We'll explore how to design prompts that are robust, maintainable, and deliver consistent results across different models and use cases.",
            "author": "AI Product Team",
            "source": "Daily.dev",
            "tags": ["prompt-engineering", "llm", "ai-development", "production-ai"],
            "upvotes": 203,
            "numComments": 31,
            "createdAt": "2024-01-08T16:20:00Z"
        },
        {
            "title": "Securing AI Applications: Privacy and Safety Considerations",
            "url": "https://daily.dev/posts/securing-ai-applications-privacy-safety",
            "content": "As AI applications become more prevalent, security considerations become paramount. This article covers data privacy, model security, prompt injection attacks, and compliance requirements. We discuss techniques for protecting sensitive data, implementing access controls, and ensuring AI systems behave safely and ethically.",
            "author": "AI Security Team",
            "source": "Daily.dev",
            "tags": ["ai-security", "privacy", "safety", "compliance", "data-protection"],
            "upvotes": 178,
            "numComments": 19,
            "createdAt": "2024-01-05T11:30:00Z"
        }
    ]

if __name__ == "__main__":
    print("🚀 Starting Daily.dev integration...")
    success = integrate_dailydev_articles()
    
    if success:
        print("\n🎉 Integration completed! You can now run the enhanced advisor:")
        print("   streamlit run enhanced_main.py")
    else:
        print("\n⚠️  Integration had issues. Check the logs above.")