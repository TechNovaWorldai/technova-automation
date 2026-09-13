# ============================================================
# TechNova World — Config v4.0 (Deployment-Safe)
# ============================================================
# IMPORTANT: This file reads ALL secrets from environment variables,
# NOT from hardcoded values.  It is therefore safe to commit to GitHub
# without leaking any credentials.
#
# LOCAL DEVELOPMENT:
#   1. Copy ".env.example" to ".env"
#   2. Fill in your real API keys in ".env"
#   3. Never commit ".env" to Git (".gitignore" already excludes it)
#
# GITHUB ACTIONS / RENDER (production):
#   Set keys in the repository Secrets panel or Render’s
#   Environment Variables panel using the exact names below
#   (e.g. GEMINI_API_KEY, LINKEDIN_ACCESS_TOKEN).
#   This file will automatically pick them up at runtime.
# ============================================================

import os

# Load variables from a local .env file if one exists (development only).
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; env vars can also be set directly in the OS


def _env(key: str, default: str = "") -> str:
    """Read an environment variable, stripping surrounding whitespace."""
    return os.environ.get(key, default).strip()


# ── GEMINI API (Free — aistudio.google.com) ──────────────────
GEMINI_API_KEY = _env("GEMINI_API_KEY")

# ── OPENROUTER (Free fallback — openrouter.ai) ───────────────
OPENROUTER_API_KEY = _env("OPENROUTER_API_KEY")

# ── LINKEDIN ─────────────────────────────────────────────────
LINKEDIN_ACCESS_TOKEN    = _env("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_ORGANIZATION_ID = _env("LINKEDIN_ORGANIZATION_ID")

# Personal profile fallback (jab tak company page approval na mile)
# LINKEDIN_PERSON_URN auto-fetch hoga token se — manually set karna zaroori nahi
LINKEDIN_PERSON_URN           = _env("LINKEDIN_PERSON_URN")
LINKEDIN_FALLBACK_TO_PERSONAL = _env("LINKEDIN_FALLBACK_TO_PERSONAL", "true").lower() == "true"

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
LINKEDIN_POST_TIME = _env("LINKEDIN_POST_TIME", "09:00")
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
    if not LINKEDIN_ORGANIZATION_ID and not LINKEDIN_PERSON_URN:
        missing.append("LINKEDIN_ORGANIZATION_ID ya LINKEDIN_PERSON_URN (ek zaroori hai)")

    if missing and _env("SUPPRESS_CONFIG_WARNINGS") != "1":
        print("[WARNING] Missing environment variables:")
        for m in missing:
            print(f"    - {m}")
        print("   Local: add to .env file")
        print("   GitHub Actions: add to repo Secrets")
        print("   Render: add to Environment Variables panel\n")


_warn_if_missing()
