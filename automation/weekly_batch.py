"""
TechNova World — Weekly Batch Generator (non-interactive)
GitHub Actions Sunday cron se call hota hai.
Koi input() nahi — fully automated.

Flow:
  1. TOPICS_INPUT env var se topics lo (ya trending auto-fetch karo)
  2. 5 din ka content generate karo (algo-aware + brand voice)
  3. LinkedIn posts ko queue mein daal do (Mon-Fri auto-post hoga)
  4. Twitter/Medium content generated/ mein save karo (manual use ke liye)
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils         import logger, queue_mgr, save_text
from ai_generator   import generate_linkedin_post, generate_twitter_posts, generate_medium_article
from algo_engine    import score_linkedin_post
import config as cfg


def get_topics() -> list:
    """Topics environment variable se lo, ya trending fetch karo."""
    raw = os.environ.get("TOPICS_INPUT", "").strip()
    if raw:
        topics = [t.strip() for t in raw.split(",") if t.strip()]
        if len(topics) >= 5:
            logger.info(f"📋 Using provided topics: {topics[:5]}")
            return topics[:5]

    logger.info("🔥 No topics provided — fetching trending AI topics...")
    from ai_generator import get_trending_topics as fetch_trending
    trending_text = fetch_trending()

    if not trending_text:
        logger.warning("⚠️  Trending fetch failed — using fallback generic topics")
        return [
            "5 AI tools that save hours every week",
            "How to start learning AI in 2026",
            "Common mistakes beginners make with ChatGPT",
            "AI tools comparison: free vs paid",
            "What AI skills are companies hiring for now",
        ]

    # Extract topic-like lines (very simple heuristic — good enough as fallback)
    lines = [l.strip("-•* ").strip() for l in trending_text.split("\n")
              if l.strip() and len(l.strip()) > 15 and len(l.strip()) < 100]
    topics = lines[:5] if len(lines) >= 5 else lines + ["AI productivity tips"] * (5 - len(lines))
    logger.info(f"📋 Auto-picked topics: {topics}")
    return topics[:5]


def main():
    logger.info("=" * 50)
    logger.info(f"🤖 Weekly batch generation started: {datetime.now().isoformat()}")
    logger.info("=" * 50)

    if not cfg.GEMINI_API_KEY:
        logger.error("❌ GEMINI_API_KEY missing — check GitHub Secrets")
        sys.exit(1)

    Path("generated").mkdir(exist_ok=True)
    days   = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    topics = get_topics()

    success_count = 0

    for day, topic in zip(days, topics):
        logger.info(f"\n📅 {day}: '{topic}'")

        # LinkedIn — generate + queue for auto-posting
        li_content = generate_linkedin_post(topic, auto_improve=True, show_score=False)
        if li_content:
            score = score_linkedin_post(li_content)
            queue_mgr.add("linkedin", li_content, topic)
            save_text(f"generated/linkedin_{day.lower()}.txt", li_content)
            logger.info(f"  ✅ LinkedIn queued — score {score.total}/100")
            success_count += 1
        else:
            logger.error(f"  ❌ LinkedIn generation failed for {day}")

        # Twitter — generate + save (manual posting via Buffer)
        tweets = generate_twitter_posts(topic, 5)
        if tweets:
            save_text(f"generated/twitter_{day.lower()}.txt", "\n\n---\n\n".join(tweets))
            logger.info(f"  ✅ Twitter posts saved ({len(tweets)})")

        # Medium — Tuesday + Thursday only
        if day in cfg.MEDIUM_POST_DAYS:
            article = generate_medium_article(topic, show_score=False)
            if article:
                content = (f"TITLE: {article.get('title','')}\n"
                           f"SUBTITLE: {article.get('subtitle','')}\n\n"
                           f"{article.get('content','')}\n\n"
                           f"TAGS: {', '.join(article.get('tags', []))}")
                save_text(f"generated/medium_{day.lower()}.txt", content)
                logger.info(f"  ✅ Medium article saved")

    logger.info("\n" + "=" * 50)
    logger.info(f"✅ Weekly batch complete: {success_count}/5 LinkedIn posts queued")
    logger.info("   Mon-Fri 9PM IST workflow will auto-post these from queue.")
    logger.info("   Twitter/Medium content saved in generated/ — post manually via Buffer/Medium.")
    logger.info("=" * 50)

    if success_count == 0:
        sys.exit(1)   # signal failure to GitHub Actions


if __name__ == "__main__":
    main()
