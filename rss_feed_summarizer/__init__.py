"""
RSS Feed Summarizer

An intelligent RSS feed processor that fetches, filters, ranks, summarizes, 
and distributes AI technology news using a 6-agent AI pipeline.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .pipeline import run_pipeline
from .agents.fetcher import RSSFetcher
from .agents.relevance import filter_relevant_articles
from .agents.categorization import categorize_by_topic
from .agents.ranking import rank_articles_by_importance
from .agents.overall_summary import generate_daily_overview
from .agents.summaries import generate_article_summaries
from .agents.keyword_filter import filter_articles, assign_category
from .agents.deduplication import remove_duplicates

__all__ = [
    "run_pipeline",
    "RSSFetcher",
    "filter_relevant_articles",
    "categorize_by_topic",
    "rank_articles_by_importance",
    "generate_daily_overview",
    "generate_article_summaries",
    "filter_articles",
    "assign_category",
    "remove_duplicates",
]
