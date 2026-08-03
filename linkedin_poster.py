"""
TechNova World — LinkedIn Poster v3.1

Handles all LinkedIn publishing for TechNova World.

Posting strategy:
  1. Try the company / organisation page first (requires LINKEDIN_ORGANIZATION_ID).
  2. If the company post returns a 403 (Community Management API approval pending),
     automatically fall back to the personal profile (w_member_social scope).
  3. Person URN is fetched automatically from the token if not set explicitly.

Required OAuth scopes (LinkedIn Developer App):
  - w_member_social   — post on behalf of the member (personal)
  - r_liteprofile     — read profile to auto-fetch Person URN
  - r_emailaddress    — (optional but often bundled)
  - rw_organization_social — post to company page (requires LinkedIn approval)

Common failure causes:
  • Token expired (LinkedIn tokens expire every 60 days)
  • Missing LINKEDIN_ORGANIZATION_ID *and* LINKEDIN_PERSON_URN in Secrets
  • Wrong OAuth scopes selected when generating the token
  • Company page posting requires Community Management API approval from LinkedIn

Run diagnose_linkedin() for a full self-test report.
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
    if not cfg.LINKEDIN_ACCESS_TOKEN:
        logger.error("❌ Cannot fetch Person URN: LINKEDIN_ACCESS_TOKEN is not set.")
        return None

    for url, field in [
        ("https://api.linkedin.com/v2/userinfo", "sub"),
        ("https://api.linkedin.com/v2/me",       "id"),
    ]:
        try:
            r = requests.get(url, headers=_headers(), timeout=cfg.API_TIMEOUT)
            if r.status_code == 200:
                val = r.json().get(field)
                if val:
                    urn = val if val.startswith("urn:li:person:") else f"urn:li:person:{val}"
                    logger.debug(f"Person URN resolved from {url}: {urn}")
                    return urn
            elif r.status_code == 403:
                logger.debug(f"_fetch_person_urn: 403 on {url} (scope limitation) — trying next endpoint")
            elif r.status_code == 401:
                logger.error("❌ _fetch_person_urn: 401 Unauthorized — token may be expired.")
                return None
        except Exception as exc:
            logger.debug(f"_fetch_person_urn: exception on {url}: {exc}")
            continue
    logger.warning(
        "⚠️  Could not auto-fetch Person URN (both profile endpoints returned 403/error). "
        "Set LINKEDIN_PERSON_URN manually in your .env / GitHub Secrets."
    )
    return None


def check_linkedin_connection() -> bool:
    """Verify that the LinkedIn access token is valid.

    Proceeds even on HTTP 403 responses because a 403 may indicate a scope
    limitation rather than an expired token — posting may still succeed.
    """
    if not cfg.LINKEDIN_ACCESS_TOKEN:
        logger.error(
            "❌ LINKEDIN_ACCESS_TOKEN is not set.\n"
            "   → Local: add it to your .env file\n"
            "   → GitHub Actions: add it as a repository Secret\n"
            "   → Render: add it in the Environment Variables panel"
        )
        return False

    for url, field in [
        ("https://api.linkedin.com/v2/userinfo", "sub"),
        ("https://api.linkedin.com/v2/me",       "localizedFirstName"),
    ]:
        try:
            r = requests.get(url, headers=_headers(), timeout=cfg.API_TIMEOUT)
            if r.status_code == 200:
                name = r.json().get(field) or r.json().get("name") or "User"
                logger.info(f"✅ LinkedIn token is valid. Authenticated as: {name}")
                return True
            elif r.status_code == 401:
                logger.error(
                    "❌ LinkedIn token has expired (HTTP 401).\n"
                    "   → Go to: https://developer.linkedin.com/tools/oauth\n"
                    "   → Generate a new Access Token\n"
                    "   → Update LINKEDIN_ACCESS_TOKEN in GitHub Secrets / .env"
                )
                return False
            elif r.status_code == 403:
                continue  # Scope limitation on this endpoint — try next one
        except Exception:
            continue

    # All profile endpoints returned 403 — token is likely valid for posting
    if cfg.LINKEDIN_ORGANIZATION_ID or cfg.LINKEDIN_PERSON_URN:
        logger.warning(
            "⚠️  Profile endpoints returned 403 (likely a scope limitation).\n"
            "   Your token may still be valid for posting — proceeding.\n"
            "   If posts also fail, regenerate the token with r_liteprofile scope."
        )
        return True

    logger.error(
        "❌ Cannot verify LinkedIn token — all profile endpoints returned 403.\n"
        "   → Ensure your LinkedIn App has the r_liteprofile scope enabled.\n"
        "   → Or set LINKEDIN_PERSON_URN manually to bypass profile lookup."
    )
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
            return Result.fail(
                "401 Unauthorized: LinkedIn token has expired.\n"
                "Fix: go to https://developer.linkedin.com/tools/oauth, generate a new token,\n"
                "then update LINKEDIN_ACCESS_TOKEN in your GitHub Secrets or .env file."
            )
        elif r.status_code == 403:
            msg = (
                f"403 Permission denied for {label}." + "\n"
                "Likely cause: your OAuth token lacks the required scope (w_member_social for\n"
                "personal posts, rw_organization_social for company page posts).\n"
                "Fix: regenerate the token with the correct scopes enabled."
            )
            return Result.fail(msg)
        elif r.status_code == 422:
            msg = r.json().get('message', r.text[:200])
            return Result.fail("422 Validation error: " + str(msg))
        else:
            return Result.fail("HTTP " + str(r.status_code) + ": " + str(r.text[:200]))

    except requests.exceptions.Timeout:
        return Result.fail(
            "Request timed out after " + str(cfg.API_TIMEOUT) + "s posting to " + str(label) + ". "
            "LinkedIn may be slow -- the job will retry automatically."
        )
    except requests.exceptions.ConnectionError:
        return Result.fail("Network error: could not reach api.linkedin.com. Check your internet connection.")
    except Exception as exc:
        return Result.fail("Unexpected error posting to " + str(label) + ": " + str(exc))


def diagnose_linkedin() -> None:
    """
    Print a full LinkedIn configuration diagnostic report.

    Run this locally to troubleshoot posting failures before deploying:
        python -c "from linkedin_poster import diagnose_linkedin; diagnose_linkedin()"
    """
    print("\n" + "=" * 60)
    print("  [DIAGNOSTICS] TechNova World -- LinkedIn Diagnostics")
    print("=" * 60)

    token = cfg.LINKEDIN_ACCESS_TOKEN
    org   = cfg.LINKEDIN_ORGANIZATION_ID
    urn   = cfg.LINKEDIN_PERSON_URN

    token_info = '[SET] (' + token[:8] + '...)' if token else '[NOT SET]'
    org_info = org if org else '[NOT SET] (personal-only mode)'
    urn_info = urn if urn else '[NOT SET] (will auto-fetch)'
    fallback_info = 'Enabled' if cfg.LINKEDIN_FALLBACK_TO_PERSONAL else 'Disabled'

    print("\n  LINKEDIN_ACCESS_TOKEN        : " + token_info)
    print("  LINKEDIN_ORGANIZATION_ID     : " + org_info)
    print("  LINKEDIN_PERSON_URN          : " + urn_info)
    print("  LINKEDIN_FALLBACK_TO_PERSONAL: " + fallback_info)

    if not token:
        print("\n  [FATAL] No access token. Cannot proceed.")
        print("  -> Get one at: https://developer.linkedin.com/tools/oauth")
        print("=" * 60 + "\n")
        return

    print("\n  Testing connection ...")
    ok = check_linkedin_connection()
    status_str = '[PASS]' if ok else '[FAIL]'
    print("  Connection check : " + status_str)

    if not urn:
        print("  Auto-fetching Person URN ...")
        fetched = _fetch_person_urn()
        urn_str = fetched if fetched else '[FAIL] Could not fetch'
        print("  Person URN       : " + urn_str)
    else:
        fetched = urn

    if org:
        print("\n  Posting target   : Company page (urn:li:organization:" + str(org) + ")")
    elif fetched:
        print("\n  Posting target   : Personal profile (" + str(fetched) + ")")
    else:
        print("\n  [FAIL] No posting target available. Set LINKEDIN_ORGANIZATION_ID or LINKEDIN_PERSON_URN.")

    print("\n  Required OAuth Scopes:")
    print("    r_liteprofile          -- read profile (URN auto-fetch)")
    print("    w_member_social        -- post as member (personal)")
    print("    rw_organization_social -- post as company (needs LinkedIn approval)")
    print("\n  If you see 403 errors, regenerate your token at:")
    print("    https://developer.linkedin.com/tools/oauth")
    print("  and ensure ALL three scopes above are checked.")
    print("=" * 60 + "\n")
