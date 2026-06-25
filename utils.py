"""
TechNova World — Core Utilities v2.0
Logging, retry logic, error handling, validation
"""

import os
import sys
import time
import json
import logging
import functools
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

# ── LOGGING SETUP ────────────────────────────────────────────
LOG_DIR  = Path("logs")
LOG_FILE = LOG_DIR / "automation.log"

def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger("TechNova")
    logger.setLevel(logging.DEBUG)

    # Console handler — coloured
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(ColorFormatter())

    # File handler — plain
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)
    return logger


class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG":    "\033[36m",   # cyan
        "INFO":     "\033[32m",   # green
        "WARNING":  "\033[33m",   # yellow
        "ERROR":    "\033[31m",   # red
        "CRITICAL": "\033[35m",   # magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname:<8}{self.RESET}"
        record.msg = f"{record.msg}"
        return super().format(record)

    def formatException(self, exc_info):
        return ""  # Suppress traceback in console


logger = setup_logging()


# ── RETRY DECORATOR ──────────────────────────────────────────
def retry(max_tries: int = 3, delay: float = 5.0, exceptions=(Exception,)):
    """
    Automatic retry decorator with exponential backoff.
    Usage: @retry(max_tries=3, delay=5)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_tries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    wait = delay * (2 ** (attempt - 1))   # exponential backoff
                    if attempt < max_tries:
                        logger.warning(
                            f"⚠️  {func.__name__} attempt {attempt}/{max_tries} failed: {e}. "
                            f"Retry in {wait:.0f}s..."
                        )
                        time.sleep(wait)
                    else:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_tries} attempts: {e}"
                        )
            raise last_error
        return wrapper
    return decorator


# ── RESULT WRAPPER ───────────────────────────────────────────
class Result:
    """Standard result object — success or error, no surprises."""
    def __init__(self, ok: bool, data: Any = None, error: str = ""):
        self.ok    = ok
        self.data  = data
        self.error = error

    @classmethod
    def success(cls, data=None):
        return cls(ok=True, data=data)

    @classmethod
    def fail(cls, error: str):
        logger.error(f"Result.fail: {error}")
        return cls(ok=False, error=error)

    def __bool__(self):
        return self.ok

    def __repr__(self):
        return f"Result(ok={self.ok}, data={str(self.data)[:60]}, error={self.error!r})"


# ── CONFIG VALIDATION ────────────────────────────────────────
def validate_config() -> dict:
    """
    config.py keys validate karo.
    Returns dict of what is set / missing.
    """
    try:
        import config as cfg
    except ImportError:
        logger.critical("config.py nahi mili! Project folder check karo.")
        sys.exit(1)

    status = {}

    checks = {
        "gemini":    (cfg.GEMINI_API_KEY,            "AIzaSy"),
        "linkedin":  (cfg.LINKEDIN_ACCESS_TOKEN,     "AQV"),
        "li_org":    (cfg.LINKEDIN_ORGANIZATION_ID,  ""),
        "tw_bearer": (cfg.TWITTER_BEARER_TOKEN,      "AAAAAA"),
    }

    for key, (value, prefix) in checks.items():
        if value and value != f"YOUR_{key.upper()}_HERE":
            status[key] = "✅ Set"
        else:
            status[key] = "❌ Missing"

    return status


def print_config_status():
    status = validate_config()
    print("\n🔧 Config Status:")
    labels = {
        "gemini":    "Gemini API Key   (required)",
        "linkedin":  "LinkedIn Token   (for auto-post)",
        "li_org":    "LinkedIn Org ID  (for auto-post)",
        "tw_bearer": "Twitter Bearer   (optional)",
    }
    for key, val in status.items():
        print(f"   {val}  {labels.get(key, key)}")
    print()
    return status


# ── FILE HELPERS ─────────────────────────────────────────────
def save_json(path: str, data: Any) -> bool:
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"save_json failed ({path}): {e}")
        return False


def load_json(path: str, default=None) -> Any:
    try:
        if Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"load_json failed ({path}): {e}")
    return default if default is not None else {}


def save_text(path: str, text: str) -> bool:
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return True
    except Exception as e:
        logger.error(f"save_text failed ({path}): {e}")
        return False


def load_text(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"load_text failed ({path}): {e}")
        return None


# ── QUEUE MANAGER ────────────────────────────────────────────
QUEUE_PATH = "queue/posts_queue.json"

class QueueManager:
    def __init__(self, path: str = QUEUE_PATH):
        self.path = path
        Path(path).parent.mkdir(exist_ok=True)

    def load(self) -> list:
        return load_json(self.path, default=[])

    def save(self, data: list) -> bool:
        return save_json(self.path, data)

    def add(self, platform: str, content: str, topic: str = "",
            image_path: str = "", schedule_time: str = "") -> bool:
        q = self.load()
        q.append({
            "id":            len(q) + 1,
            "platform":      platform,
            "content":       content,
            "topic":         topic,
            "image_path":    image_path,
            "schedule_time": schedule_time,
            "added_at":      datetime.now().isoformat(),
            "status":        "pending",
            "attempts":      0,
            "last_error":    "",
        })
        ok = self.save(q)
        if ok:
            logger.info(f"📝 Queue +1 [{platform}] {topic[:50]}")
        return ok

    def pending(self, platform: str = "") -> list:
        q = self.load()
        out = [x for x in q if x["status"] == "pending"]
        if platform:
            out = [x for x in out if x["platform"] == platform]
        return out

    def mark(self, item_id: int, status: str, error: str = ""):
        q = self.load()
        for item in q:
            if item.get("id") == item_id:
                item["status"]    = status
                item["last_error"] = error
                item["updated_at"] = datetime.now().isoformat()
                item["attempts"]   = item.get("attempts", 0) + 1
        self.save(q)

    def stats(self) -> dict:
        q = self.load()
        return {
            "total":   len(q),
            "pending": sum(1 for x in q if x["status"] == "pending"),
            "posted":  sum(1 for x in q if x["status"] == "posted"),
            "failed":  sum(1 for x in q if x["status"] == "failed"),
        }


queue_mgr = QueueManager()


# ── PROGRESS BAR ─────────────────────────────────────────────
def progress(current: int, total: int, label: str = ""):
    bar_len = 30
    filled  = int(bar_len * current / total) if total else 0
    bar     = "█" * filled + "░" * (bar_len - filled)
    pct     = int(100 * current / total) if total else 0
    print(f"\r  [{bar}] {pct:3d}%  {label[:40]}", end="", flush=True)
    if current >= total:
        print()
