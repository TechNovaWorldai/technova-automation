"""
TechNova World — LinkedIn Poster v3.0

Handles all LinkedIn publishing for TechNova World.

Posting strategy:
  1. Try the company / organisation page first (requires LINKEDIN_ORGANIZATION_ID).
  2. If the company post returns a 403 (Community Management API approval pending),
     automatically fall back to the personal profile (w_member_social scope).
  3. Person URN is fetched automatically from the token if not set explicitly.
"""

import requests
from datetime import datetime
from pathlib import Path
from typing import Optional
from utils import logger, retry, Result
import config as cfg


def _headers() -> dict:
    return {
        "Authorization":             f"Bearer {cfg.LINKEDIN_ACCESS_TOKEN}",
        "Content-Type":              "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _fetch_person_urn() -> Optional[str]:
    """Derive the LinkedIn Person URN from the current access token."""
    for url, field in [
        ("https://api.linkedin.com/v2/userinfo", "sub"),
        ("https://api.linkedin.com/v2/me",       "id"),
    ]:
        try:
            r = requests.get(url, headers=_headers(), timeout=cfg.API_TIMEOUT)
            if r.status_code == 200:
                val = r.json().get(field)
                if val:
                    return val if val.startswith("urn:li:person:") else f"urn:li:person:{val}"
        except Exception:
            continue
    return None


def check_linkedin_connection() -> bool:
    """Verify that the LinkedIn access token is valid.

    Proceeds even on HTTP 403 responses because a 403 may indicate a scope
    limitation rather than an expired token — posting may still succeed.
    """
    if not cfg.LINKEDIN_ACCESS_TOKEN:
        logger.error("❌ LINKEDIN_ACCESS_TOKEN missing")
        return False

    for url, field in [
        ("https://api.linkedin.com/v2/userinfo", "sub"),
        ("https://api.linkedin.com/v2/me",       "localizedFirstName"),
    ]:
        try:
            r = requests.get(url, headers=_headers(), timeout=cfg.API_TIMEOUT)
            if r.status_code == 200:
                name = r.json().get(field) or r.json().get("name") or "User"
                logger.info(f"✅ LinkedIn token valid! ({name})")
                return True
            elif r.status_code == 401:
                logger.error("❌ Token expired — naya token lo: developer.linkedin.com/tools/oauth")
                return False
            elif r.status_code == 403:
                continue  # scope issue, try next endpoint
        except Exception:
            continue

    # All profile endpoints returned 403 — token likely valid for posting
    if cfg.LINKEDIN_ORGANIZATION_ID or cfg.LINKEDIN_PERSON_URN:
        logger.warning("⚠️  Profile check returned 403 (scope issue) — proceeding with posting anyway")
        return True

    logger.error("❌ Cannot verify token — check LINKEDIN_ACCESS_TOKEN")
    return False


def post_to_linkedin(text: str, image_path: str = None, force_personal: bool = False) -> Result:
    """
    Publish a post to LinkedIn.

    Strategy:
      1. Attempt the company / organisation page (if LINKEDIN_ORGANIZATION_ID is set).
      2. If that returns a 403, fall back to the personal profile
         (auto-fetching the Person URN from the token when necessary).

    Args:
        text:           The post content (20 – 3000 chars).
        image_path:     Optional path to an image file to attach.
        force_personal: Skip the company page and post directly to the personal profile.

    Returns:
        ``Result`` with ``.data = {"post_id": str, "posted_to": str}`` on success.
    """
    if not cfg.LINKEDIN_ACCESS_TOKEN:
        return Result.fail("LINKEDIN_ACCESS_TOKEN missing")

    if not text or len(text.strip()) < 20:
        return Result.fail("Content too short (min 20 chars)")

    if len(text) > 3000:
        text = text[:2990] + "..."

    # Determine targets
    has_company  = bool(cfg.LINKEDIN_ORGANIZATION_ID) and not force_personal
    person_urn   = cfg.LINKEDIN_PERSON_URN

    # Auto-fetch person URN if not set
    if not person_urn:
        person_urn = _fetch_person_urn()
        if person_urn:
            logger.info(f"✅ Auto-fetched Person URN: {person_urn}")
            cfg.LINKEDIN_PERSON_URN = person_urn

    has_personal = bool(person_urn)

    if not has_company and not has_personal:
        return Result.fail(
            "No posting target! Set LINKEDIN_ORGANIZATION_ID (company) "
            "or LINKEDIN_PERSON_URN (personal) in GitHub Secrets."
        )

    # Try company page first
    if has_company:
        urn    = f"urn:li:organization:{cfg.LINKEDIN_ORGANIZATION_ID}"
        result = _do_post(text, image_path, urn, "company page")
        if result.ok:
            result.data["posted_to"] = "company"
            return result

        is_perm_error = any(x in result.error for x in ["403", "401", "ACCESS_DENIED", "Permission"])
        if not is_perm_error or not has_personal:
            return result

        logger.warning("⚠️  Company page 403 — Community Management API approval pending")
        logger.warning("🔄 Falling back to personal profile...")

    # Personal profile fallback
    if has_personal:
        result = _do_post(text, image_path, person_urn, "personal profile")
        if result.ok:
            result.data["posted_to"] = "personal"
            if has_company:
                result.data["note"] = (
                    "Posted to PERSONAL profile (company page needs "
                    "Community Management API approval). "
                    "Share post to TechNova World page manually."
                )
        return result

    return Result.fail("All posting attempts failed")


def _do_post(text: str, image_path: str, author_urn: str, label: str) -> Result:
    """Execute a single LinkedIn UGC post request and map the HTTP response to a Result."""
    share_content = {
        "shareCommentary":    {"text": text},
        "shareMediaCategory": "NONE",
    }

    post_body = {
        "author":          author_urn,
        "lifecycleState":  "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
        "visibility":      {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    logger.info(f"📤 Posting to {label}...")
    try:
        r = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=_headers(),
            json=post_body,
            timeout=cfg.API_TIMEOUT,
        )

        if r.status_code == 201:
            post_id = r.json().get("id", "unknown")
            logger.info(f"✅ Posted to {label}! ID: {post_id}")
            return Result.success({"post_id": post_id, "timestamp": datetime.now().isoformat()})
        elif r.status_code == 401:
            return Result.fail("401 Token expired — naya token lo")
        elif r.status_code == 403:
            return Result.fail(f"403 Permission denied for {label}")
        elif r.status_code == 422:
            return Result.fail(f"422 Validation: {r.json().get('message', 'unknown')}")
        else:
            return Result.fail(f"HTTP {r.status_code}: {r.text[:200]}")

    except requests.exceptions.Timeout:
        return Result.fail("Timeout — LinkedIn slow hai")
    except requests.exceptions.ConnectionError:
        return Result.fail("Network error")
    except Exception as e:
        return Result.fail(f"Error: {e}")
