"""
TechNova World — Web Dashboard v5.0
Flask app: browser se input do, output dekho, queue manage karo.
Render.com pe web service ke roop mein deploy hota hai.

Routes:
  /                  Dashboard home — connection status, stats
  /generate          Single/batch topic generation UI
  /queue             View/manage scheduled posts
  /research          Research agent with sources
  /api/*             JSON endpoints (AJAX, no page reload)
"""

import os
import sys
import json
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for

sys.path.insert(0, str(Path(__file__).parent))

from utils import logger, queue_mgr, validate_config
from ai_client import generate, check_all_providers
from ai_generator import (
    generate_linkedin_post, generate_twitter_posts, generate_twitter_thread,
    generate_medium_article, repurpose_article, get_trending_topics,
)
from algo_engine import (
    score_linkedin_post, score_twitter_post, score_medium_article,
    check_spam, check_value,
)
from brand_voice import check_voice_compliance, load_voice
from research_agent import research_topic, get_news_with_sources
from linkedin_poster import post_to_linkedin, check_linkedin_connection
from watermark import add_watermark
import config as cfg

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "technova-dev-key-change-in-prod")

# In-memory job tracker for async generation (simple, no Redis needed)
_jobs = {}
_jobs_lock = threading.Lock()


# ════════════════════════════════════════════════════════════
# HOME / DASHBOARD
# ════════════════════════════════════════════════════════════

@app.route("/")
def home():
    stats = queue_mgr.stats()
    return render_template("dashboard.html", stats=stats, brand=cfg.BRAND_NAME)


@app.route("/api/status")
def api_status():
    """Connection health for all providers — used by dashboard status panel."""
    config_status = validate_config()
    queue_stats = queue_mgr.stats()

    li_connected = False
    try:
        li_connected = bool(cfg.LINKEDIN_ACCESS_TOKEN and cfg.LINKEDIN_ORGANIZATION_ID)
    except Exception:
        pass

    return jsonify({
        "config": config_status,
        "queue": queue_stats,
        "linkedin_configured": li_connected,
        "gemini_configured": bool(cfg.GEMINI_API_KEY),
        "openrouter_configured": bool(cfg.OPENROUTER_API_KEY),
        "brand": cfg.BRAND_NAME,
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/check-providers")
def api_check_providers():
    """Live ping to AI providers — slower, only call on-demand (button click)."""
    try:
        status = check_all_providers()
        return jsonify({"ok": True, "providers": status})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ════════════════════════════════════════════════════════════
# GENERATE — single topic, any platform
# ════════════════════════════════════════════════════════════

@app.route("/generate")
def generate_page():
    return render_template("generate.html", brand=cfg.BRAND_NAME)


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """
    Single topic -> single platform content.
    Body: { "platform": "linkedin|twitter|twitter_thread|medium", "topic": "..." }
    """
    data = request.get_json(force=True) or {}
    platform = data.get("platform", "linkedin")
    topic = (data.get("topic") or "").strip()

    if not topic:
        return jsonify({"ok": False, "error": "Topic is required"}), 400

    try:
        if platform == "linkedin":
            content = generate_linkedin_post(topic, auto_improve=True, show_score=False)
            if not content:
                return jsonify({"ok": False, "error": "Generation failed (all AI providers exhausted)"}), 502
            score = score_linkedin_post(content)
            spam = check_spam(content)
            voice = check_voice_compliance(content)
            return jsonify({
                "ok": True, "platform": platform, "content": content,
                "score": {"total": score.total, "grade": score.grade,
                          "passed": score.passed, "failed": score.failed,
                          "warnings": score.warnings, "suggestions": score.suggestions},
                "spam_safe": spam["safe_to_post"],
                "voice_score": voice["voice_score"],
                "voice_verdict": voice["verdict"],
            })

        elif platform == "twitter":
            tweets = generate_twitter_posts(topic, 5)
            scored = [{"text": t, "score": score_twitter_post(t).total} for t in tweets]
            return jsonify({"ok": True, "platform": platform, "tweets": scored})

        elif platform == "twitter_thread":
            thread = generate_twitter_thread(topic, 8)
            return jsonify({"ok": True, "platform": platform, "thread": thread})

        elif platform == "medium":
            article = generate_medium_article(topic, show_score=False)
            if not article:
                return jsonify({"ok": False, "error": "Generation failed"}), 502
            score = score_medium_article(
                article.get("title", ""), article.get("content", ""),
                article.get("subtitle", "")
            )
            return jsonify({
                "ok": True, "platform": platform, "article": article,
                "score": {"total": score.total, "grade": score.grade,
                          "failed": score.failed, "suggestions": score.suggestions},
            })
        else:
            return jsonify({"ok": False, "error": f"Unknown platform: {platform}"}), 400

    except Exception as e:
        logger.error(f"Generation error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/repurpose", methods=["POST"])
def api_repurpose():
    """Article text -> all platform formats."""
    data = request.get_json(force=True) or {}
    article = (data.get("article") or "").strip()

    if len(article) < 100:
        return jsonify({"ok": False, "error": "Article too short (min 100 chars)"}), 400

    try:
        result = repurpose_article(article)
        if not result:
            return jsonify({"ok": False, "error": "Repurpose failed"}), 502
        return jsonify({"ok": True, "formats": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ════════════════════════════════════════════════════════════
# BATCH MODE — "Sunday 5 topics -> 5 different posts"
# ════════════════════════════════════════════════════════════

@app.route("/batch")
def batch_page():
    return render_template("batch.html", brand=cfg.BRAND_NAME)


@app.route("/api/batch/start", methods=["POST"])
def api_batch_start():
    """
    Start a background batch job: list of topics -> 5 separate posts.
    Each topic gets its OWN platform + content (not all same).
    Body: { "items": [{"day":"Monday","topic":"...","platform":"linkedin"}, ...] }
    Returns job_id immediately — poll /api/batch/status/<job_id> for progress.
    """
    data = request.get_json(force=True) or {}
    items = data.get("items", [])

    if not items or len(items) == 0:
        return jsonify({"ok": False, "error": "No topics provided"}), 400

    job_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with _jobs_lock:
        _jobs[job_id] = {
            "status": "running", "total": len(items), "done": 0,
            "results": [], "started_at": datetime.now().isoformat(),
        }

    def run_batch():
        for item in items:
            day = item.get("day", "")
            topic = item.get("topic", "").strip()
            platform = item.get("platform", "linkedin")
            if not topic:
                continue
            try:
                if platform == "linkedin":
                    content = generate_linkedin_post(topic, auto_improve=True, show_score=False)
                    score = score_linkedin_post(content).total if content else 0
                elif platform == "twitter":
                    tweets = generate_twitter_posts(topic, 5)
                    content = "\n\n---\n\n".join(tweets)
                    score = None
                elif platform == "medium":
                    article = generate_medium_article(topic, show_score=False)
                    content = article.get("content", "") if article else None
                    score = None
                else:
                    content, score = None, None

                with _jobs_lock:
                    _jobs[job_id]["results"].append({
                        "day": day, "topic": topic, "platform": platform,
                        "content": content, "score": score,
                        "ok": content is not None,
                    })
                    _jobs[job_id]["done"] += 1
            except Exception as e:
                with _jobs_lock:
                    _jobs[job_id]["results"].append({
                        "day": day, "topic": topic, "platform": platform,
                        "content": None, "ok": False, "error": str(e),
                    })
                    _jobs[job_id]["done"] += 1

        with _jobs_lock:
            _jobs[job_id]["status"] = "complete"
            _jobs[job_id]["finished_at"] = datetime.now().isoformat()

    threading.Thread(target=run_batch, daemon=True).start()
    return jsonify({"ok": True, "job_id": job_id})


@app.route("/api/batch/status/<job_id>")
def api_batch_status(job_id):
    """Poll this to see batch progress + results as they complete."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "Job not found"}), 404
    return jsonify({"ok": True, **job})


@app.route("/api/batch/queue", methods=["POST"])
def api_batch_queue_all():
    """Add all completed batch results to the posting queue."""
    data = request.get_json(force=True) or {}
    job_id = data.get("job_id", "")
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "Job not found"}), 404

    queued = 0
    for r in job.get("results", []):
        if r.get("ok") and r.get("content"):
            queue_mgr.add(r["platform"], r["content"], r["topic"])
            queued += 1
    return jsonify({"ok": True, "queued": queued})


# ════════════════════════════════════════════════════════════
# QUEUE — view/manage scheduled posts
# ════════════════════════════════════════════════════════════

@app.route("/queue")
def queue_page():
    return render_template("queue.html", brand=cfg.BRAND_NAME)


@app.route("/api/queue")
def api_queue_list():
    items = queue_mgr.load()
    stats = queue_mgr.stats()
    return jsonify({"ok": True, "items": items, "stats": stats})


@app.route("/api/queue/add", methods=["POST"])
def api_queue_add():
    data = request.get_json(force=True) or {}
    platform = data.get("platform", "linkedin")
    content = (data.get("content") or "").strip()
    topic = data.get("topic", "")

    if not content:
        return jsonify({"ok": False, "error": "Content required"}), 400

    spam = check_spam(content)
    if not spam["safe_to_post"]:
        return jsonify({"ok": False, "error": f"Spam detected: {spam['spam_signals']}"}), 400

    queue_mgr.add(platform, content, topic)
    return jsonify({"ok": True})


@app.route("/api/queue/post-now", methods=["POST"])
def api_queue_post_now():
    """Manually trigger posting the next pending LinkedIn item right now."""
    pending = queue_mgr.pending("linkedin")
    if not pending:
        return jsonify({"ok": False, "error": "Queue is empty"}), 400

    item = pending[0]
    result = post_to_linkedin(item["content"])
    if result:
        queue_mgr.mark(item["id"], "posted")
        return jsonify({"ok": True, "post_id": result.data.get("post_id")})
    else:
        queue_mgr.mark(item["id"], "failed", result.error)
        return jsonify({"ok": False, "error": result.error}), 502


@app.route("/api/queue/clear", methods=["POST"])
def api_queue_clear():
    queue_mgr.save([])
    return jsonify({"ok": True})


@app.route("/api/queue/export-buffer")
def api_queue_export_buffer():
    """
    Export pending Twitter queue items as a Buffer-compatible bulk-upload CSV.
    Buffer's bulk upload expects: Text, Image URL, Tags, Posting Time columns.
    Download this file, then in Buffer: channel settings -> Bulk Upload ->
    upload this CSV. (Buffer free plan: up to 100 posts per import.)
    """
    import csv
    import io
    from flask import Response

    platform = request.args.get("platform", "twitter")
    items = [i for i in queue_mgr.load()
             if i["platform"] == platform and i["status"] == "pending"]

    if not items:
        return jsonify({"ok": False, "error": f"No pending {platform} posts in queue"}), 404

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Text", "Image URL", "Tags", "Posting Time"])
    for item in items:
        writer.writerow([item["content"], "", "", ""])  # times set manually in Buffer's review screen

    csv_data = buf.getvalue()
    filename = f"technova_{platform}_buffer_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ════════════════════════════════════════════════════════════
# RESEARCH AGENT — news with sources
# ════════════════════════════════════════════════════════════

@app.route("/research")
def research_page():
    return render_template("research.html", brand=cfg.BRAND_NAME)


@app.route("/api/research", methods=["POST"])
def api_research():
    """
    Topic ke baare mein research karo — sources ke saath.
    Body: { "topic": "..." }
    """
    data = request.get_json(force=True) or {}
    topic = (data.get("topic") or "").strip()

    if not topic:
        return jsonify({"ok": False, "error": "Topic required"}), 400

    try:
        result = research_topic(topic)
        if not result:
            return jsonify({"ok": False, "error": result.error}), 502
        return jsonify({"ok": True, **result.data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/news-with-sources")
def api_news_sources():
    """Latest AI news with source attribution."""
    try:
        result = get_news_with_sources()
        if not result:
            return jsonify({"ok": False, "error": result.error}), 502
        return jsonify({"ok": True, "items": result.data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ════════════════════════════════════════════════════════════
# TRENDING TOPICS (for batch mode suggestions)
# ════════════════════════════════════════════════════════════

@app.route("/api/trending")
def api_trending():
    try:
        text = get_trending_topics()
        if not text:
            return jsonify({"ok": False, "error": "Could not fetch trending topics"}), 502
        return jsonify({"ok": True, "trending": text})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ════════════════════════════════════════════════════════════
# HEALTH CHECK (Render needs this)
# ════════════════════════════════════════════════════════════

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
