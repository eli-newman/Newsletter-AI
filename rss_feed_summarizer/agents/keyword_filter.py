"""
Keyword pre-filter + category assignment.

Pre-filter goal: kill obvious slop fast, before paying for an LLM call.
Category goal: bucket each article into a reader-intent category.
"""
from typing import List, Dict, Any

from .. import config

CATEGORIES = config.CATEGORIES
TITLE_BLOCKLIST = getattr(config, "TITLE_BLOCKLIST", [])
TRUSTED_CREATORS = [c.lower() for c in getattr(config, "TRUSTED_CREATORS", [])]


def _has_trusted_creator(title: str, content: str, summary: str, url: str) -> bool:
    """True if a trusted creator's name appears anywhere — their stuff is auto-signal."""
    if not TRUSTED_CREATORS:
        return False
    blob = f"{title} {content} {summary} {url}".lower()
    return any(name in blob for name in TRUSTED_CREATORS)


def _is_blocked_title(title: str) -> bool:
    """Drop articles whose title screams slop."""
    if not getattr(config, "FEATURES", {}).get("enable_title_blocklist", True):
        return False
    t = (title or "").lower()
    return any(phrase in t for phrase in TITLE_BLOCKLIST)


def filter_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Pre-filter articles for AI + builder/money relevance.

    Drops:
      - empty articles
      - slop titles (TITLE_BLOCKLIST)
      - articles with zero AI signal AND zero money signal
    """
    filtered = []
    dropped_blocklist = 0
    dropped_no_signal = 0

    # Lightweight AI signal — if none of these appear, almost certainly not for us.
    ai_signal_terms = [
        "ai", "artificial intelligence", "llm", "gpt", "claude", "gemini",
        "openai", "anthropic", "model", "agent", "automation", "machine learning",
        "ml ", "neural", "generative", "rag", "prompt", "fine-tune", "embedding",
    ]

    for article in articles:
        title = article.get("title", "")
        if not title or not (article.get("content") or article.get("summary")):
            continue

        if _is_blocked_title(title):
            dropped_blocklist += 1
            continue

        title_l = title.lower()
        content_l = (article.get("content") or "").lower()
        summary_l = (article.get("summary") or "").lower()
        url_l = (article.get("link") or "").lower()
        text = f"{title_l} {content_l} {summary_l}"

        # Must have at least one AI signal — otherwise it's not on-topic
        has_ai = any(term in text for term in ai_signal_terms)
        # OR it's from a source we trust to already be on-topic
        # (indie/builder feeds + idea-mining feeds where every post is potential signal)
        trusted_url = any(
            p in url_l
            for p in [
                "indiehackers.com", "producthunt.com", "ycombinator.com",
                "bensbites", "therundown", "every.to", "stratechery",
                "openai.com", "anthropic.com", "huggingface.co",
                # Idea-mining sources — every post is a startup/SaaS idea by nature
                "reddit.com/r/sideproject", "reddit.com/r/saas",
                "reddit.com/r/microsaas", "reddit.com/r/entrepreneurridealong",
                "reddit.com/r/indiehackers", "reddit.com/r/nocode",
                "reddit.com/r/automate",
                "trends.vc", "failory.com", "acquire.com",
                # Trusted creators' own feeds
                "latecheckout.substack.com", "flightcast.com",
            ]
        )
        # OR a trusted creator's name appears anywhere
        trusted_creator = _has_trusted_creator(title_l, content_l, summary_l, url_l)
        if not has_ai and not trusted_url and not trusted_creator:
            dropped_no_signal += 1
            continue

        # Score by category matches (used as a cheap "interesting-ness" proxy)
        total_matches = 0
        category_matches = set()
        for category, patterns in CATEGORIES.items():
            for keyword in patterns.get("keywords", []):
                if keyword.lower() in text:
                    total_matches += 1
                    category_matches.add(category)
            for pattern in patterns.get("url_patterns", []):
                if pattern.lower() in url_l:
                    total_matches += 2
                    category_matches.add(category)

        # Big boost for trusted creators — their stuff goes near the top.
        if trusted_creator:
            total_matches += 10
            article["trusted_creator"] = True

        article["match_score"] = total_matches
        article["category_matches"] = list(category_matches)
        filtered.append(article)

    filtered.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    print(
        f"\nKeyword pre-filter: {len(articles)} → {len(filtered)} "
        f"(blocked slop titles: {dropped_blocklist}, no AI signal: {dropped_no_signal})"
    )
    return filtered


def assign_category(article: Dict[str, Any]) -> str:
    """
    Bucket an article into one of the reader-intent categories.

    Priority order matters: MONEY_PLAYS wins over generic news because that's
    the newsletter's whole thesis.
    """
    title_l = (article.get("title") or "").lower()
    content_l = (article.get("content") or "").lower()
    summary_l = (article.get("summary") or "").lower()
    url_l = (article.get("link") or "").lower()
    text = f"{title_l} {content_l} {summary_l}"

    # Title gets 3x weight — title language is the strongest intent signal
    scores = {category: 0 for category in CATEGORIES.keys()}
    for category, patterns in CATEGORIES.items():
        for keyword in patterns.get("keywords", []):
            kw = keyword.lower()
            if kw in title_l:
                scores[category] += 3
            elif kw in text:
                scores[category] += 1
        for pattern in patterns.get("url_patterns", []):
            if pattern.lower() in url_l:
                scores[category] += 2

    max_score = max(scores.values()) if scores else 0
    if max_score == 0:
        return "IMPORTANT_AI_NEWS"  # safer default than the old INDUSTRY_AND_MARKET

    # Tie-break order — favor concrete ideas/money over generic news
    priority = [
        "STARTUP_IDEAS",
        "MONEY_PLAYS",
        "LAUNCHES_AND_PRODUCTS",
        "TOOLS_AND_PLAYBOOKS",
        "MARKET_AND_MONEY_MOVES",
        "IMPORTANT_AI_NEWS",
    ]
    for cat in priority:
        if scores.get(cat, 0) == max_score:
            return cat
    return "IMPORTANT_AI_NEWS"


def categorize_articles(articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Bucket articles into the reader-intent categories."""
    categorized = {key: [] for key in CATEGORIES}
    for article in articles:
        category = assign_category(article)
        article["category"] = category
        categorized[category].append(article)

    for category, articles_list in categorized.items():
        if articles_list:
            print(f"Category {category}: {len(articles_list)} articles")
    return categorized


if __name__ == "__main__":
    from .fetcher import RSSFetcher

    fetcher = RSSFetcher()
    all_articles = fetcher.fetch_articles()
    filtered = filter_articles(all_articles)
    categorized = categorize_articles(filtered)
    print(f"\nFiltered {len(filtered)} from {len(all_articles)} total")
    for category, articles in categorized.items():
        if articles:
            print(f"  {category}: {len(articles)} articles")
