"""
Subject Line Agent.

Generates curiosity-driven email subject lines based on the day's top story.
Picks the best of N candidates using simple heuristics (numbers > vague, short > long,
curiosity gap > generic).
"""
from typing import List, Dict, Any
import re
import json

from .. import config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

try:
    from cost_tracking import get_cost_tracker
except ImportError:  # pragma: no cover
    get_cost_tracker = None


_FORBIDDEN = {
    "revolutionary", "groundbreaking", "game-changer", "game changer",
    "unleash", "unlock the power", "in the world of",
}


def _score_subject(s: str) -> float:
    """Heuristic score for a subject line — higher = better."""
    if not s:
        return -1.0
    s_low = s.lower()
    if any(bad in s_low for bad in _FORBIDDEN):
        return -1.0

    length = len(s)
    if length > 75:
        return -1.0  # gets truncated in most inboxes

    score = 0.0
    # Sweet spot: 30-55 chars
    if 30 <= length <= 55:
        score += 2.0
    elif 25 <= length <= 65:
        score += 1.0

    # Has a number or dollar amount — usually a CTR win
    if re.search(r"\$\d|[0-9]", s):
        score += 1.5

    # Curiosity / specificity markers
    if any(w in s_low for w in ["how", "why", "what", "this", "new", "just", "now"]):
        score += 0.5

    # Lowercase / sentence case feels more human than Title Case Newsletters
    if s == s.lower():
        score += 0.5

    # Penalize ALL CAPS and excessive emoji
    if sum(1 for c in s if c.isupper()) > length * 0.3:
        score -= 1.0
    if s.count("!") > 1:
        score -= 0.5

    return score


def generate_subject_line(
    daily_overview: str,
    top_articles: List[Dict[str, Any]],
    fallback: str = "Your daily AI money & builder digest",
) -> str:
    """Generate today's subject line from the day's top stories."""
    if not config.FEATURES.get("enable_dynamic_subject", True):
        return fallback
    if not config.OPENAI_API_KEY:
        return fallback

    # Build the context the LLM sees
    top_lines = []
    for a in (top_articles or [])[:5]:
        title = a.get("title", "")
        money = a.get("money_angle", "")
        if title:
            top_lines.append(f"- {title}" + (f"  (angle: {money})" if money else ""))
    context = "\n".join(top_lines) if top_lines else (daily_overview or "")

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You write email subject lines for a newsletter about making money with AI. "
         "Your subjects get OPENED. Style: lowercase, conversational, specific, curiosity gap. "
         "Think Morning Brew, not corporate press release. No emoji. No clickbait lies. "
         "Use real numbers/names from the articles when possible."),
        ("user", """Generate 5 subject line candidates for today's email based on the top stories below.

Rules:
- 30 to 55 characters each.
- Plain lowercase. No emoji.
- Reference a specific tool, dollar amount, company, or play from the stories — not a generic "AI roundup".
- Mix styles: one with a number, one curiosity-gap, one direct value prop, one news hook, one playbook hook.
- Never use: revolutionary, groundbreaking, game-changer, unleash.

Top stories today:
{context}

Reply with strict JSON only:
{{"candidates": ["...", "...", "...", "...", "..."]}}""")
    ])

    try:
        model = config.MODELS.get("subject_line", "gpt-4o-mini")
        llm = ChatOpenAI(
            model_name=model,
            openai_api_key=config.OPENAI_API_KEY,
            temperature=0.8,
            request_timeout=20,
        )
        response = (prompt | llm).invoke({"context": context})

        # Track cost
        if get_cost_tracker:
            usage = response.response_metadata.get("token_usage", {}) if hasattr(response, "response_metadata") else {}
            if usage:
                get_cost_tracker().track_call(agent="subject_line", model=model, usage=usage)

        text = (response.content or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]

        data = json.loads(text)
        candidates = [c for c in data.get("candidates", []) if isinstance(c, str)]
    except Exception as e:
        print(f"Subject line agent error: {e}")
        return fallback

    if not candidates:
        return fallback

    best = max(candidates, key=_score_subject)
    if _score_subject(best) <= 0:
        return fallback

    print(f"📬 Subject candidates: {candidates}")
    print(f"📬 Chosen: {best}")
    return best
