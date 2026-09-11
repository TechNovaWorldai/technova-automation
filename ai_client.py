"""
TechNova World — Unified AI Client v5.0

Single entry point for all AI text-generation calls in the application.

Fallback chain (tried in order):
  1. Gemini 2.5 Flash    — fast, free-tier primary model
  2. Gemini 2.5 Pro      — higher quality, same API key, used if Flash fails
  3. OpenRouter free pool — different provider entirely; survives Google outages

Background:
  Gemini 1.5 models were shut down by Google (404 errors), which is exactly
  why the old automation broke. Models get deprecated without warning. A
  two-provider fallback chain means one vendor’s decision cannot break the
  entire pipeline.
"""

import time
import requests
from typing import Optional, List, Dict
from utils import logger, retry, Result
import config as cfg


# ════════════════════════════════════════════════════════════
# MODEL ENDPOINTS
# ════════════════════════════════════════════════════════════

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"

# Order matters — tried top to bottom
GEMINI_MODELS = [
    "gemini-2.5-flash",       # primary — fast + free tier
    "gemini-2.5-pro",          # fallback 1 — higher quality, same key
]

# OpenRouter free models — tried top to bottom if Gemini totally fails
OPENROUTER_FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-chat:free",
    "google/gemini-2.0-flash-exp:free",
    "openrouter/free",          # auto-router — always-on safety net
]


# ════════════════════════════════════════════════════════════
# PROVIDER: GEMINI
# ════════════════════════════════════════════════════════════

def _call_gemini_model(model: str, prompt: str, max_tokens: int) -> str:
    """Make a single synchronous request to a Gemini model.

    Raises a typed exception on known HTTP error codes so the caller
    can decide whether to fall through to the next model:
      LookupError    — model not found / deprecated (HTTP 404)
      IOError        — rate limited (HTTP 429)
      PermissionError — API key invalid or expired (HTTP 403)
      ValueError     — bad request or safety filter triggered (HTTP 400)
    """
    if not cfg.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")

    url = f"{GEMINI_BASE}/{model}:generateContent?key={cfg.GEMINI_API_KEY}"

    generation_config = {
        "maxOutputTokens": max_tokens,
        "temperature": 0.8,
        "topP": 0.94,
    }
    # Gemini 2.5 models spend part of maxOutputTokens on internal "thinking"
    # before the visible answer, which was silently truncating our posts
    # (finishReason=MAX_TOKENS was never checked, so a cut-off post looked
    # like a success). Flash supports disabling thinking entirely; Pro
    # requires a small minimum budget, so we just give it a token cushion.
    if "flash" in model:
        generation_config["thinkingConfig"] = {"thinkingBudget": 0}

    r = requests.post(
        url,
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        },
        timeout=cfg.API_TIMEOUT,
    )

    if r.status_code == 404:
        raise LookupError(f"Model '{model}' not found/deprecated (404)")
    if r.status_code == 429:
        raise IOError(f"Rate limit hit on {model}")
    if r.status_code == 403:
        raise PermissionError(f"API key invalid/expired for {model}")
    if r.status_code == 400:
        msg = r.json().get("error", {}).get("message", "Bad request")
        raise ValueError(f"{model} 400 error: {msg}")
    r.raise_for_status()

    data = r.json()
    cands = data.get("candidates", [])
    if not cands:
        raise ValueError(f"{model} returned empty candidates")

    finish = cands[0].get("finishReason", "STOP")
    if finish == "SAFETY":
        raise ValueError(f"{model} safety filter triggered")
    if finish == "MAX_TOKENS":
        raise IOError(
            f"{model} hit MAX_TOKENS — response was truncated "
            f"(thinking tokens likely ate the budget)"
        )

    parts = cands[0].get("content", {}).get("parts", [])
    text_parts = [p["text"] for p in parts if "text" in p and not p.get("thought")]
    if not text_parts:
        raise ValueError(f"{model} returned no usable text parts")

    return "".join(text_parts)


# ════════════════════════════════════════════════════════════
# PROVIDER: OPENROUTER
# ════════════════════════════════════════════════════════════

def _call_openrouter_model(model: str, prompt: str, max_tokens: int) -> str:
    """Make a single synchronous request to an OpenRouter model.

    Raises IOError on rate limits and PermissionError on auth failures,
    matching the same exception contract as ``_call_gemini_model``.
    """
    if not cfg.OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set")

    r = requests.post(
        OPENROUTER_BASE,
        headers={
            "Authorization": f"Bearer {cfg.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/technova-world",
            "X-Title": "TechNova World Automation",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.8,
        },
        timeout=cfg.API_TIMEOUT,
    )

    if r.status_code == 429:
        raise IOError(f"Rate limit hit on OpenRouter {model}")
    if r.status_code == 401:
        raise PermissionError("OpenRouter API key invalid")
    r.raise_for_status()

    data = r.json()
    choices = data.get("choices", [])
    if not choices:
        raise ValueError(f"OpenRouter {model} returned no choices")

    return choices[0]["message"]["content"]


# ════════════════════════════════════════════════════════════
# UNIFIED CALL — TRIES EVERYTHING IN ORDER
# ════════════════════════════════════════════════════════════

def generate(prompt: str, max_tokens: int = 1300,
             prefer_quality: bool = False) -> Result:
    """
    Generate text using the full provider fallback chain.

    Tries every Gemini model first, then falls through to OpenRouter
    free models if all Gemini calls fail. Returns a ``Result`` so
    callers never need to catch exceptions.

    Args:
        prompt:          The user / system prompt to send.
        max_tokens:      Maximum number of output tokens.
        prefer_quality:  If True, tries Gemini 2.5 Pro first (slower, better
                         quality); otherwise Flash is tried first.

    Returns:
        Result with ``.data = {"text": str, "model_used": str}`` on success,
        or ``Result.fail(error)`` if every provider is exhausted.
    """
    attempts_log = []

    gemini_order = list(GEMINI_MODELS)
    if prefer_quality:
        gemini_order = gemini_order[::-1]   # Pro first

    # ── Try Gemini models in order ──────────────────────────
    for model in gemini_order:
        try:
            text = _call_gemini_model(model, prompt, max_tokens)
            logger.info(f"✅ Generated via Gemini ({model})")
            return Result.success({"text": text, "model_used": f"gemini/{model}"})
        except (IOError,) as e:
            attempts_log.append(f"{model}: rate limited")
            logger.warning(f"⏳ {model} rate limited — trying next model")
            time.sleep(1)
            continue
        except (LookupError, PermissionError, ValueError) as e:
            attempts_log.append(f"{model}: {e}")
            logger.warning(f"⚠️  {model} failed ({e}) — trying next model")
            continue
        except Exception as e:
            attempts_log.append(f"{model}: {e}")
            logger.warning(f"⚠️  {model} unexpected error ({e}) — trying next")
            continue

    # ── All Gemini failed — try OpenRouter free models ──────
    if cfg.OPENROUTER_API_KEY:
        logger.info("🔄 All Gemini models failed — falling back to OpenRouter")
        for model in OPENROUTER_FREE_MODELS:
            try:
                text = _call_openrouter_model(model, prompt, max_tokens)
                logger.info(f"✅ Generated via OpenRouter ({model})")
                return Result.success({"text": text, "model_used": f"openrouter/{model}"})
            except (IOError,) as e:
                attempts_log.append(f"{model}: rate limited")
                time.sleep(1)
                continue
            except Exception as e:
                attempts_log.append(f"{model}: {e}")
                logger.warning(f"⚠️  OpenRouter {model} failed ({e}) — trying next")
                continue
    else:
        attempts_log.append("OpenRouter: no API key configured (optional fallback skipped)")

    # ── Everything failed ────────────────────────────────────
    error_summary = " | ".join(attempts_log)
    logger.error(f"❌ ALL providers failed: {error_summary}")
    return Result.fail(f"All AI providers failed: {error_summary}")


def generate_text(prompt: str, max_tokens: int = 1300,
                   prefer_quality: bool = False) -> Optional[str]:
    """
    Convenience wrapper that returns a plain string instead of a Result.

    Returns None if all providers fail. This signature is backwards-compatible
    with the old ``_gemini()`` helper used in ``ai_generator.py`` and
    ``deep_research.py``.
    """
    result = generate(prompt, max_tokens, prefer_quality)
    if result:
        return result.data["text"]
    return None


def which_model_answered(prompt: str, max_tokens: int = 100) -> str:
    """Debug helper — returns the name of the first model that currently responds."""
    result = generate(prompt, max_tokens)
    return result.data["model_used"] if result else f"NONE WORKING ({result.error})"


def check_all_providers() -> Dict[str, bool]:
    """
    Health-check every configured AI provider with a minimal test prompt.

    Used by the web dashboard’s “Connection Status” panel to show which
    models are currently reachable.  Returns a dict of model names to
    availability booleans (None = not configured).
    """
    status = {}
    test_prompt = "Reply with exactly one word: OK"

    for model in GEMINI_MODELS:
        try:
            _call_gemini_model(model, test_prompt, 10)
            status[f"gemini/{model}"] = True
        except Exception as e:
            status[f"gemini/{model}"] = False

    if cfg.OPENROUTER_API_KEY:
        try:
            _call_openrouter_model(OPENROUTER_FREE_MODELS[0], test_prompt, 10)
            status[f"openrouter/{OPENROUTER_FREE_MODELS[0]}"] = True
        except Exception:
            status[f"openrouter/{OPENROUTER_FREE_MODELS[0]}"] = False
    else:
        status["openrouter (not configured)"] = None

    return status


if __name__ == "__main__":
    print("=" * 55)
    print("🤖 TechNova World — Unified AI Client Test")
    print("=" * 55)

    if not cfg.GEMINI_API_KEY and not cfg.OPENROUTER_API_KEY:
        print("\n❌ No API keys configured. Set GEMINI_API_KEY or OPENROUTER_API_KEY")
        exit(1)

    print("\n🔍 Checking all providers...")
    status = check_all_providers()
    for model, ok in status.items():
        icon = "✅" if ok else ("⚪" if ok is None else "❌")
        print(f"  {icon} {model}")

    print("\n🧪 Test generation...")
    result = generate("Write one sentence about AI tools for beginners.", max_tokens=100)
    if result:
        print(f"\n✅ Success via: {result.data['model_used']}")
        print(f"   Output: {result.data['text'][:200]}")
    else:
        print(f"\n❌ All providers failed: {result.error}")
