"""
Agent 4: Ranking Agent
Orders articles by priority based on innovation, utility, and strategic impact
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
import os
import json
import hashlib
import sqlite3
from datetime import datetime
from .cache_utils import CacheTracker

class RankingAgent:
    def __init__(self, api_key=None, model=None):
        """Initialize the Ranking Agent"""
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
        self.cache_tracker = CacheTracker(cost_per_call=0.02)
        
        # Use GPT-3.5 Turbo for ranking (cost-effective)
        self.model = model or config.MODELS.get("ranking", config.OPENAI_MODEL)
        print(f"📊 RANKING AGENT: Using {self.model} for cost-effective ranking")
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model_name=self.model,
            openai_api_key=self.api_key,
            temperature=0.2,
            request_timeout=30
        )
        
        # Ranking prompt
        self.ranking_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a ranking agent. Order articles by priority based on innovation, utility, and strategic impact for a tech-savvy AI audience."),
            ("user", """Rank the following articles from most to least relevant for a tech-savvy AI audience based on innovation, utility, or strategic impact.

Articles:
{articles}

Return a JSON array of article indices (0-based) in order of importance: [2, 0, 1, 3, 4]""")
        ])

    def _get_cache_key(self, articles: List[Dict[str, Any]]) -> str:
        """Create a cache key based on article titles and sources."""
        serialized = "|".join(
            f"{article.get('title','').strip()}::{article.get('source','').strip()}"
            for article in articles
        )
        return hashlib.md5(f"ranking:{serialized}".encode()).hexdigest()

    def _check_cache(self, cache_key: str):
        """Return cached ranking indices if present."""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS article_ranking
            (cache_key TEXT PRIMARY KEY, indices TEXT, timestamp TEXT)
            """
        )
        cursor.execute("SELECT indices FROM article_ranking WHERE cache_key = ?", (cache_key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return None
        return None

    def _save_cache(self, cache_key: str, indices: List[int]) -> None:
        """Persist ranking indices for reuse."""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO article_ranking (cache_key, indices, timestamp)
            VALUES (?, ?, ?)
            """,
            (cache_key, json.dumps(indices), datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

    def rank_articles(self, articles: List[Dict[str, Any]], max_articles: int = 5) -> List[Dict[str, Any]]:
        """Rank articles by importance and return top N"""
        if len(articles) <= max_articles:
            return articles
        
        print(f"\n📊 RANKING AGENT: Ranking {len(articles)} articles, selecting top {max_articles}...")
        
        # Prepare article summaries for ranking
        article_texts = []
        for i, article in enumerate(articles):
            title = article.get('title', 'No Title')
            summary = article.get('summary', article.get('content', ''))[:200]
            source = article.get('source', 'Unknown')
            article_texts.append(f"[{i}] {title} (from {source})\n{summary}")

        cache_key = self._get_cache_key(articles)
        cached_indices = self._check_cache(cache_key)
        if cached_indices:
            self.cache_tracker.record_hit()
            selected_indices = [idx for idx in cached_indices if idx < len(articles)]
            ranked_articles = [articles[i] for i in selected_indices][:max_articles]
            print(f"✅ Ranking retrieved from cache (saved an LLM call)")
            stats = self.cache_tracker.get_stats()
            print(f"Cache Stats - Hits: {stats['hits']}, Misses: {stats['misses']}, Hit Rate: {stats['hit_rate']}, Saved: {stats['estimated_savings']}")
            return ranked_articles

        self.cache_tracker.record_miss()
        
        try:
            response = (self.ranking_prompt | self.llm).invoke({
                "articles": "\n\n".join(article_texts)
            })
            
            # Parse indices from response
            response_text = response.content.strip()
            if response_text.startswith('[') and response_text.endswith(']'):
                indices = json.loads(response_text)
                indices = indices[:max_articles]
                ranked_articles = [articles[i] for i in indices if i < len(articles)]
                self._save_cache(cache_key, indices)
                print(f"✅ Selected top {len(ranked_articles)} articles")
                
                # Print cache statistics
                stats = self.cache_tracker.get_stats()
                print(f"Cache Stats - Hits: {stats['hits']}, Misses: {stats['misses']}, Hit Rate: {stats['hit_rate']}, Saved: {stats['estimated_savings']}")
                
                return ranked_articles
            
        except Exception as e:
            print(f"Error in ranking agent: {str(e)}")
        
        # Fallback: return first N articles
        print(f"⚠️ Ranking failed, returning first {max_articles} articles")
        stats = self.cache_tracker.get_stats()
        print(f"Cache Stats - Hits: {stats['hits']}, Misses: {stats['misses']}, Hit Rate: {stats['hit_rate']}, Saved: {stats['estimated_savings']}")
        return articles[:max_articles]

# Helper function for easy use
def rank_articles_by_importance(articles: List[Dict[str, Any]], max_articles: int = 5) -> List[Dict[str, Any]]:
    """Helper function for ranking articles"""
    agent = RankingAgent()
    return agent.rank_articles(articles, max_articles)

if __name__ == "__main__":
    # Test the ranking agent
    from fetcher import RSSFetcher
    import keyword_filter
    
    fetcher = RSSFetcher()
    articles = fetcher.fetch_articles()
    filtered_articles = keyword_filter.filter_articles(articles)
    
    agent = RankingAgent()
    ranked = agent.rank_articles(filtered_articles[:10], max_articles=5)
    print(f"\nRanked articles: {len(ranked)}") 
