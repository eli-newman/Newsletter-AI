"""
Main pipeline orchestrating 5 AI agents for RSS feed processing

Agent Flow:
1. Ingestion Agent (fetcher.py) - Pulls articles from RSS feeds (includes RSS summaries)
2. Relevance Agent (relevance.py) - Filters for relevant articles
3. Macro Summary Agent (overall_summary.py) - Creates daily digest overview  
4. Categorization Agent (categorization.py) - Tags articles with categories
5. Ranking Agent (ranking.py) - Orders articles by priority PER CATEGORY (only if >5 articles)
Note: Using RSS feed summaries directly (no AI summarization needed)
"""
try:
    from .agents.fetcher import RSSFetcher  # Agent 1: Ingestion
    from .agents.keyword_filter import filter_articles, assign_category  # Keyword pre-filter and categorization
    from .agents.relevance import filter_relevant_articles  # Agent 2: Relevance
    from .agents.overall_summary import generate_daily_overview  # Agent 3: Macro Summary
    from .agents.categorization import categorize_by_topic  # Agent 4: LLM Categorization (optional)
    from .agents.ranking import rank_articles_by_importance  # Agent 5: Ranking
    from .agents.deduplication import remove_duplicates  # Duplicate detection
    from .agents.summaries import generate_article_summaries  # Builder-focused TL;DRs
    from .agents.idea_of_the_day import generate_idea_of_the_day  # 💡 daily micro-SaaS pitch
    from . import config
except ImportError:  # pragma: no cover
    # Handle direct execution
    import sys
    from pathlib import Path
    package_root = Path(__file__).parent
    sys.path.insert(0, str(package_root))
    sys.path.insert(0, str(package_root / "agents"))
    from fetcher import RSSFetcher
    from keyword_filter import filter_articles, assign_category
    from relevance import filter_relevant_articles
    from overall_summary import generate_daily_overview
    from categorization import categorize_by_topic
    from ranking import rank_articles_by_importance
    from deduplication import remove_duplicates
    from summaries import generate_article_summaries
    from idea_of_the_day import generate_idea_of_the_day
    import config

# Import distribution from separate module
try:
    from distribution import use_distributor
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from distribution import use_distributor
from collections import defaultdict
from datetime import datetime
import time

# Import cost tracker for reporting
try:
    from cost_tracking import get_cost_tracker
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from cost_tracking import get_cost_tracker

def run_pipeline(email_recipients=None):
    """
    Run the complete 5-agent RSS feed processing pipeline.
    Uses RSS feed summaries directly (no AI summarization).

    Args:
        email_recipients: Optional override list/string for ad-hoc newsletters.

    Returns:
        Dictionary containing digest metadata and processing stats.
    """
    print("\n🤖 ===  5-AGENT AI PIPELINE STARTING ===")
    
    # Initialize analytics tracking
    try:
        from distribution.analytics import get_tracker
        tracker = get_tracker()
        tracker.start_processing()
        pipeline_start = time.time()
    except ImportError:
        tracker = None
        pipeline_start = time.time()
    
    # AGENT 1: Ingestion Agent
    stage_start = time.time()
    print("\n📡 AGENT 1 - INGESTION: Fetching articles from RSS feeds...")
    fetcher = RSSFetcher()
    articles = fetcher.fetch_articles()
    if tracker:
        tracker.track_stage("ingestion", time.time() - stage_start)
    
    if not articles:
        print("❌ No articles fetched. Exiting pipeline.")
        return {
            "success": False,
            "reason": "No articles fetched",
            "distribution": None,
            "stats": {},
        }
    
    # Remove duplicates before processing
    stage_start = time.time()
    print("\n🔍 DEDUPLICATION: Removing duplicate articles...")
    articles = remove_duplicates(articles)
    print(f"✅ {len(articles)} unique articles after deduplication")
    if tracker:
        tracker.track_stage("deduplication", time.time() - stage_start)
    
    # Pre-filter with keywords (optional - LLM relevance filter is smarter)
    keyword_filtered_articles = articles
    if config.FEATURES.get("enable_keyword_filter", False):
        stage_start = time.time()
        print("\n🔍 PRE-FILTER: Applying keyword filters...")
        keyword_filtered_articles = filter_articles(articles)
        print(f"✅ {len(keyword_filtered_articles)} articles passed keyword filter")
        if tracker:
            tracker.track_stage("keyword_filter", time.time() - stage_start)
        
        if not keyword_filtered_articles:
            print("❌ No articles passed keyword filtering. Exiting pipeline.")
            return {
                "success": False,
                "reason": "No articles passed keyword filtering",
                "distribution": None,
                "stats": {},
            }
    else:
        print("\n🔍 PRE-FILTER: Skipped (using LLM relevance filter only)")
        if tracker:
            tracker.track_stage("keyword_filter", 0)
    
    # AGENT 2: Relevance Agent
    stage_start = time.time()
    print("\n🎯 AGENT 2 - RELEVANCE: Filtering for AI-relevant articles...")
    relevant_articles = filter_relevant_articles(keyword_filtered_articles)
    if tracker:
        tracker.track_stage("relevance_filter", time.time() - stage_start)
    
    if not relevant_articles:
        print("❌ No relevant articles found. Exiting pipeline.")
        return {
            "success": False,
            "reason": "No relevant articles after filtering",
            "distribution": None,
            "stats": {},
        }
    
    # AGENT 3: Macro Summary Agent (Daily Digest Insight Generator) - Optional
    stage_start = time.time()
    daily_overview = None
    if config.FEATURES.get("enable_macro_summary", True):
        print("\n📊 AGENT 3 - MACRO SUMMARY: Generating daily digest overview...")
        daily_overview = generate_daily_overview(relevant_articles)
        print(f"✅ Daily Overview: {daily_overview}")
        if tracker:
            tracker.track_stage("macro_summary", time.time() - stage_start)
    else:
        print("\n📊 AGENT 3 - MACRO SUMMARY: Skipped (disabled in config)")
        if tracker:
            tracker.track_stage("macro_summary", 0)
    
    # AGENT 4: Categorization Agent - Use keyword-based or LLM categorization
    stage_start = time.time()
    print("\n🏷️ AGENT 4 - CATEGORIZATION: Categorizing all relevant articles...")
    if config.FEATURES.get("use_keyword_categorization", True):
        # Use free keyword-based categorization
        print("   Using keyword-based categorization (no LLM cost)")
        categorized_articles = []
        for article in relevant_articles:
            article['category'] = assign_category(article)
            categorized_articles.append(article)
        
        # Print category distribution
        from collections import Counter
        categories = [a.get('category', 'UNKNOWN') for a in categorized_articles]
        category_counts = Counter(categories)
        print("✅ Category distribution:")
        for cat, count in category_counts.items():
            print(f"  {cat}: {count} articles")
    else:
        # Use LLM-based categorization
        print("   Using LLM-based categorization")
        categorized_articles = categorize_by_topic(relevant_articles)
    
    if tracker:
        tracker.track_stage("categorization", time.time() - stage_start)
    
    # Group categorized articles by category
    articles_by_category = defaultdict(list)
    for article in categorized_articles:
        category = article.get('category', 'UNCATEGORIZED')
        articles_by_category[category].append(article)
    
    # AGENT 5: Ranking Agent - Rank PER CATEGORY only if more than 5 articles
    stage_start = time.time()
    print("\n🏆 AGENT 5 - RANKING: Ranking categories with >5 articles...")
    final_articles_by_category = {}
    total_final_articles = 0
    ranking_calls_saved = 0
    
    for category, cat_articles in articles_by_category.items():
        if len(cat_articles) > 5:
            print(f"📊 Ranking {len(cat_articles)} articles in {category} (>5 articles)...")
            # Rank to get top 5 in this category
            ranked_articles = rank_articles_by_importance(cat_articles, max_articles=5)
            final_articles_by_category[category] = ranked_articles
            total_final_articles += len(ranked_articles)
            print(f"✅ {category}: Selected top {len(ranked_articles)} from {len(cat_articles)} articles")
        else:
            # Keep all articles if 5 or fewer
            final_articles_by_category[category] = cat_articles
            total_final_articles += len(cat_articles)
            ranking_calls_saved += 1
            print(f"✅ {category}: Kept all {len(cat_articles)} articles (≤5, no ranking needed)")
    
    print(f"✅ Ranking complete - saved {ranking_calls_saved} LLM calls by skipping categories with ≤5 articles")
    print(f"✅ Total articles ready for distribution: {total_final_articles}")
    if tracker:
        tracker.track_stage("ranking", time.time() - stage_start)
    
    # AI SUMMARIES — builder-focused TL;DRs (What it is / Who / How to monetize)
    stage_start = time.time()
    if config.FEATURES.get("enable_ai_summaries", True):
        print("\n✏️  AI SUMMARIES: Generating builder-focused TL;DRs for final articles...")
        for category, cat_articles in final_articles_by_category.items():
            if cat_articles:
                final_articles_by_category[category] = generate_article_summaries(cat_articles)
        if tracker:
            tracker.track_stage("ai_summaries", time.time() - stage_start)
    else:
        print("\n📝 Using RSS feed summaries directly (AI summaries disabled in config)")
        for category, cat_articles in final_articles_by_category.items():
            for article in cat_articles:
                if not article.get('summary') and article.get('content'):
                    article['summary'] = article['content']
                elif not article.get('summary'):
                    article['summary'] = 'No summary available'
    
    # IDEA OF THE DAY — the centerpiece. One fresh micro-SaaS pitch per email.
    stage_start = time.time()
    idea_of_the_day = ""
    if config.FEATURES.get("enable_idea_of_the_day", True):
        print("\n💡 IDEA OF THE DAY: Generating one fresh micro-SaaS pitch...")
        idea_of_the_day = generate_idea_of_the_day(final_articles_by_category)
        if tracker:
            tracker.track_stage("idea_of_the_day", time.time() - stage_start)

    # Distribution
    stage_start = time.time()
    print("\n📧 DISTRIBUTION: Generating digest...")
    # Flatten all articles for count purposes
    all_final_articles = []
    for category_articles in final_articles_by_category.values():
        all_final_articles.extend(category_articles)

    # Generate dynamic subject line from the top stories (MONEY_PLAYS first if present)
    subject_line = None
    if config.FEATURES.get("enable_dynamic_subject", True):
        try:
            try:
                from .agents.subject_line import generate_subject_line
            except ImportError:
                from agents.subject_line import generate_subject_line
            priority_cats = [
                "STARTUP_IDEAS", "MONEY_PLAYS", "LAUNCHES_AND_PRODUCTS",
                "IMPORTANT_AI_NEWS", "TOOLS_AND_PLAYBOOKS", "MARKET_AND_MONEY_MOVES",
            ]
            top_pool = []
            for cat in priority_cats:
                top_pool.extend(final_articles_by_category.get(cat, []))
            top_pool = top_pool[:5] if top_pool else all_final_articles[:5]
            subject_line = generate_subject_line(daily_overview or "", top_pool)
            print(f"📬 Subject line for today: {subject_line}")
        except Exception as e:
            print(f"Subject line generation skipped: {e}")

    distribution_result = use_distributor(
        all_final_articles,
        final_articles_by_category,
        daily_overview,
        email_recipients=email_recipients,
        subject_override=subject_line,
        idea_of_the_day=idea_of_the_day,
    )
    if tracker:
        tracker.track_stage("distribution", time.time() - stage_start)
        processing_stats = tracker.end_processing()
        print(f"\n⏱️  Processing Time: {processing_stats.get('total_time', 0):.2f}s")
        print(f"   Stage breakdown:")
        for stage, duration in processing_stats.get('stages', {}).items():
            print(f"     • {stage}: {duration:.2f}s")
    
    print("\n🎉 === 5-AGENT PIPELINE COMPLETE ===")
    print(f"📊 Final Stats:")
    print(f"   • Started with: {len(articles)} articles")
    print(f"   • Keyword filtered: {len(keyword_filtered_articles)} articles")
    print(f"   • Relevant articles: {len(relevant_articles)}")
    print(f"   • Categories found: {len(articles_by_category)}")
    print(f"   • Ranking calls saved: {ranking_calls_saved}")
    print(f"   • Final articles (using RSS summaries): {len(all_final_articles)}")
    
    # Cost optimization summary
    optimizations = []
    if config.FEATURES.get("use_keyword_categorization", True):
        optimizations.append("Keyword-based categorization (free)")
    if not config.FEATURES.get("enable_macro_summary", True):
        optimizations.append("Macro summary disabled")
    if not config.FEATURES.get("enable_keyword_filter", False):
        optimizations.append("Keyword filter disabled (using LLM relevance only)")
    if config.MODELS.get("relevance") == "gpt-3.5-turbo":
        optimizations.append("GPT-3.5-turbo for relevance (~80% cheaper than GPT-4)")
    
    if optimizations:
        print(f"   • Cost optimizations: {', '.join(optimizations)}")
    
    # Print cost report
    cost_tracker = get_cost_tracker()
    cost_tracker.print_daily_report()

    stats = {
        "started": len(articles),
        "keyword_filtered": len(keyword_filtered_articles),
        "relevant": len(relevant_articles),
        "categories": len(articles_by_category),
        "ranking_calls_saved": ranking_calls_saved,
        "final_articles": len(all_final_articles),
        "summarization": "RSS feed summaries (no AI)",
        "generated_at": datetime.now().isoformat(),
    }

    return {
        "success": True,
        "distribution": distribution_result,
        "daily_overview": daily_overview,
        "articles_by_category": final_articles_by_category,
        "all_articles": all_final_articles,
        "stats": stats,
    }
if __name__ == "__main__":
    run_pipeline() 
