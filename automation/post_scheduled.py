"""
TechNova World — Scheduled Post Runner (non-interactive)
GitHub Actions ya Render cron job se call hota hai.
Koi input() nahi — fully automated.

Flow:
  1. Queue se next pending LinkedIn post uthao
  2. Algo score + spam check karo
  3. Post karo (ya skip + log karo agar fail ho)
  4. Queue update karo
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils           import logger, queue_mgr
from linkedin_poster import post_to_linkedin, check_linkedin_connection
from algo_engine      import score_linkedin_post, check_spam
import config as cfg


def main():
    logger.info("=" * 50)
    logger.info(f"🤖 Scheduled run started: {datetime.now().isoformat()}")
    logger.info("=" * 50)

    # 1. Pre-flight checks
    if not cfg.GEMINI_API_KEY:
        logger.error("❌ GEMINI_API_KEY missing — check GitHub Secrets")
        sys.exit(1)

    if not check_linkedin_connection():
        logger.error("❌ LinkedIn connection failed — check token validity (expires every 60 days)")
        sys.exit(1)

    # 2. Get next pending LinkedIn post
    pending = queue_mgr.pending("linkedin")
    if not pending:
        logger.warning("⚠️  Queue empty — nothing to post today.")
        logger.warning("   Run weekly_batch.py first, or add posts manually.")
        sys.exit(0)   # not an error — just nothing to do

    item = pending[0]
    content = item["content"]
    logger.info(f"📋 Next post: {item.get('topic', 'untitled')[:60]}")

    # 3. Safety checks before posting
    spam_check = check_spam(content)
    if not spam_check["safe_to_post"]:
        logger.error(f"🚨 Spam detected — skipping post: {spam_check['spam_signals']}")
        queue_mgr.mark(item["id"], "failed", f"Spam check failed: {spam_check['spam_signals']}")
        sys.exit(1)

    quality = score_linkedin_post(content)
    logger.info(f"📊 Quality score: {quality.total}/100 (Grade {quality.grade})")

    if quality.total < 40:
        logger.error(f"❌ Quality too low ({quality.total}/100) — skipping post")
        queue_mgr.mark(item["id"], "failed", f"Quality score too low: {quality.total}")
        sys.exit(1)

    # 4. Post it
    result = post_to_linkedin(content, item.get("image_path") or None)

    if result:
        queue_mgr.mark(item["id"], "posted")
        logger.info(f"✅ Posted successfully! ID: {result.data.get('post_id')}")
    else:
        queue_mgr.mark(item["id"], "failed", result.error)
        logger.error(f"❌ Post failed: {result.error}")
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("✅ Scheduled run complete")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
