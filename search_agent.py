"""
TechNova World — Search Agent v2.0
Real-time AI news fetch karta hai RSS feeds se
Gemini se summarize aur post-ready karta hai
"""

import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils import logger, retry, Result, save_text, save_json
import config as cfg

# ── RSS FEEDS ────────────────────────────────────────────────
AI_RSS_FEEDS = {
    "OpenAI Blog":       "https://openai.com/blog/rss.xml",
    "Anthropic News":    "https://www.anthropic.com/news/rss",
    "Google AI Blog":    "https://blog.google/technology/ai/rss/",
    "HuggingFace Blog":  "https://huggingface.co/blog/feed.xml",
    "MIT Tech Review AI":"https://www.technologyreview.com/feed/",
    "VentureBeat AI":    "https://venturebeat.com/category/ai/feed/",
    "TechCrunch AI":     "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI":      "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
}

GEMINI_URL = None  # deprecated — kept for backward compat, no longer used

BRAND_CTX = f"""You are the AI news analyst for {cfg.BRAND_NAME}.
Audience: {cfg.AUDIENCE}.
Always explain in simple terms — no jargon."""


# ── CORE FUNCTIONS ───────────────────────────────────────────

@retry(max_tries=2, delay=1.5)
def fetch_rss(url: str, source_name: str) -> List[Dict]:
    """Single RSS feed fetch karo"""
    headers = {
        "User-Agent": "TechNovaWorld-Bot/2.0 (AI Education; contact@technova.world)"
    }
    r = requests.get(url, headers=headers, timeout=cfg.API_TIMEOUT)
    r.raise_for_status()

    items = []
    try:
        root = ET.fromstring(r.content)
        # Handle both RSS and Atom formats
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        # RSS format
        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link  = item.findtext("link", "").strip()
            desc  = item.findtext("description", "").strip()
            pub   = item.findtext("pubDate", "").strip()

            # Clean HTML from description
            desc = re.sub(r"<[^>]+>", "", desc)[:500]

            if title and link:
                items.append({
                    "source": source_name,
                    "title":  title,
                    "link":   link,
                    "summary": desc,
                    "published": pub,
                })

        # Atom format (if RSS found nothing)
        if not items:
            for entry in root.findall(".//atom:entry", ns):
                title   = entry.findtext("atom:title", "", ns).strip()
                link_el = entry.find("atom:link", ns)
                link    = link_el.attrib.get("href", "") if link_el is not None else ""
                summary = entry.findtext("atom:summary", "", ns).strip()
                pub     = entry.findtext("atom:published", "", ns).strip()

                desc = re.sub(r"<[^>]+>", "", summary)[:500]
                if title and link:
                    items.append({
                        "source": source_name,
                        "title":  title,
                        "link":   link,
                        "summary": desc,
                        "published": pub,
                    })

    except ET.ParseError as e:
        logger.warning(f"RSS parse error ({source_name}): {e}")

    logger.info(f"  📡 {source_name}: {len(items)} articles fetched")
    return items[:5]   # latest 5 per source


def fetch_all_news(max_age_hours: int = 48) -> List[Dict]:
    """
    Saare RSS feeds se news fetch karo.
    Returns sorted list (newest first).
    """
    logger.info("🔍 AI news fetch kar raha hoon...")
    all_items = []
    errors = []

    for source, url in AI_RSS_FEEDS.items():
        try:
            items = fetch_rss(url, source)
            all_items.extend(items)
            time.sleep(0.5)   # polite delay
        except Exception as e:
            errors.append(f"{source}: {e}")
            logger.warning(f"⚠️  {source} skip — {e}")

    if errors:
        logger.warning(f"⚠️  {len(errors)} sources failed (network/parse issue)")

    # Deduplicate by title similarity
    seen_titles = set()
    unique = []
    for item in all_items:
        key = re.sub(r"\W+", "", item["title"].lower())[:50]
        if key not in seen_titles:
            seen_titles.add(key)
            unique.append(item)

    logger.info(f"✅ {len(unique)} unique articles fetched from {len(AI_RSS_FEEDS)} sources")
    return unique


def gemini_call(prompt: str) -> Optional[str]:
    """
    AI call — ab ai_client.py ke fallback chain se (Gemini 2.5 +
    OpenRouter free). Naam purana rakha hai backward-compat ke liye.
    Contract preserved: raises on total failure (callers wrap in try/except).
    """
    from ai_client import generate_text
    text = generate_text(BRAND_CTX + "\n\n" + prompt, max_tokens=1200)
    if text is None:
        raise Exception("All AI providers failed (Gemini 2.5 + OpenRouter exhausted)")
    return text


def summarize_news(articles: List[Dict], count: int = 6) -> Result:
    """
    Top articles ko TechNova World ke liye summarize karo
    """
    if not articles:
        return Result.fail("Koi article nahi mila")

    # Top articles select karo (first count)
    selected = articles[:count]
    articles_text = "\n\n".join([
        f"SOURCE: {a['source']}\nTITLE: {a['title']}\nSUMMARY: {a['summary'][:300]}"
        for a in selected
    ])

    prompt = f"""Analyze these AI news articles for TechNova World audience (AI learners, career switchers):

{articles_text}

For each article give:
1. 📰 **Headline** (rewritten simply)
2. 🔍 **Source**: [source name]
3. 💡 **Why it matters** (1 sentence, for beginners)
4. 🎯 **TechNova World angle** (best post angle)
5. 🔥 **Viral potential**: Low/Medium/High

Format clearly. Skip duplicates. Focus on genuinely important news."""

    try:
        result = gemini_call(prompt)
        return Result.success(result)
    except Exception as e:
        return Result.fail(str(e))


def generate_post_from_news(article: Dict, platform: str) -> Result:
    """
    Single article se platform-specific post generate karo
    """
    platform_specs = {
        "linkedin": """LinkedIn post rules:
- Line 1-2: Scroll-stopping hook (NEVER start with I/We/Excited/Happy)
- Body: Key insight, what it means for AI learners
- End: 1 genuine question to drive comments
- Last line: 5 hashtags (#AI #ArtificialIntelligence #AITools #MachineLearning #TechNova)
- Total: 150-300 words""",

        "twitter_single": """Single tweet rules:
- MAX 270 characters
- Strong hook or insight
- 2 relevant hashtags
- Optional: link placeholder [LINK]""",

        "twitter_5": """5 standalone tweets about this news:
Tweet 1: Breaking news hook
Tweet 2: Key insight/what changed
Tweet 3: What this means for AI beginners
Tweet 4: Question to audience
Tweet 5: CTA + link
Each tweet MAX 270 chars. Number them 1. 2. 3. etc.""",

        "medium_outline": """Medium article outline:
TITLE: [SEO title, 60 chars max]
SUBTITLE: [Compelling subtitle]
HOOK: [Opening paragraph - 2-3 lines]
SECTION 1: [heading + 3 points]
SECTION 2: [heading + 3 points]
SECTION 3: [heading + 3 points]
CONCLUSION: [1 paragraph + CTA]
SEO_TAGS: [5 tags]"""
    }

    spec = platform_specs.get(platform, platform_specs["linkedin"])
    prompt = f"""Write a {platform} post for {cfg.BRAND_NAME} based on this news:

Title: {article['title']}
Source: {article['source']}
Summary: {article['summary'][:400]}
Link: {article['link']}

{spec}

Audience: {cfg.AUDIENCE}
Tone: Educational, simple, no jargon. Make it genuinely useful."""

    try:
        result = gemini_call(prompt)
        return Result.success(result)
    except Exception as e:
        return Result.fail(str(e))


def get_trending_topics() -> Result:
    """Current trending AI topics fetch karo"""
    prompt = f"""List 8 trending AI topics RIGHT NOW that {cfg.BRAND_NAME} should cover.
Target: {cfg.AUDIENCE}

For each topic:
- **Topic name** (specific — mention actual products/models)
- Heat: 🔥 Low | 🔥🔥 Medium | 🔥🔥🔥 Viral
- Why trending (1 sentence)
- Best angle for TechNova World
- Best platform: LinkedIn / Twitter / Medium

Be specific. Mention real AI tools, models, companies."""

    try:
        result = gemini_call(prompt)
        return Result.success(result)
    except Exception as e:
        return Result.fail(str(e))


def validate_post_content(content: str, platform: str) -> Result:
    """
    Post content validate karo — length, format, quality check
    """
    errors = []
    warnings = []

    if not content or len(content.strip()) < 50:
        errors.append("Content too short (min 50 chars)")

    if platform == "twitter_single" and len(content) > 280:
        errors.append(f"Tweet too long: {len(content)} chars (max 280)")

    if platform == "linkedin":
        if len(content) < 100:
            warnings.append("LinkedIn post bahut short hai — engagement kam hoga")
        if not any(h in content for h in ["#AI", "#ArtificialIntelligence", "#MachineLearning"]):
            warnings.append("Hashtags missing — add karo")
        bad_starts = ["I am excited", "We are excited", "Happy to share", "I am happy"]
        for bad in bad_starts:
            if content.strip().startswith(bad):
                errors.append(f"Weak hook: starts with '{bad}' — change karo")

    for w in warnings:
        logger.warning(f"⚠️  Content warning: {w}")

    if errors:
        return Result.fail(" | ".join(errors))

    return Result.success({"content": content, "warnings": warnings})


# ── MAIN SEARCH AGENT ─────────────────────────────────────────

class SearchAgent:
    """
    TechNova World Search Agent
    Automatically news fetch, analyze, aur post generate karta hai
    """

    def __init__(self):
        self.last_fetch = None
        self.cache_file = "queue/news_cache.json"
        self.cache: List[Dict] = []

    def fetch_and_cache(self, force: bool = False) -> Result:
        """News fetch karo aur cache karo"""
        # Cache fresh hai toh reuse karo (1 hour)
        if not force and self.last_fetch:
            age = (datetime.now() - self.last_fetch).seconds / 3600
            if age < 1 and self.cache:
                logger.info(f"📦 Cache use kar raha hoon ({int(age*60)} min old)")
                return Result.success(self.cache)

        try:
            articles = fetch_all_news()
            self.cache = articles
            self.last_fetch = datetime.now()
            save_json(self.cache_file, articles)
            return Result.success(articles)
        except Exception as e:
            # Cache se fallback
            cached = save_json.__module__ and load_from_cache(self.cache_file)
            if cached:
                logger.warning(f"⚠️  Fresh fetch failed, cache use kar raha hoon: {e}")
                return Result.success(cached)
            return Result.fail(str(e))

    def run_daily_briefing(self) -> Result:
        """
        Daily AI news briefing generate karo
        - Top 6 news summarize
        - LinkedIn + Twitter drafts
        - Save to generated/ folder
        """
        logger.info("📰 Daily briefing shuru...")

        # Fetch news
        fetch_result = self.fetch_and_cache()
        if not fetch_result:
            return Result.fail(f"News fetch failed: {fetch_result.error}")

        articles = fetch_result.data

        # Summarize
        logger.info("🤖 Gemini se summarize kar raha hoon...")
        summary_result = summarize_news(articles, count=6)
        if not summary_result:
            return Result.fail(f"Summary failed: {summary_result.error}")

        summary = summary_result.data
        save_text(f"generated/daily_briefing_{datetime.now().strftime('%Y%m%d')}.txt", summary)

        # Top article se LinkedIn post
        if articles:
            logger.info("💼 LinkedIn post generate kar raha hoon...")
            li_result = generate_post_from_news(articles[0], "linkedin")
            if li_result:
                save_text(f"generated/linkedin_news_{datetime.now().strftime('%Y%m%d')}.txt", li_result.data)

            # Twitter 5 posts
            logger.info("🐦 Twitter posts generate kar raha hoon...")
            tw_result = generate_post_from_news(articles[0], "twitter_5")
            if tw_result:
                save_text(f"generated/twitter_news_{datetime.now().strftime('%Y%m%d')}.txt", tw_result.data)

        logger.info("✅ Daily briefing complete!")
        return Result.success(summary)

    def search_specific_topic(self, topic: str, platform: str = "linkedin") -> Result:
        """Specific topic ke baare mein news search karo aur post banao"""
        logger.info(f"🔍 Searching: {topic}")

        # Fetch all news
        fetch_result = self.fetch_and_cache()
        if not fetch_result:
            return Result.fail(fetch_result.error)

        articles = fetch_result.data

        # Topic se relevant articles filter karo
        topic_lower = topic.lower()
        relevant = [
            a for a in articles
            if topic_lower in a["title"].lower() or topic_lower in a["summary"].lower()
        ]

        if relevant:
            logger.info(f"✅ {len(relevant)} relevant articles mili")
            # Best article se post generate karo
            return generate_post_from_news(relevant[0], platform)
        else:
            logger.info("📝 RSS mein nahi mila — Gemini se generate kar raha hoon...")
            # Direct Gemini se generate karo
            dummy_article = {
                "title": topic,
                "source": "TechNova Research",
                "summary": f"Content about {topic} for AI learners",
                "link": ""
            }
            return generate_post_from_news(dummy_article, platform)


def load_from_cache(path: str) -> Optional[list]:
    """Cache file se load karo"""
    try:
        from utils import load_json
        data = load_json(path)
        return data if isinstance(data, list) else None
    except:
        return None


# Singleton instance
search_agent = SearchAgent()


if __name__ == "__main__":
    print("=" * 55)
    print("🔍 TechNova World — Search Agent Test")
    print("=" * 55)

    if not cfg.GEMINI_API_KEY:
        print("❌ config.py mein GEMINI_API_KEY set karo pehle!")
        import sys; sys.exit(1)

    print("\n1️⃣  AI news fetch kar raha hoon...")
    agent = SearchAgent()
    result = agent.fetch_and_cache(force=True)

    if result:
        articles = result.data
        print(f"✅ {len(articles)} articles fetched!\n")
        print("Top 3 headlines:")
        for a in articles[:3]:
            print(f"  📰 [{a['source']}] {a['title'][:80]}")

        print("\n2️⃣  Summarize kar raha hoon...")
        summary = summarize_news(articles[:4])
        if summary:
            print("\n" + summary.data[:600] + "...")
    else:
        print(f"❌ Fetch failed: {result.error}")
        print("Check karo: internet connection + RSS URLs accessible hain?")
