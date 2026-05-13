"""
Idea of the Day Agent.

Takes today's most signal-rich articles and synthesizes ONE concrete, shippable
AI micro-SaaS or business idea. Output is the centerpiece of the email — the
thing the reader screenshots and forwards.

The agent is grounded in real articles (not hallucinated) and forced into a
structured format so every issue's idea reads the same way.
"""
from typing import List, Dict, Any
import json
import hashlib
import os
import sqlite3
from datetime import datetime

from .. import config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

try:
    from cost_tracking import get_cost_tracker
except ImportError:  # pragma: no cover
    get_cost_tracker = None


# Priority order: ideas/money posts are the richest seed material.
SEED_PRIORITY = [
    "STARTUP_IDEAS",
    "MONEY_PLAYS",
    "LAUNCHES_AND_PRODUCTS",
    "TOOLS_AND_PLAYBOOKS",
    "IMPORTANT_AI_NEWS",
    "MARKET_AND_MONEY_MOVES",
]


def _pick_seed_articles(articles_by_category: Dict[str, List[Dict[str, Any]]],
                        n: int = 8) -> List[Dict[str, Any]]:
    """Pick the n most-promising seed articles, weighted by category priority."""
    seeds: List[Dict[str, Any]] = []
    for cat in SEED_PRIORITY:
        for a in articles_by_category.get(cat, []):
            seeds.append(a)
            if len(seeds) >= n:
                return seeds
    return seeds


def _cache_db_path() -> str:
    """Resolve cache DB; the relevance agent creates this on its own runs."""
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return f"{cache_dir}/langchain.db"


def _seed_signature(seeds: List[Dict[str, Any]]) -> str:
    """Stable hash of today's seed article titles — guards against duplicate spend."""
    payload = "||".join(sorted((a.get("title") or "") for a in seeds))
    return hashlib.md5(payload.encode()).hexdigest()


def _load_cached_idea(sig: str) -> str:
    db = _cache_db_path()
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS idea_of_the_day
            (sig TEXT PRIMARY KEY, idea_md TEXT, timestamp TEXT)
        """)
        cur.execute("SELECT idea_md FROM idea_of_the_day WHERE sig = ?", (sig,))
        row = cur.fetchone()
    return row[0] if row else ""


def _save_cached_idea(sig: str, idea_md: str) -> None:
    db = _cache_db_path()
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS idea_of_the_day
            (sig TEXT PRIMARY KEY, idea_md TEXT, timestamp TEXT)
        """)
        cur.execute(
            "INSERT OR REPLACE INTO idea_of_the_day (sig, idea_md, timestamp) VALUES (?, ?, ?)",
            (sig, idea_md, datetime.now().isoformat()),
        )
        conn.commit()


def generate_idea_of_the_day(articles_by_category: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Return a markdown-formatted "AI Idea of the Day" block, or an empty string
    if generation is disabled / fails / no seeds available.
    """
    if not config.FEATURES.get("enable_idea_of_the_day", True):
        return ""
    if not config.OPENAI_API_KEY:
        return ""

    seeds = _pick_seed_articles(articles_by_category, n=8)
    if not seeds:
        return ""

    sig = _seed_signature(seeds)
    cached = _load_cached_idea(sig)
    if cached:
        print("💡 Idea of the Day: retrieved from cache (same seed set)")
        return cached

    # Build a compact, scannable context for the LLM
    seed_lines = []
    for i, a in enumerate(seeds, 1):
        title = a.get("title", "")
        source = a.get("source", "")
        summary = (a.get("summary") or a.get("content") or "")[:240]
        seed_lines.append(f"{i}. [{source}] {title}\n   {summary}")
    seed_text = "\n\n".join(seed_lines)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a startup-idea machine in the style of Greg Isenberg / Pieter Levels / "
         "Marc Lou. You generate concrete, shippable micro-SaaS and AI side-hustle ideas. "
         "You hate vague platform-y ideas ('an AI marketplace'). You love sharp, ugly, "
         "specific ideas a single person could ship in 2-4 weekends. You ground ideas in "
         "real signals from today's news — never hallucinated trends."),
        ("user", """Below are today's most interesting AI/builder news items. Synthesize ONE concrete AI micro-SaaS / business idea inspired by what's in the news.

Hard rules:
- The idea must be specific, narrow, and shippable by one person in 2-4 weekends.
- Pick a real, painful niche — not "AI for [broad industry]".
- The monetization path must be clear ($X/mo per user, $Y per credit, etc.).
- Use plain language. No buzzwords. No "revolutionary", no "game-changer", no "leverage".
- Tie the idea to at least ONE of the seed articles by referencing it briefly in "The signal".

Output EXACTLY this markdown format (no extra lines, no preamble):

### 💡 AI Idea of the Day: <2-5 word name>

**The pain:** <one sentence — who hurts and how>

**The build:** <one sentence — what you ship, plain English, max 25 words>

**Who pays:** <specific niche — be granular, e.g. "real-estate investors who flip 5-15 properties/year">

**Pricing:** <concrete number — $X/mo or $Y per use>

**MVP in a weekend:** <one sentence — the cheapest version of the product, what tools (OpenAI API, n8n, Supabase, etc.)>

**Why now:** <one sentence — tie to a specific signal from the articles below>

**The signal:** <briefly cite the seed article number or source that inspired this>

Today's seed articles:
{seeds}
""")
    ])

    try:
        model = config.MODELS.get("idea_of_the_day", config.MODELS.get("micro_summary", "gpt-4o-mini"))
        llm = ChatOpenAI(
            model_name=model,
            openai_api_key=config.OPENAI_API_KEY,
            temperature=0.9,  # higher for divergent ideas
            request_timeout=45,
        )
        response = (prompt | llm).invoke({"seeds": seed_text})

        if get_cost_tracker:
            usage = response.response_metadata.get("token_usage", {}) if hasattr(response, "response_metadata") else {}
            if usage:
                get_cost_tracker().track_call(agent="idea_of_the_day", model=model, usage=usage)

        idea_md = (response.content or "").strip()
        if not idea_md.startswith("###"):
            # Light cleanup: strip code fences and ensure it leads with the heading
            idea_md = idea_md.strip("`")
            if idea_md.lower().startswith("markdown"):
                idea_md = idea_md[8:].lstrip()

        if not idea_md or "### 💡" not in idea_md and "### " not in idea_md:
            print("💡 Idea of the Day: LLM returned malformed output, skipping")
            return ""

        _save_cached_idea(sig, idea_md)
        print("💡 Idea of the Day: generated")
        return idea_md

    except Exception as e:
        print(f"Idea of the Day agent error: {e}")
        return ""
