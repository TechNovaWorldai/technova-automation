"""
TechNova World — Algorithm-Aware AI Generator v5.0
Har platform ke algorithm rules ko prompts mein inject karta hai
Auto quality-check + retry if score is low

v5.0: Ab ai_client.py ke through generate karta hai — Gemini 2.5
Flash/Pro + OpenRouter free fallback automatically handle ho jaata hai.
"""

import re
import time
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from utils       import logger, retry, Result, save_text
from ai_client    import generate_text
from algo_engine import (
    build_linkedin_prompt, build_twitter_prompt, build_medium_prompt,
    score_linkedin_post, score_twitter_post, score_medium_article,
    check_spam, check_value, print_score_report, QualityScore
)
import config as cfg

MIN_QUALITY_SCORE = 65          # Posts below this get auto-improved
MAX_IMPROVE_TRIES = 2           # Max re-generation attempts


# ── AI CALL (now routed through ai_client's fallback chain) ──

def _gemini(prompt: str, max_tokens: int = 1300) -> Optional[str]:
    """
    Naam purana rakha hai (_gemini) taaki baaki saara code unchanged
    chale, lekin ab yeh ai_client.generate_text() call karta hai —
    jo Gemini 2.5 Flash -> Gemini 2.5 Pro -> OpenRouter free models
    ka poora fallback chain try karta hai.
    """
    return generate_text(prompt, max_tokens=max_tokens)


# ── IMPROVE WEAK CONTENT ─────────────────────────────────────

def _improve_post(content: str, platform: str, score: QualityScore,
                  topic: str) -> Optional[str]:
    """Weak scoring post ko improve karo."""
    issues = "\n".join(score.failed + score.warnings)
    suggestions = "\n".join(score.suggestions)

    prompt = f"""This {platform} post scored {score.total}/100 — needs improvement.

CURRENT POST:
{content}

ISSUES FOUND:
{issues}

SUGGESTIONS:
{suggestions}

REWRITE the post fixing ALL issues above.
Brand: {cfg.BRAND_NAME}
Topic: {topic}
Keep the core insight but fix every flagged problem.
Return ONLY the improved post."""

    return _gemini(prompt)


# ── GENERATORS ───────────────────────────────────────────────

def generate_linkedin_post(topic: str,
                            auto_improve: bool = True,
                            show_score: bool = True) -> Optional[str]:
    """
    LinkedIn post generate karo — algo-aware + auto-improve.

    Flow:
      1. Algo-aware prompt → Gemini
      2. Quality score check
      3. Spam check
      4. If score < MIN_QUALITY_SCORE → improve (up to MAX_IMPROVE_TRIES)
      5. Return best version
    """
    logger.info(f"💼 LinkedIn post: {topic[:50]}")
    prompt = build_linkedin_prompt(topic, cfg.BRAND_NAME, cfg.AUDIENCE)

    content = _gemini(prompt)
    if not content:
        return None

    # Quality loop
    for attempt in range(MAX_IMPROVE_TRIES + 1):
        score = score_linkedin_post(content)

        if show_score:
            logger.info(f"  📊 Quality score: {score.total}/100 (Grade {score.grade})")

        spam = check_spam(content)
        if not spam["safe_to_post"]:
            logger.warning(f"  ⚠️  Spam detected: {spam['spam_signals']} — regenerating")
            content = _gemini(prompt)
            if not content:
                return None
            continue

        if score.total >= MIN_QUALITY_SCORE or not auto_improve or attempt >= MAX_IMPROVE_TRIES:
            break

        logger.info(f"  🔄 Score {score.total} < {MIN_QUALITY_SCORE} — improving (attempt {attempt+1})")
        improved = _improve_post(content, "LinkedIn", score, topic)
        if improved:
            content = improved

    if show_score:
        final_score = score_linkedin_post(content)
        print_score_report(final_score)

    return content


def generate_twitter_posts(topic: str, count: int = 5,
                            show_score: bool = False) -> List[str]:
    """Twitter posts generate karo — algo-aware (≤2 hashtags, replies-first)."""
    logger.info(f"🐦 Twitter {count} posts: {topic[:50]}")
    prompt = build_twitter_prompt(topic, cfg.BRAND_NAME, cfg.AUDIENCE, "single")

    raw = _gemini(prompt, max_tokens=900)
    if not raw:
        return []

    tweets = []
    for line in raw.strip().split('\n'):
        m = re.match(r'^(\d+)[.)]\s+(.+)$', line.strip())
        if m:
            tweet = m.group(2).strip().strip('"').strip("'")
            # Enforce 280 char limit
            if len(tweet) > 277:
                tweet = tweet[:274].rsplit(' ', 1)[0] + "..."
            if tweet:
                tweets.append(tweet)

    if not tweets:
        # Fallback parse
        tweets = [l.strip() for l in raw.split('\n')
                  if l.strip() and len(l.strip()) > 20 and len(l.strip()) <= 280]

    if show_score and tweets:
        for i, t in enumerate(tweets[:2], 1):
            s = score_twitter_post(t)
            logger.info(f"  Tweet {i}: {s.total}/100 (Grade {s.grade})")

    logger.info(f"✅ {len(tweets[:count])} tweets ready")
    return tweets[:count]


def generate_twitter_thread(topic: str, tweet_count: int = 8) -> List[str]:
    """Twitter thread generate karo — algo-aware."""
    logger.info(f"🧵 Thread ({tweet_count} tweets): {topic[:50]}")
    prompt = build_twitter_prompt(topic, cfg.BRAND_NAME, cfg.AUDIENCE, "thread")

    raw = _gemini(prompt, max_tokens=1200)
    if not raw:
        return []

    tweets = []
    for line in raw.strip().split('\n'):
        line = line.strip()
        # Match "1/8 text" pattern
        m = re.match(r'^\d+/\d+\s+(.+)$', line)
        if m:
            tweet = m.group(1).strip()
            if len(tweet) <= 280:
                tweets.append(tweet)

    logger.info(f"✅ Thread: {len(tweets)} tweets")
    return tweets


def generate_medium_article(topic: str, show_score: bool = True) -> Dict:
    """Medium article generate karo — algo-aware (read ratio optimised)."""
    logger.info(f"📝 Medium article: {topic[:50]}")
    prompt = build_medium_prompt(topic, cfg.BRAND_NAME, cfg.AUDIENCE)

    raw = _gemini(prompt, max_tokens=1800)
    if not raw:
        return {}

    result = {"title": "", "subtitle": "", "content": "", "tags": []}
    lines  = raw.strip().split('\n')
    in_body = False
    body_lines = []

    for line in lines:
        if line.startswith("TITLE:"):
            result["title"] = line.replace("TITLE:", "").strip()
        elif line.startswith("SUBTITLE:"):
            result["subtitle"] = line.replace("SUBTITLE:", "").strip()
        elif line.startswith("TAGS:"):
            result["tags"] = [t.strip() for t in
                               line.replace("TAGS:", "").split(",")][:5]
        elif line.strip() == "---":
            in_body = not in_body
        elif in_body:
            body_lines.append(line)

    result["content"] = "\n".join(body_lines).strip() or raw
    if not result["title"]:
        result["title"] = topic[:60]

    if show_score and result["content"]:
        score = score_medium_article(
            result["title"], result["content"], result.get("subtitle", "")
        )
        logger.info(f"  📊 Article score: {score.total}/100 (Grade {score.grade})")
        if score.total < MIN_QUALITY_SCORE:
            logger.info(f"  🔄 Improving article...")
            improved_raw = _gemini(
                prompt + f"\n\nIMPROVE: Previous attempt scored {score.total}/100.\n"
                         f"Focus on: {', '.join(score.failed[:3])}",
                max_tokens=1800
            )
            if improved_raw:
                # Re-parse
                raw = improved_raw
                body_lines, in_body = [], False
                for line in raw.split('\n'):
                    if line.startswith("TITLE:"):
                        result["title"] = line.replace("TITLE:", "").strip()
                    elif line.startswith("SUBTITLE:"):
                        result["subtitle"] = line.replace("SUBTITLE:", "").strip()
                    elif line.startswith("TAGS:"):
                        result["tags"] = [t.strip() for t in
                                           line.replace("TAGS:", "").split(",")][:5]
                    elif line.strip() == "---":
                        in_body = not in_body
                    elif in_body:
                        body_lines.append(line)
                result["content"] = "\n".join(body_lines).strip() or raw

    logger.info(f"✅ Article: '{result['title']}'")
    return result


def repurpose_article(article_text: str) -> Dict:
    """Article ko sab platforms ke liye repurpose — algo rules applied."""
    logger.info("🔁 Repurposing article...")

    if len(article_text.strip()) < 100:
        logger.error("❌ Article too short")
        return {}

    # Extract topic from article
    first_line = article_text.strip().split('\n')[0][:80]

    prompt = f"""Repurpose this {cfg.BRAND_NAME} article into all formats below.
Apply platform algorithm rules for each format.

LINKEDIN_POST:
[Hook ≤140 chars + insight + question + 5 hashtags. No external links. 900-1300 chars total.]

TWITTER_HOOKS:
Hook 1: [shocking stat — under 120 chars]
Hook 2: [question — under 120 chars]
Hook 3: [contrarian — under 120 chars]

TWITTER_THREAD:
[8 tweets numbered 1/8 to 8/8. Tweet 1 = viral hook with 🧵. Max 270 chars each. Max 2 hashtags total in tweet 1 only.]

CAROUSEL_TITLES:
Slide 1: [Cover — bold hook]
Slide 2-7: [One key point each]
Slide 8: [CTA — Follow TechNova World]

NEWSLETTER:
Subject: [Subject line]
Preview: [3-line teaser]

---
ARTICLE:
{article_text[:2500]}"""

    raw = _gemini(prompt, max_tokens=1800)
    if not raw:
        return {}

    sections = {}
    current_key, current_lines = None, []
    labels = {
        "LINKEDIN_POST":   "linkedin_post",
        "TWITTER_HOOKS":   "twitter_hooks",
        "TWITTER_THREAD":  "twitter_thread",
        "CAROUSEL_TITLES": "carousel_titles",
        "NEWSLETTER":      "newsletter",
    }

    for line in raw.split('\n'):
        matched = False
        for lbl, key in labels.items():
            if line.strip().startswith(lbl + ":") or line.strip() == lbl + ":":
                if current_key:
                    sections[current_key] = "\n".join(current_lines).strip()
                current_key  = key
                rest = line.replace(lbl + ":", "").strip()
                current_lines = [rest] if rest else []
                matched = True
                break
        if not matched and current_key:
            current_lines.append(line)

    if current_key:
        sections[current_key] = "\n".join(current_lines).strip()

    # Score LinkedIn post if present
    if "linkedin_post" in sections:
        score = score_linkedin_post(sections["linkedin_post"])
        logger.info(f"  LinkedIn repurpose score: {score.total}/100")

    logger.info(f"✅ Repurposed into {len(sections)} formats")
    return sections


def get_trending_topics(niche: str = "AI") -> Optional[str]:
    prompt = f"""List 8 trending {niche} topics RIGHT NOW for {cfg.BRAND_NAME}.
Audience: {cfg.AUDIENCE}

For each topic:
- **Topic** (specific — real product/model/event names)
- 🔥 Heat level (🔥 low / 🔥🔥 medium / 🔥🔥🔥 viral trending)
- Why trending: 1 sentence
- TechNova angle: best content hook
- Best platform: LinkedIn/Twitter/Medium
- Content type: Tutorial/News/Opinion/List

Only include topics where there is REAL audience demand. No filler."""
    return _gemini(prompt)


def generate_weekly_batch(topics: List[str]) -> Dict:
    """Poori week ka content generate karo — algo-optimised each piece."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    all_content = {}
    Path("generated").mkdir(exist_ok=True)

    for i, topic in enumerate(topics[:5]):
        day = days[i]
        logger.info(f"\n📅 {day}: '{topic}'")
        day_content = {}

        # LinkedIn
        li = generate_linkedin_post(topic, auto_improve=True, show_score=False)
        if li:
            day_content["linkedin"] = li
            save_text(f"generated/linkedin_{day.lower()}.txt", li)
            s = score_linkedin_post(li)
            logger.info(f"  ✅ LinkedIn — {s.total}/100 (Grade {s.grade})")

        # Twitter 5 posts
        tweets = generate_twitter_posts(topic, 5)
        if tweets:
            day_content["twitter"] = tweets
            save_text(f"generated/twitter_{day.lower()}.txt",
                      "\n\n---\n\n".join(tweets))
            logger.info(f"  ✅ Twitter — {len(tweets)} posts")

        # Medium on Tue + Thu
        if day in ["Tuesday", "Thursday"]:
            article = generate_medium_article(topic, show_score=False)
            if article:
                day_content["medium"] = article
                content = (f"TITLE: {article.get('title','')}\n"
                           f"SUBTITLE: {article.get('subtitle','')}\n\n"
                           f"{article.get('content','')}\n\n"
                           f"TAGS: {', '.join(article.get('tags', []))}")
                save_text(f"generated/medium_{day.lower()}.txt", content)
                logger.info(f"  ✅ Medium article saved")

        all_content[day] = day_content
        time.sleep(2)   # rate limit protection

    logger.info("\n✅ Weekly batch complete! Check generated/ folder.")
    return all_content
