"""
Duplicate detection for articles
"""
from typing import List, Dict, Any
from difflib import SequenceMatcher
import hashlib
import re

def normalize_title(title: str) -> str:
    """Normalize title for comparison"""
    # Remove extra whitespace, convert to lowercase
    title = re.sub(r'\s+', ' ', title.strip().lower())
    # Remove common prefixes/suffixes
    title = re.sub(r'^(new|breaking|update|announcing):\s*', '', title)
    return title

def normalize_url(url: str) -> str:
    """Normalize URL for comparison"""
    # Remove query parameters and fragments
    url = url.split('?')[0].split('#')[0]
    # Remove trailing slashes
    url = url.rstrip('/')
    return url.lower()

def title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles (0-1)"""
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    return SequenceMatcher(None, norm1, norm2).ratio()

def url_similarity(url1: str, url2: str) -> float:
    """Calculate similarity between two URLs (0-1)"""
    norm1 = normalize_url(url1)
    norm2 = normalize_url(url2)
    
    # Exact match
    if norm1 == norm2:
        return 1.0
    
    # Check if one URL contains the other (common for redirects)
    if norm1 in norm2 or norm2 in norm1:
        return 0.9
    
    # Calculate similarity
    return SequenceMatcher(None, norm1, norm2).ratio()

def is_duplicate(article1: Dict[str, Any], article2: Dict[str, Any], 
                 title_threshold: float = 0.85, url_threshold: float = 0.8) -> bool:
    """
    Check if two articles are duplicates
    
    Args:
        article1: First article
        article2: Second article
        title_threshold: Minimum title similarity to consider duplicate (0-1)
        url_threshold: Minimum URL similarity to consider duplicate (0-1)
    
    Returns:
        True if articles are likely duplicates
    """
    title1 = article1.get('title', '')
    title2 = article2.get('title', '')
    url1 = article1.get('link', '')
    url2 = article2.get('link', '')
    
    # Check URL similarity first (more reliable)
    url_sim = url_similarity(url1, url2)
    if url_sim >= url_threshold:
        return True
    
    # Check title similarity
    title_sim = title_similarity(title1, title2)
    if title_sim >= title_threshold:
        # If titles are very similar, check URLs are at least somewhat similar
        if url_sim >= 0.5:
            return True
    
    return False

def remove_duplicates(articles: List[Dict[str, Any]], 
                     title_threshold: float = 0.85,
                     url_threshold: float = 0.8) -> List[Dict[str, Any]]:
    """
    Remove duplicate articles from list
    
    Args:
        articles: List of articles
        title_threshold: Minimum title similarity to consider duplicate
        url_threshold: Minimum URL similarity to consider duplicate
    
    Returns:
        List of unique articles (keeps first occurrence)
    """
    if not articles:
        return articles
    
    unique_articles = []
    seen_hashes = set()
    
    for article in articles:
        # Create hash for quick exact duplicate check
        title = normalize_title(article.get('title', ''))
        url = normalize_url(article.get('link', ''))
        article_hash = hashlib.md5(f"{title}:{url}".encode()).hexdigest()
        
        # Check exact duplicates first
        if article_hash in seen_hashes:
            continue
        
        # Check for similar duplicates
        is_dup = False
        for unique_article in unique_articles:
            if is_duplicate(article, unique_article, title_threshold, url_threshold):
                is_dup = True
                # Merge sources if different
                if article.get('source') != unique_article.get('source'):
                    sources = unique_article.get('sources', [unique_article.get('source')])
                    if article.get('source') not in sources:
                        sources.append(article.get('source'))
                        unique_article['sources'] = sources
                break
        
        if not is_dup:
            unique_articles.append(article)
            seen_hashes.add(article_hash)
    
    removed = len(articles) - len(unique_articles)
    if removed > 0:
        print(f"✅ Removed {removed} duplicate article(s)")
    
    return unique_articles

