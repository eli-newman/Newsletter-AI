"""
Configuration settings for RSS Feed Summarizer

Focus: AI business ideas, ways to make money with AI, and IMPORTANT AI news only.
No celebrity gossip. No research-paper slop. No PR rewrites.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# RSS FEEDS — Curated for: AI business ideas · money with AI · frontier AI news
# Every URL below was probed and returned HTTP 200 at config time. Dead candidates
# (Anthropic news, a16z, every.to, Rundown beehiiv) were intentionally dropped.
# =============================================================================
RSS_FEEDS = [
    # --- GREG ISENBERG (full surface — newsletter, podcast, YouTube) ---
    "https://latecheckout.substack.com/feed",                                          # Greg's Letter (Substack)
    "https://rss2.flightcast.com/ordbkg8yojpehffas7vr7qpc.xml",                        # The Startup Ideas Podcast
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCPjNBjflYl0-HQtUvOx0Ibw",    # Greg Isenberg on YouTube

    # --- FRONTIER AI SIGNAL (engineer/builder-grade, very low slop ratio) ---
    "https://buttondown.com/ainews/rss",                        # AI News by smol.ai — premier AI engineering digest
    "https://www.latent.space/feed",                            # Latent Space (Swyx) — frontier AI eng + podcast
    "https://simonwillison.net/atom/everything/",               # Simon Willison — practical AI usage, weekly LLM roundups
    "https://importai.substack.com/feed",                       # Import AI (Jack Clark) — frontier model news + policy
    "https://www.interconnects.ai/feed",                        # Interconnects (Nathan Lambert) — frontier research, plain English
    "https://tldr.tech/api/rss/ai",                             # TLDR AI — daily 5-minute frontier digest
    "https://www.aitidbits.ai/feed",                            # AI Tidbits — practical AI for builders

    # --- TRENDING REPOS / LAUNCHES (what builders are actually shipping) ---
    "https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml",     # GitHub Trending — all languages, daily
    "https://mshibanami.github.io/GitHubTrendingRSS/daily/python.xml",  # GitHub Trending — Python (AI/ML hotspot)
    "https://github.com/trending/python.atom?since=daily",      # Native GitHub trending Python feed
    "https://github.blog/changelog/feed/",                      # GitHub product/AI feature launches
    "https://www.producthunt.com/feed?category=artificial-intelligence",  # PH AI launches daily
    "https://www.ycombinator.com/blog/rss/",                    # YC blog — startup launches, heavy AI

    # --- BUILDER / INDIE / "MAKE MONEY WITH AI" ---
    "https://www.indiehackers.com/feed.xml",                    # Indie revenue stories, AI side projects
    "https://news.ycombinator.com/rss",                         # HN front page
    "https://hnrss.org/show",                                   # Show HN — every launch a builder ships
    "https://hnrss.org/newest?q=AI+revenue",                    # HN: AI + revenue
    "https://hnrss.org/newest?q=AI+SaaS",                       # HN: AI + SaaS
    "https://hnrss.org/newest?q=micro+saas",                    # HN: micro-SaaS
    "https://hnrss.org/newest?q=startup+idea",                  # HN: startup idea
    "https://hnrss.org/newest?q=Greg+Isenberg",                 # HN discussion of Greg's ideas

    # --- IDEAS FACTORY — startup/micro-SaaS idea sources ---
    "https://old.reddit.com/r/SideProject/.rss",                # r/SideProject — what builders are shipping
    "https://old.reddit.com/r/microsaas/.rss",                  # r/microsaas — pure micro-SaaS ideas
    "https://old.reddit.com/r/SaaS/.rss",                       # r/SaaS — SaaS builders and ideas
    "https://old.reddit.com/r/EntrepreneurRideAlong/.rss",      # r/ERA — build-in-public revenue stories
    "https://old.reddit.com/r/indiehackers/.rss",               # r/indiehackers — indie revenue
    "https://old.reddit.com/r/nocode/.rss",                     # r/nocode — no-code AI builds, big monetization angle
    "https://old.reddit.com/r/automate/.rss",                   # r/automate — automation-business ideas
    "https://failory.com/blog/rss.xml",                         # Failory — startup failures + ideas
    "https://trends.vc/feed/",                                  # Trends.vc — niche trends, idea-mining gold
    "https://www.acquire.com/blog/rss",                         # Acquire.com — what SaaS is selling, at what multiples

    # --- AI BUSINESS / MARKET (frontier money moves) ---
    "https://www.theinformation.com/feed",                      # Premium AI business reporting
    "https://www.bensbites.com/feed",                           # Ben's Bites — curated builder-focused AI
    "https://stratechery.com/feed/",                            # Stratechery — strategic analysis of AI moves
    "https://blog.langchain.dev/rss/",                          # LangChain — agent building

    # --- MAJOR AI LAB ANNOUNCEMENTS (only the labs that move the market) ---
    "https://openai.com/blog/rss.xml",                          # OpenAI product launches
    "https://blog.google/technology/ai/rss/",                   # Google AI launches
    "https://huggingface.co/blog/feed.xml",                     # Hugging Face — open-source AI tools

    # --- WIDE-NET AI NEWS (with strong relevance filter downstream) ---
    "https://venturebeat.com/category/ai/feed/",                # AI biz news (filtered hard by relevance agent)
    "https://techcrunch.com/category/artificial-intelligence/feed/",  # Filtered hard — celebrity slop blocklisted
]

# =============================================================================
# TIME WINDOW — 48h so thin days don't ship 2-article emails
# =============================================================================
TIME_WINDOW = 48  # hours

# Minimum articles per digest. If we'd ship fewer, the relevance filter relaxes.
MIN_ARTICLES = 5

# =============================================================================
# TOPICS OF INTEREST — money + builder lens
# =============================================================================
TOPICS_OF_INTEREST = [
    "AI side hustle",
    "AI business idea",
    "Make money with AI",
    "AI SaaS",
    "AI product launch",
    "AI revenue",
    "AI startup funding",
    "AI automation business",
    "AI agent",
    "AI tool",
    "LLM application",
    "Indie hacker AI",
    "AI case study",
    "AI prompt playbook",
    "Greg Isenberg",
    "Late Checkout",
]

# Trusted creators whose content gets a relevance boost — their stuff is signal,
# not slop, even if the headline doesn't obviously match a keyword.
TRUSTED_CREATORS = [
    "greg isenberg",
    "late checkout",
    "pieter levels",
    "levelsio",
    "marc lou",
    "danny postma",
    "andrew chen",
    "lenny rachitsky",
    "ben tossell",
]

# =============================================================================
# CATEGORIES — Reader-intent buckets, not technology buckets
# =============================================================================
CATEGORIES = {
    "STARTUP_IDEAS": {
        "emoji": "💡",
        "label": "Startup & Micro-SaaS Ideas",
        "keywords": [
            "startup idea", "saas idea", "micro saas", "micro-saas", "business idea",
            "niche", "untapped", "underserved", "opportunity", "pain point",
            "validate", "validation", "i'm building", "im building", "i built",
            "side project", "weekend project", "mvp", "wedge",
        ],
        "url_patterns": [
            "reddit.com/r/sideproject", "reddit.com/r/saas", "reddit.com/r/microsaas",
            "reddit.com/r/entrepreneurridealong", "reddit.com/r/indiehackers",
            "reddit.com/r/nocode", "reddit.com/r/automate",
            "trends.vc", "failory.com", "acquire.com",
            "latecheckout.substack.com", "flightcast.com",
        ],
    },
    "MONEY_PLAYS": {
        "emoji": "💰",
        "label": "Make Money With AI",
        "keywords": [
            "side hustle", "make money", "revenue", "monetize",
            "monetization", "earn", "income", "freelance", "consulting",
            "passive income", "bootstrap", "indie", "solo founder", "solopreneur",
            "$", "mrr", "arr", "profit", "case study", "how i built", "how i made",
            "audience",
        ],
        "url_patterns": ["indiehackers.com", "stratechery", "every.to"],
    },
    "LAUNCHES_AND_PRODUCTS": {
        "emoji": "🚀",
        "label": "New Launches You Can Use",
        "keywords": [
            "launch", "launching", "released", "announces", "introduces",
            "show hn", "now available", "ga", "beta", "v1", "v2",
            "new tool", "new product", "shipped",
        ],
        "url_patterns": ["producthunt.com", "ycombinator.com/blog", "hnrss.org/show"],
    },
    "TOOLS_AND_PLAYBOOKS": {
        "emoji": "🛠️",
        "label": "Tools & Playbooks",
        "keywords": [
            "tutorial", "guide", "how to", "playbook", "workflow", "automation",
            "prompt", "template", "framework", "n8n", "zapier", "make.com",
            "agent", "rag", "fine-tune", "fine tuning", "no-code", "low-code",
            "build with", "stack",
        ],
        "url_patterns": ["langchain.dev", "huggingface.co", "bensbites", "therundown"],
    },
    "IMPORTANT_AI_NEWS": {
        "emoji": "📣",
        "label": "Important AI News",
        "keywords": [
            "openai", "anthropic", "claude", "gpt", "gemini", "llama",
            "model release", "benchmark", "outperforms", "state of the art",
            "acquires", "acquisition", "ipo", "valuation", "funding round",
            "series a", "series b", "series c", "raises",
        ],
        "url_patterns": ["openai.com", "anthropic.com", "blog.google", "theinformation.com"],
    },
    "MARKET_AND_MONEY_MOVES": {
        "emoji": "📈",
        "label": "Where the Money Is Going",
        "keywords": [
            "funding", "raised", "investment", "vc", "venture", "valuation",
            "deal", "partnership", "acquisition", "ipo", "billion", "million",
            "market share", "growth", "adoption",
        ],
        "url_patterns": ["a16z.com", "venturebeat", "theinformation.com"],
    },
}

# =============================================================================
# QUALITY BLOCKLIST — phrases that almost always signal slop
# Articles whose title matches any of these get dropped before LLM filtering.
# =============================================================================
TITLE_BLOCKLIST = [
    # Celebrity / personality slop
    "elon musk", "musk says", "altman says", "trump", "biden",
    # Opinion slop with no concrete play
    "will change everything", "is killing", "is dead", "is the future",
    "the rise of", "the fall of", "everything you need to know",
    # Pure gossip / drama
    "feud", "rant", "slams", "fires back", "takes shots", "twitter spat",
    "tweet", "x post", "imagines",
    # Generic listicle slop
    "top 10 ", "top 5 ", "best ai tools you", "ai tools you should",
    # Pure research-paper jargon (no actionable angle)
    "we propose", "we present a novel",
]

# =============================================================================
# Distribution
# =============================================================================
DISTRIBUTION = {
    "email": {
        "enabled": True,
        "recipient": os.getenv("EMAIL_RECIPIENTS", ""),
        "sender": os.getenv("SMTP_USER", ""),
        # Fallback subject — the dynamic subject agent overrides this per-send.
        "subject": "Your daily AI money & builder digest",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 465,
        "smtp_user": os.getenv("SMTP_USER"),
        "smtp_password": os.getenv("GMAIL_APP_PASSWORD"),
    }
}

# =============================================================================
# OpenAI / model config
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAIAPIKEY")

# Use gpt-4o-mini across the board — same/lower cost than gpt-3.5-turbo,
# dramatically better at nuanced filtering (which is the whole problem we have).
MODELS = {
    "relevance": "gpt-4o-mini",
    "categorization": "gpt-4o-mini",
    "ranking": "gpt-4o-mini",
    "macro_summary": "gpt-4o-mini",
    "micro_summary": "gpt-4o-mini",
    "subject_line": "gpt-4o-mini",
    # Idea of the Day is the centerpiece — use a stronger model for sharper ideas
    "idea_of_the_day": "gpt-4o",
}

# =============================================================================
# Feature flags
# =============================================================================
FEATURES = {
    "use_keyword_categorization": True,    # Free keyword categorization (LLM categorization is overkill)
    "enable_macro_summary": True,          # Daily overview at top
    "enable_keyword_filter": True,         # Pre-filter for AI/money relevance before LLM (saves cost)
    "enable_ai_summaries": True,           # ON — generates builder-focused TL;DRs (the whole point)
    "enable_dynamic_subject": True,        # LLM-written subject lines from top story
    "enable_title_blocklist": True,        # Drop slop titles before they hit the LLM
    "enable_idea_of_the_day": True,        # 💡 One fresh micro-SaaS pitch per email — the centerpiece
}

# Default model (kept for backward compatibility)
OPENAI_MODEL = "gpt-4o-mini"
