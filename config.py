# ============================================================
# TechNova World — Config v4.0 (Deployment-Safe)
# ============================================================
# CRITICAL: Yeh file ab API keys ko ENVIRONMENT VARIABLES se
# leta hai, hardcoded values se NAHI. Isliye yeh GitHub pe
# safely push kar sakte ho — koi key leak nahi hogi.
#
# LOCAL TESTING (apne computer pe):
#   1. ".env.example" ko copy karke ".env" banao
#   2. ".env" mein apni real keys daalo
#   3. ".env" KABHI git mein commit mat karo (.gitignore mein hai already)
#
# GITHUB ACTIONS / RENDER (deployment):
#   Keys "Secrets" / "Environment Variables" panel mein daalo
#   (isi naam se: GEMINI_API_KEY, LINKEDIN_ACCESS_TOKEN, etc.)
#   Yeh file automatically wahan se pick kar lega.
# ============================================================

import os

# python-dotenv se local .env file load karo (agar exists)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv na ho toh bhi chalega — env vars seedhe OS se aa sakte hain


def _env(key: str, default: str = "") -> str:
    """Environment variable safely read karo."""
    return os.environ.get(key, default).strip()


# ── GEMINI API (Free — aistudio.google.com) ──────────────────
GEMINI_API_KEY = _env("GEMINI_API_KEY")

# ── OPENROUTER (Free fallback — openrouter.ai) ───────────────
OPENROUTER_API_KEY = _env("OPENROUTER_API_KEY")

# ── LINKEDIN ─────────────────────────────────────────────────
LINKEDIN_ACCESS_TOKEN    = _env("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_ORGANIZATION_ID = _env("LINKEDIN_ORGANIZATION_ID")

# ── TWITTER (optional) ───────────────────────────────────────
TWITTER_API_KEY              = _env("TWITTER_API_KEY")
TWITTER_API_SECRET           = _env("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN         = _env("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET  = _env("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN         = _env("TWITTER_BEARER_TOKEN")

# ── BRAND SETTINGS (no secrets — safe to hardcode) ───────────
BRAND_NAME         = _env("BRAND_NAME", "TechNova World")
WATERMARK_TEXT     = _env("WATERMARK_TEXT", "TechNova World")
WATERMARK_POSITION = _env("WATERMARK_POSITION", "bottom_right")

# ── SCHEDULE (IST 24h format) ─────────────────────────────────
LINKEDIN_POST_TIME = _env("LINKEDIN_POST_TIME", "21:00")
MEDIUM_POST_DAYS   = ["Tuesday", "Thursday"]
MEDIUM_POST_TIME   = _env("MEDIUM_POST_TIME", "18:00")
TWITTER_POST_TIMES = ["09:00", "12:00", "15:00", "18:00", "23:00"]

# ── AI CONTEXT ───────────────────────────────────────────────
AUDIENCE      = _env("AUDIENCE", "people learning AI, transitioning to IT/AI careers, AI enthusiasts")
CONTENT_STYLE = _env("CONTENT_STYLE", "Educational, simple, no jargon, actionable, beginner-friendly")

# ── RETRY / NETWORK SETTINGS ──────────────────────────────────
MAX_RETRIES = int(_env("MAX_RETRIES", "3"))
RETRY_DELAY = float(_env("RETRY_DELAY", "5"))
API_TIMEOUT = int(_env("API_TIMEOUT", "30"))


# ── STARTUP VALIDATION (helpful error messages) ───────────────
def _warn_if_missing():
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY (required for ALL AI features)")
    if not LINKEDIN_ACCESS_TOKEN:
        missing.append("LINKEDIN_ACCESS_TOKEN (required for auto-posting)")
    if not LINKEDIN_ORGANIZATION_ID:
        missing.append("LINKEDIN_ORGANIZATION_ID (required for auto-posting)")

    if missing and _env("SUPPRESS_CONFIG_WARNINGS") != "1":
        print("⚠️  Missing environment variables:")
        for m in missing:
            print(f"    - {m}")
        print("   Local: add to .env file")
        print("   GitHub Actions: add to repo Secrets")
        print("   Render: add to Environment Variables panel\n")


_warn_if_missing()
