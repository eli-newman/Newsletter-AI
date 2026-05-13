"""
Agent 2: Relevance Agent
Filters articles for relevance to AI topics
"""
from typing import List, Dict, Any

from .. import config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache
import sqlite3
import os
import hashlib
import json
from datetime import datetime
from ..utils.cache_utils import CacheTracker
from cost_tracking import get_cost_tracker

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
        
        # Initialize cost tracker
        self.cost_tracker = get_cost_tracker()
        
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
        
        # Trusted creators — auto-signal, the LLM should lean toward accepting.
        trusted = ", ".join(getattr(config, "TRUSTED_CREATORS", [])) or "none"

        # Relevance filter — hard bar: money/builder value or *major* AI news only.
        self.relevance_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are the gatekeeper for a newsletter about MAKING MONEY WITH AI. "
             "The reader is an indie builder / solopreneur / founder. They want: "
             "real ways to make money with AI, business ideas, new tools they can ship with, "
             "case studies with real revenue numbers, and the few AI announcements that actually move the market. "
             "You are RUTHLESS. You reject far more than you accept. Slop gets a flat no. "
             f"EXCEPTION: if the article is by or features any of these trusted creators, lean accept: {trusted}."),
            ("user", """Decide if this article belongs in the newsletter.

ACCEPT only if it clearly does ONE of these:
  1. Teaches a concrete way to make money with AI (side hustle, SaaS idea, freelance angle, automation business)
  2. Shows a real builder/founder revenue story or case study with numbers
  3. Launches a NEW AI tool or product the reader can actually use to build something
  4. Reports a MAJOR AI move (model release from OpenAI/Anthropic/Google, big funding round, big acquisition, market-shifting news)
  5. Shares an actionable prompt, playbook, workflow, or automation pattern
  6. Shares a concrete startup/SaaS/micro-SaaS idea or build-in-public story (from r/SideProject, r/microsaas, r/EntrepreneurRideAlong, r/SaaS, Failory, Trends.vc, Acquire.com, etc.) — even if AI is only implicit, these are idea fuel for our reader

REJECT (be aggressive):
  - Celebrity/personality drama (Musk, Altman quotes, executive tweets, opinion takes)
  - "AI will change everything" / "Rise of AI" / "Future of work" think pieces
  - Pure academic research with no shippable product or business angle
  - Listicles ("Top 10 AI tools you must try")
  - Vendor PR with no concrete new capability
  - Generic tech news that only mentions AI in passing
  - Cybersecurity breaches, regulatory minutiae, infra plumbing (unless AI-specific AND consequential)
  - Anything where you can't answer "what could a builder DO with this?"

Title: {title}
Source: {source}
Summary: {summary}

Reply with strict JSON only (no markdown, no prose):
{{"is_relevant": true|false, "money_angle": "one short sentence on the monetization/builder angle, or empty string if rejected", "reason": "why kept or killed"}}""")
        ])
    
    def _get_cache_key(self, title: str, content: str) -> str:
        """Generate a cache key for an article"""
        text = f"relevance:{title}:{content}"
        return hashlib.md5(text.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> tuple:
        """Return (is_relevant, reason, money_angle) or (None, None, None)."""
        with sqlite3.connect(self.cache_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS article_relevance
            (cache_key TEXT PRIMARY KEY, is_relevant BOOLEAN, reason TEXT, money_angle TEXT, timestamp TEXT)
            """)
            # Migrate older schema if needed
            cursor.execute("PRAGMA table_info(article_relevance)")
            cols = {row[1] for row in cursor.fetchall()}
            if "money_angle" not in cols:
                cursor.execute("ALTER TABLE article_relevance ADD COLUMN money_angle TEXT")

            cursor.execute(
                "SELECT is_relevant, reason, money_angle FROM article_relevance WHERE cache_key = ?",
                (cache_key,),
            )
            result = cursor.fetchone()
            return result if result else (None, None, None)

    def _save_cache(self, cache_key: str, is_relevant: bool, reason: str, money_angle: str = ""):
        """Persist relevance + money angle for reuse."""
        with sqlite3.connect(self.cache_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO article_relevance "
                "(cache_key, is_relevant, reason, money_angle, timestamp) VALUES (?, ?, ?, ?, ?)",
                (cache_key, is_relevant, reason, money_angle, datetime.now().isoformat()),
            )
            conn.commit()

    @staticmethod
    def _parse_json_loose(text: str) -> Dict[str, Any]:
        """Tolerate code fences and stray prose around a JSON object."""
        text = (text or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]
        return json.loads(text)

    def filter_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter articles for relevance to AI topics"""
        print(f"\n🔍 RELEVANCE AGENT: Filtering {len(articles)} articles...")
        
        relevant_articles = []
        for article in articles:
            title = article.get('title', '')
            summary = article.get('summary', article.get('content', ''))[:500]
            source = article.get('source', 'Unknown')
            
            cache_key = self._get_cache_key(title, summary)
            cached_relevant, cached_reason, cached_money_angle = self._check_cache(cache_key)

            if cached_relevant is not None:
                self.cache_tracker.record_hit()
                if cached_relevant:
                    article['relevance_reason'] = cached_reason
                    article['money_angle'] = cached_money_angle or ""
                    relevant_articles.append(article)
            else:
                self.cache_tracker.record_miss()

                try:
                    response = (self.relevance_prompt | self.llm).invoke({
                        "title": title,
                        "source": source,
                        "summary": summary,
                    })

                    usage = response.response_metadata.get('token_usage', {}) if hasattr(response, 'response_metadata') else {}
                    if usage:
                        self.cost_tracker.track_call(agent="relevance", model=self.model, usage=usage)

                    result = self._parse_json_loose(response.content)
                    is_relevant = bool(result.get('is_relevant', False))
                    reason = result.get('reason', 'No reason provided')
                    money_angle = result.get('money_angle', '') or ''

                    self._save_cache(cache_key, is_relevant, reason, money_angle)

                    if is_relevant:
                        article['relevance_reason'] = reason
                        article['money_angle'] = money_angle
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
    from rss_feed_summarizer.agents.fetcher import RSSFetcher
    from rss_feed_summarizer.agents.keyword_filter import filter_articles
    
    fetcher = RSSFetcher()
    articles = fetcher.fetch_articles()
    filtered_articles = filter_articles(articles)
    
    agent = RelevanceAgent()
    relevant = agent.filter_articles(filtered_articles[:10])
    print(f"\nRelevant articles: {len(relevant)}") 