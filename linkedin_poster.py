"""
TechNova World — LinkedIn Auto-Poster v2.0
Company Page pe automatically post karta hai
Proper error handling + token validation
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


def check_linkedin_connection() -> bool:
    """LinkedIn connection test karo."""
    if not cfg.LINKEDIN_ACCESS_TOKEN:
        logger.error("❌ LINKEDIN_ACCESS_TOKEN config.py mein set nahi hai")
        logger.error("   developer.linkedin.com → OAuth Playground → token lo")
        return False

    try:
        r = requests.get(
            "https://api.linkedin.com/v2/me",
            headers=_headers(),
            timeout=cfg.API_TIMEOUT
        )
        if r.status_code == 200:
            data = r.json()
            name = data.get("localizedFirstName", "User")
            logger.info(f"✅ LinkedIn connected! ({name})")
            return True
        elif r.status_code == 401:
            logger.error("❌ Token invalid ya expired! Naya token lo.")
            logger.error("   linkedin.com/developers/tools/oauth → regenerate")
            return False
        else:
            logger.error(f"❌ LinkedIn check failed: HTTP {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ Network error — internet check karo")
        return False
    except Exception as e:
        logger.error(f"❌ LinkedIn connection error: {e}")
        return False


@retry(max_tries=2, delay=5)
def _upload_image(image_path: str) -> Optional[str]:
    """Image upload karo LinkedIn pe, asset URN return karo."""
    logger.info(f"📸 Image upload kar raha hoon: {image_path}")

    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner":   f"urn:li:organization:{cfg.LINKEDIN_ORGANIZATION_ID}",
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier":       "urn:li:userGeneratedContent"
            }]
        }
    }

    r = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers=_headers(),
        json=register_payload,
        timeout=cfg.API_TIMEOUT
    )

    if r.status_code != 200:
        logger.error(f"Image registration failed: {r.status_code} — {r.text[:200]}")
        return None

    data       = r.json()
    upload_url = (data["value"]["uploadMechanism"]
                  ["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]
                  ["uploadUrl"])
    asset_id   = data["value"]["asset"]

    # Upload image bytes
    with open(image_path, "rb") as f:
        img_data = f.read()

    r2 = requests.put(
        upload_url,
        headers={"Authorization": f"Bearer {cfg.LINKEDIN_ACCESS_TOKEN}"},
        data=img_data,
        timeout=60
    )

    if r2.status_code in (200, 201):
        logger.info(f"✅ Image uploaded: {asset_id}")
        return asset_id
    else:
        logger.error(f"Image upload failed: {r2.status_code}")
        return None


def post_to_linkedin(text: str, image_path: str = None) -> Result:
    """
    LinkedIn Company Page pe post karo.

    Args:
        text:       Post content (max ~3000 chars)
        image_path: Optional image file path

    Returns:
        Result with post_id on success
    """
    # Pre-flight checks
    if not cfg.LINKEDIN_ACCESS_TOKEN:
        return Result.fail("LINKEDIN_ACCESS_TOKEN set nahi hai — config.py update karo")

    if not cfg.LINKEDIN_ORGANIZATION_ID:
        return Result.fail("LINKEDIN_ORGANIZATION_ID set nahi hai — config.py update karo")

    if not text or len(text.strip()) < 20:
        return Result.fail("Post content too short (min 20 chars)")

    if len(text) > 3000:
        logger.warning(f"⚠️  Post {len(text)} chars — LinkedIn 3000 char limit! Truncating...")
        text = text[:2990] + "..."

    # Optional image upload
    image_urn = None
    if image_path:
        if not Path(image_path).exists():
            logger.warning(f"⚠️  Image nahi mili: {image_path} — text-only post karunga")
        else:
            image_urn = _upload_image(image_path)

    # Build post body
    share_content = {
        "shareCommentary":   {"text": text},
        "shareMediaCategory": "IMAGE" if image_urn else "NONE",
    }
    if image_urn:
        share_content["media"] = [{"status": "READY", "media": image_urn}]

    post_body = {
        "author":          f"urn:li:organization:{cfg.LINKEDIN_ORGANIZATION_ID}",
        "lifecycleState":  "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
        "visibility":      {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    logger.info("📤 LinkedIn pe post kar raha hoon...")
    try:
        r = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=_headers(),
            json=post_body,
            timeout=cfg.API_TIMEOUT
        )

        if r.status_code == 201:
            post_id = r.json().get("id", "unknown")
            logger.info(f"✅ LinkedIn posted! ID: {post_id}")
            return Result.success({"post_id": post_id, "timestamp": datetime.now().isoformat()})

        elif r.status_code == 401:
            return Result.fail("Token expired! Naya token lo: linkedin.com/developers/tools/oauth")

        elif r.status_code == 403:
            return Result.fail(
                "Permission denied! App mein 'Share on LinkedIn' product add karo: developer.linkedin.com"
            )

        elif r.status_code == 422:
            err = r.json().get("message", "Unknown validation error")
            return Result.fail(f"Validation error: {err}")

        else:
            return Result.fail(f"HTTP {r.status_code}: {r.text[:300]}")

    except requests.exceptions.Timeout:
        return Result.fail("Request timeout — LinkedIn server slow hai, baad mein try karo")
    except requests.exceptions.ConnectionError:
        return Result.fail("Network error — internet connection check karo")
    except Exception as e:
        return Result.fail(f"Unexpected error: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("💼 TechNova World — LinkedIn Poster v2.0 Test")
    print("=" * 50)

    connected = check_linkedin_connection()

    if connected:
        print("\n✅ LinkedIn ready!")
        print("\nTest post karna hai? (y/n): ", end="")
        if input().strip().lower() == "y":
            test_text = ("🧪 TechNova World automation test.\n\n"
                         "Agar yeh dikh raha hai toh Python automation kaam kar raha hai! 🎉\n\n"
                         "#AI #TechNova #Automation")
            result = post_to_linkedin(test_text)
            if result:
                print(f"✅ Post ID: {result.data['post_id']}")
            else:
                print(f"❌ Failed: {result.error}")
    else:
        print("\n📋 Setup steps:")
        print("1. developer.linkedin.com → App banao")
        print("2. 'Share on LinkedIn' product add karo")
        print("3. linkedin.com/developers/tools/oauth → token lo")
        print("4. config.py mein token + org ID paste karo")
