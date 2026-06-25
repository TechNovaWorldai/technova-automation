"""
TechNova World — Research Agent v5.0
Real-time AI news + topic research — har output mein SOURCE link hota hai.

Why this matters:
Generic AI writing makes up facts or gives vague claims with no backing.
This module forces every research output to carry a source — either a
real RSS article link, or an explicit "general knowledge, no live source"
flag — so readers (and you) know what's verifiable vs general commentary.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from utils import logger, Result, save_text
from ai_client import generate_text
import search_agent
import config as cfg


# ════════════════════════════════════════════════════════════
# NEWS WITH SOURCES
# ════════════════════════════════════════════════════════════

def get_news_with_sources(max_age_hours: int = 48, count: int = 8) -> Result:
    """
    Latest AI news fetch karo — har item ke saath source name + link.

    Returns:
        Result with list of dicts:
        [{"title", "source", "link", "summary", "published"}, ...]
    """
    logger.info("📰 Fetching news with sources...")
    try:
        articles = search_agent.fetch_all_news(max_age_hours=max_age_hours)
        if not articles:
            return Result.fail("No articles fetched from any RSS source — check internet/feeds")

        clean = []
        for a in articles[:count]:
            clean.append({
                "title":     a.get("title", "Untitled"),
                "source":    a.get("source", "Unknown"),
                "link":      a.get("link", ""),
                "summary":   a.get("summary", "")[:300],
                "published": a.get("published", ""),
            })

        logger.info(f"✅ {len(clean)} news items with sources ready")
        return Result.success(clean)
    except Exception as e:
        logger.error(f"News fetch failed: {e}")
        return Result.fail(str(e))


# ════════════════════════════════════════════════════════════
# TOPIC RESEARCH — generates a writeup WITH cited sources
# ════════════════════════════════════════════════════════════

def research_topic(topic: str, platform: str = "linkedin") -> Result:
    """
    Topic ke baare mein research karo:
      1. RSS articles check karo jo is topic se relevant hain
      2. Agar mile, unke source ke saath content likho
      3. Agar nahi mile, "general knowledge" flag ke saath likho
         (no fake source attribution)

    Returns:
        Result with {
            "content": str,
            "sources": [{"title","source","link"}, ...],
            "has_live_sources": bool,
            "platform": str,
        }
    """
    logger.info(f"🔍 Researching: {topic[:50]} [{platform}]")

    news_result = get_news_with_sources(count=20)
    relevant_sources = []

    if news_result:
        topic_words = set(re.findall(r"\w+", topic.lower())) - {
            "the", "a", "an", "is", "are", "for", "in", "on", "of", "to", "and"
        }
        for article in news_result.data:
            article_text = (article["title"] + " " + article["summary"]).lower()
            overlap = sum(1 for w in topic_words if w in article_text)
            if overlap >= 2:
                relevant_sources.append(article)

    relevant_sources = relevant_sources[:3]
    has_live_sources = len(relevant_sources) > 0

    if has_live_sources:
        sources_block = "\n".join(
            f"- [{s['source']}] {s['title']} — {s['link']}"
            for s in relevant_sources
        )
        prompt = f"""Write {platform} content about: "{topic}"

You have these REAL, CURRENT sources to base your content on:
{sources_block}

Audience: {cfg.AUDIENCE}
Brand: {cfg.BRAND_NAME}

RULES:
- Base your claims on the sources above — don't invent statistics
- Naturally reference what these sources reported (e.g. "According to [Source]...")
- If sources disagree or are unclear on something, say so honestly
- Write engaging, platform-appropriate content (hook, value, CTA)

Return ONLY the content."""
    else:
        prompt = f"""Write {platform} content about: "{topic}"

NOTE: No current/live news sources were found for this specific topic.
Write based on general knowledge, but:
- Do NOT invent fake statistics or fake studies
- Use phrases like "many developers report" instead of fake precise numbers
- Be clear this is general insight, not breaking news
- Focus on genuinely useful, evergreen advice instead

Audience: {cfg.AUDIENCE}
Brand: {cfg.BRAND_NAME}

Return ONLY the content."""

    content = generate_text(prompt, max_tokens=1300)
    if not content:
        return Result.fail("Content generation failed (all AI providers exhausted)")

    return Result.success({
        "content": content,
        "sources": relevant_sources,
        "has_live_sources": has_live_sources,
        "platform": platform,
        "topic": topic,
    })


def research_and_save(topic: str, platform: str = "linkedin") -> Result:
    """research_topic() + auto-save to generated/research/ with sources appended."""
    result = research_topic(topic, platform)
    if not result:
        return result

    data = result.data
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    safe_topic = re.sub(r"\W+", "_", topic[:30])

    out = f"TOPIC: {topic}\nPLATFORM: {platform}\n\n{data['content']}\n\n"
    out += "=" * 50 + "\nSOURCES\n" + "=" * 50 + "\n"
    if data["has_live_sources"]:
        for s in data["sources"]:
            out += f"- [{s['source']}] {s['title']}\n  {s['link']}\n"
    else:
        out += "No live sources found — content based on general knowledge.\n"

    out_dir = Path("generated/research")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = str(out_dir / f"{safe_topic}_{ts}.txt")
    save_text(path, out)

    data["saved_to"] = path
    return Result.success(data)


def format_sources_for_display(sources: List[Dict]) -> str:
    """Human-readable sources block — used in dashboard + exports."""
    if not sources:
        return "⚠️ No live sources — general knowledge only"
    lines = []
    for s in sources:
        lines.append(f"📰 {s['source']}: {s['title']}")
        if s.get("link"):
            lines.append(f"   🔗 {s['link']}")
    return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 55)
    print("🔍 TechNova World — Research Agent Test")
    print("=" * 55)

    if not cfg.GEMINI_API_KEY and not cfg.OPENROUTER_API_KEY:
        print("\n❌ No AI provider configured")
        exit(1)

    topic = input("\nTopic? (Enter=default): ").strip() or "OpenAI new model release"
    platform = input("Platform (linkedin/twitter/medium, Enter=linkedin): ").strip() or "linkedin"

    result = research_topic(topic, platform)
    if result:
        d = result.data
        print(f"\n{'='*55}")
        print(f"CONTENT:")
        print(f"{'='*55}")
        print(d["content"])
        print(f"\n{'='*55}")
        print(f"SOURCES ({'LIVE' if d['has_live_sources'] else 'NONE — general knowledge'}):")
        print(format_sources_for_display(d["sources"]))
    else:
        print(f"\n❌ Failed: {result.error}")
