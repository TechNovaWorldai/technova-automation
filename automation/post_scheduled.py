"""
TechNova World — Scheduled Post Runner (non-interactive)

Designed to be invoked by a GitHub Actions cron job (Mon–Fri, 9:30 PM IST).
Picks the next pending item from the post queue, validates its quality and
spam score, then publishes it to LinkedIn.  Exits with code 0 on success
or empty queue, and code 1 on any fatal error.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils           import logger, queue_mgr
from linkedin_poster import post_to_linkedin, check_linkedin_connection
from algo_engine     import score_linkedin_post, check_spam
import config as cfg


def main():
    logger.info("=" * 50)
    logger.info(f"🤖 Scheduled run started: {datetime.now().isoformat()}")
    logger.info("=" * 50)

    # Check required secrets
    if not cfg.GEMINI_API_KEY:
        logger.error("❌ GEMINI_API_KEY missing — GitHub Secrets mein daalo")
        sys.exit(1)

    if not cfg.LINKEDIN_ACCESS_TOKEN:
        logger.error("❌ LINKEDIN_ACCESS_TOKEN missing — GitHub Secrets mein daalo")
        sys.exit(1)

    # Connection check — informational only, 403 pe exit NAHI karta
    check_linkedin_connection()

    # Queue check
    pending = queue_mgr.pending("linkedin")
    if not pending:
        logger.warning("⚠️  Queue empty — kuch post nahi hai aaj.")
        logger.warning("   weekly-batch workflow chalao content generate karne ke liye.")
        sys.exit(0)

    item    = pending[0]
    content = item["content"]
    logger.info(f"📋 Post: {item.get('topic', 'untitled')[:60]}")

    # Safety checks
    spam = check_spam(content)
    if not spam["safe_to_post"]:
        logger.error(f"🚨 Spam detected — skipping: {spam['spam_signals']}")
        queue_mgr.mark(item["id"], "failed", "Spam detected")
        sys.exit(1)

    quality = score_linkedin_post(content)
    logger.info(f"📊 Quality: {quality.total}/100 (Grade {quality.grade})")

    if quality.total < 40:
        logger.error(f"❌ Quality too low ({quality.total}) — skipping")
        queue_mgr.mark(item["id"], "failed", f"Quality too low: {quality.total}")
        sys.exit(1)

    # Post it
    result = post_to_linkedin(content)

    if result:
        queue_mgr.mark(item["id"], "posted")
        target = result.data.get("posted_to", "unknown")
        logger.info(f"✅ Posted to {target}! ID: {result.data.get('post_id')}")
        if result.data.get("note"):
            logger.warning(f"ℹ️  {result.data['note']}")
    else:
        queue_mgr.mark(item["id"], "failed", result.error)
        logger.error(f"❌ Failed: {result.error}")
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("✅ Done!")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
