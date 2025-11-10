"""
RSS Feed Summarizer

An intelligent RSS feed processor that fetches, filters, ranks, summarizes, 
and distributes AI technology news using a 6-agent AI pipeline.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .pipeline import run_pipeline
from .fetcher import RSSFetcher
# Distribution moved to separate 'distribution' module

__all__ = [
    "run_pipeline",
    "RSSFetcher",
]
