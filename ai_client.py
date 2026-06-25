"""
TechNova World — Unified AI Client v5.0
Single entry point for ALL AI calls in the app.

Fallback chain (in order):
  1. Gemini 2.5 Flash    (fast, free tier, primary)
  2. Gemini 2.5 Pro       (better quality, same free key, used if Flash fails)
  3. OpenRouter free pool (different provider entirely — survives Google outages)

Why this matters:
  Gemini 1.5 models were SHUT DOWN by Google (404 errors) — this is exactly
  why the old app broke. Models get deprecated. A fallback chain across
  TWO PROVIDERS means one company's decision can't break your automation.
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
    """Single Gemini model call — raises on any failure."""
    if not cfg.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")

    url = f"{GEMINI_BASE}/{model}:generateContent?key={cfg.GEMINI_API_KEY}"
    r = requests.post(
        url,
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.8,
                "topP": 0.94,
            },
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

    return cands[0]["content"]["parts"][0]["text"]


# ════════════════════════════════════════════════════════════
# PROVIDER: OPENROUTER
# ════════════════════════════════════════════════════════════

def _call_openrouter_model(model: str, prompt: str, max_tokens: int) -> str:
    """Single OpenRouter model call — raises on any failure."""
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
    Generate text using the full fallback chain.

    Args:
        prompt:         The prompt to send
        max_tokens:      Max output tokens
        prefer_quality:  If True, tries Gemini 2.5 Pro FIRST (slower, better)

    Returns:
        Result with .data = generated text, .data also includes
        which model actually answered (for transparency/debugging)
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
    Convenience wrapper — returns just the text string (or None).
    This matches the old _gemini() function signature so existing
    code in ai_generator.py / deep_research.py keeps working.
    """
    result = generate(prompt, max_tokens, prefer_quality)
    if result:
        return result.data["text"]
    return None


def which_model_answered(prompt: str, max_tokens: int = 100) -> str:
    """Debug helper — tells you which model/provider is currently working."""
    result = generate(prompt, max_tokens)
    return result.data["model_used"] if result else f"NONE WORKING ({result.error})"


def check_all_providers() -> Dict[str, bool]:
    """
    Health check — tests each provider with a tiny prompt.
    Used by the dashboard's "Connection Status" panel.
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
