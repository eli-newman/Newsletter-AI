"""
Article fetcher for RSS feeds
"""
import feedparser
from datetime import datetime, timedelta
import time
from typing import List, Dict, Any

from .. import config
from dateutil import parser
import requests

class RSSFetcher:
    def __init__(self, feeds: List[str] = None, time_window_hours: int = None):
        # Use configured feeds and time window or provided values
        self.feeds = feeds or config.RSS_FEEDS
        self.time_window = time_window_hours or config.TIME_WINDOW
        
        # Set user agent and headers for polite scraping
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0',
            'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml'
        }
        
    def fetch_articles(self) -> List[Dict[str, Any]]:
        """
        Fetch articles from all configured RSS feeds within the specified time window
        """
        all_articles = []
        # Calculate cutoff time for article freshness
        cutoff_time = datetime.now() - timedelta(hours=self.time_window)
        
        # Process each feed URL with retry logic
        for feed_url in self.feeds:
            max_retries = 3
            retry_delay = 1
            response = None
            
            for attempt in range(max_retries):
                try:
                    # Rate limiting to be polite to servers
                    time.sleep(0.5)
                    
                    # Fetch feed content with proper headers
                    response = requests.get(feed_url, headers=self.headers, timeout=15)
                    if response.status_code == 200:
                        break  # Success, exit retry loop
                    elif attempt < max_retries - 1:
                        print(f"Warning: {feed_url} returned {response.status_code}, retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(retry_delay * (attempt + 1))
                    else:
                        print(f"Error fetching {feed_url}: HTTP status {response.status_code} after {max_retries} attempts")
                        response = None
                        break
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        print(f"Warning: Timeout fetching {feed_url}, retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(retry_delay * (attempt + 1))
                    else:
                        print(f"Error: Timeout fetching {feed_url} after {max_retries} attempts")
                        response = None
                        break
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        print(f"Warning: Error fetching {feed_url}: {str(e)}, retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(retry_delay * (attempt + 1))
                    else:
                        print(f"Error fetching {feed_url}: {str(e)} after {max_retries} attempts")
                        response = None
                        break
            
            # Skip if we didn't get a successful response
            if not response or response.status_code != 200:
                continue
            
            try:
                # Parse the feed and extract source name
                feed = feedparser.parse(response.text)
                source_name = feed.feed.title if hasattr(feed.feed, 'title') else feed_url
                
                # Process each article in the feed
                for entry in feed.entries:
                    # Handle various date formats
                    pub_date = None
                    struct = entry.get('published_parsed') or entry.get('updated_parsed')
                    if struct:
                        pub_date = datetime.fromtimestamp(time.mktime(struct))
                    else:
                        raw = entry.get('published') or entry.get('updated')
                        if raw:
                            try:
                                pub_date = parser.parse(raw)
                            except:
                                continue
                        else:
                            continue

                    # Skip older articles outside our time window
                    if pub_date < cutoff_time:
                        continue
                    
                    # Extract and normalize article data
                    article = {
                        'title': entry.title if hasattr(entry, 'title') else 'No Title',
                        'link': entry.link if hasattr(entry, 'link') else '',
                        'published': pub_date,
                        'summary': entry.summary if hasattr(entry, 'summary') else '',
                        'content': entry.content[0].value if hasattr(entry, 'content') and len(entry.content) > 0 else '',
                        'source': source_name
                    }
                    
                    # Use summary as content if no content available
                    if not article['content']:
                        article['content'] = article['summary']
                    
                    all_articles.append(article)
            except Exception as e:
                print(f"Error parsing feed from {feed_url}: {str(e)}")
                continue
        
        print(f"Fetched {len(all_articles)} articles")
        return all_articles

if __name__ == "__main__":
    # Test fetcher
    fetcher = RSSFetcher()
    articles = fetcher.fetch_articles()
    print(f"Fetched {len(articles)} articles") 