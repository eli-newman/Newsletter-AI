"""
Agent 2: Relevance Agent
Filters articles for relevance to AI topics
"""
from typing import List, Dict, Any
try:
    from . import config
except ImportError:
    import config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.cache import SQLiteCache
from langchain.globals import set_llm_cache
import sqlite3
import os
import hashlib
import json
from datetime import datetime
from .cache_utils import CacheTracker

class RelevanceAgent:
    def __init__(self, api_key=None, model=None):
        """Initialize the Relevance Agent"""
        self.api_key = api_key or config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Set up cache
        self.cache_dir = "cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        self.cache_db = f"{self.cache_dir}/langchain.db"
        set_llm_cache(SQLiteCache(database_path=self.cache_db))
        
        # Initialize cache tracker
        self.cache_tracker = CacheTracker()
        
        # Use GPT-3.5-turbo for relevance filtering (cost-effective, still high quality)
        self.model = model or config.MODELS.get("relevance", config.OPENAI_MODEL)
        print(f"🔍 RELEVANCE AGENT: Using {self.model} for cost-effective filtering")
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model_name=self.model,
            openai_api_key=self.api_key,
            temperature=0.2,
            request_timeout=30
        )
        
        # Relevance filtering prompt - balanced AI focus
        self.relevance_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a relevance filter for an AI/ML newsletter. Include articles about AI/ML technologies, tools, models, applications, and real-world AI use cases. Exclude general tech news that doesn't involve AI."),
            ("user", """Is this article about AI/ML technologies, tools, models, frameworks, or AI applications?

INCLUDE (AI-relevant):
- AI tools, frameworks, models, LLMs, agents, automation using AI
- AI infrastructure, deployment, training, fine-tuning
- Enterprise AI applications and use cases (e.g., AI in customer support, AI in workflows)
- AI research, papers, or breakthroughs
- Companies using AI in interesting ways
- AI agents, AI systems, AI-powered solutions

EXCLUDE (not AI-relevant):
- General cybersecurity news (data breaches, hacks) unless specifically about AI security
- General tech infrastructure (servers, networks) unless AI-specific
- Spectrum/network policy, regulatory decisions (unless AI-related)
- General business news without AI focus
- Articles where AI is only mentioned in passing, not the main topic

Title: {title}
Source: {source}
Summary: {summary}

Respond with JSON:
{{
  "is_relevant": true/false,
  "reason": "Brief explanation of why it is/isn't AI-relevant"
}}""")
        ])
    
    def _get_cache_key(self, title: str, content: str) -> str:
        """Generate a cache key for an article"""
        text = f"relevance:{title}:{content}"
        return hashlib.md5(text.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> tuple:
        """Check if article relevance is cached"""
        with sqlite3.connect(self.cache_db) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS article_relevance
            (cache_key TEXT PRIMARY KEY, is_relevant BOOLEAN, reason TEXT, timestamp TEXT)
            """)
            
            cursor.execute("SELECT is_relevant, reason FROM article_relevance WHERE cache_key = ?", (cache_key,))
            result = cursor.fetchone()
            
            return result if result else (None, None)
    
    def _save_cache(self, cache_key: str, is_relevant: bool, reason: str):
        """Save relevance evaluation to cache"""
        with sqlite3.connect(self.cache_db) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT OR REPLACE INTO article_relevance (cache_key, is_relevant, reason, timestamp) VALUES (?, ?, ?, ?)",
                (cache_key, is_relevant, reason, datetime.now().isoformat())
            )
            
            conn.commit()

    def filter_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter articles for relevance to AI topics"""
        print(f"\n🔍 RELEVANCE AGENT: Filtering {len(articles)} articles...")
        
        relevant_articles = []
        for article in articles:
            title = article.get('title', '')
            summary = article.get('summary', article.get('content', ''))[:500]
            source = article.get('source', 'Unknown')
            
            cache_key = self._get_cache_key(title, summary)
            cached_relevant, cached_reason = self._check_cache(cache_key)
            
            if cached_relevant is not None:
                self.cache_tracker.record_hit()
                if cached_relevant:
                    article['relevance_reason'] = cached_reason
                    relevant_articles.append(article)
            else:
                self.cache_tracker.record_miss()
                
                try:
                    response = (self.relevance_prompt | self.llm).invoke({
                        "title": title,
                        "source": source,
                        "summary": summary
                    })
                    
                    result = json.loads(response.content.strip())
                    is_relevant = result.get('is_relevant', False)
                    reason = result.get('reason', 'No reason provided')
                    
                    self._save_cache(cache_key, is_relevant, reason)
                    
                    if is_relevant:
                        article['relevance_reason'] = reason
                        relevant_articles.append(article)
                        
                except Exception as e:
                    print(f"Error in relevance agent for '{title}': {str(e)}")
        
        print(f"✅ Found {len(relevant_articles)} relevant articles ({len(relevant_articles)/len(articles)*100:.1f}%)")
        
        # Print cache statistics
        stats = self.cache_tracker.get_stats()
        print(f"Cache Stats - Hits: {stats['hits']}, Misses: {stats['misses']}, Hit Rate: {stats['hit_rate']}")
        
        return relevant_articles

# Helper function for easy use
def filter_relevant_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Helper function for relevance filtering"""
    agent = RelevanceAgent()
    return agent.filter_articles(articles)

if __name__ == "__main__":
    # Test the relevance agent
    from fetcher import RSSFetcher
    import keyword_filter
    
    fetcher = RSSFetcher()
    articles = fetcher.fetch_articles()
    filtered_articles = keyword_filter.filter_articles(articles)
    
    agent = RelevanceAgent()
    relevant = agent.filter_articles(filtered_articles[:10])
    print(f"\nRelevant articles: {len(relevant)}") 