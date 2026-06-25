"""
TechNova World — Video Script Generator v2.0
YouTube Shorts / Instagram Reels / LinkedIn Video ke liye
60-second aur 3-minute scripts generate karta hai
"""

import re
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from utils import logger, retry, Result, save_text
import config as cfg

# ── AI CALL — routed through unified ai_client (Gemini 2.5 + OpenRouter) ──
from ai_client import generate_text


def _gemini(prompt: str, max_tokens: int = 1500) -> str:
    """
    Naam purana rakha hai. Ab ai_client ke fallback chain se generate
    hota hai. Contract preserved: raises on failure (callers wrap in try/except).
    """
    text = generate_text(prompt, max_tokens=max_tokens)
    if text is None:
        raise Exception("All AI providers failed (Gemini 2.5 + OpenRouter exhausted)")
    return text


# ── VIDEO FORMATS ─────────────────────────────────────────────

VIDEO_FORMATS = {
    "shorts_60":    {"name": "YouTube Shorts / Reels (60 sec)", "duration": 60,  "words": 150},
    "shorts_30":    {"name": "TikTok / Reels (30 sec)",         "duration": 30,  "words": 75},
    "linkedin_60":  {"name": "LinkedIn Video (60 sec)",          "duration": 60,  "words": 150},
    "youtube_3min": {"name": "YouTube Video (3 min)",            "duration": 180, "words": 450},
    "podcast_clip": {"name": "Podcast Clip (90 sec)",            "duration": 90,  "words": 225},
}


def generate_video_script(
    topic: str,
    format_key: str = "shorts_60",
    hook_style: str = "question"
) -> Result:
    """
    Video script generate karo

    Args:
        topic: Video ka topic
        format_key: VIDEO_FORMATS mein se key
        hook_style: question / shocking_stat / story / contrarian

    Returns:
        Result with script dict
    """
    fmt = VIDEO_FORMATS.get(format_key, VIDEO_FORMATS["shorts_60"])
    duration = fmt["duration"]
    words    = fmt["words"]

    hook_styles = {
        "question":      "Start with a thought-provoking question that makes viewers stop scrolling",
        "shocking_stat": "Start with a surprising statistic or fact about AI",
        "story":         "Start with a 1-sentence personal story or relatable scenario",
        "contrarian":    "Start with a controversial or counter-intuitive statement",
    }
    hook_desc = hook_styles.get(hook_style, hook_styles["question"])

    prompt = f"""Write a {duration}-second video script for {cfg.BRAND_NAME} about: "{topic}"

Target audience: {cfg.AUDIENCE}
Platform: {fmt['name']}
Approximate words: {words}
Hook style: {hook_desc}

Format the script EXACTLY like this:

=== VIDEO SCRIPT ===
Topic: {topic}
Duration: {duration} seconds
Format: {fmt['name']}

[HOOK - 0:00 to 0:05]
(Visual: describe what viewer sees)
VOICEOVER: [First 1-2 sentences — the hook]

[PROBLEM/SETUP - 0:05 to 0:{int(duration*0.25):02d}]
(Visual: describe visual)
VOICEOVER: [Setup the problem or context]

[MAIN CONTENT - 0:{int(duration*0.25):02d} to 0:{int(duration*0.75):02d}]
(Visual: describe visual — use text overlays, demos, etc.)
VOICEOVER: [Core content — 2-3 key points]

[CTA - 0:{int(duration*0.75):02d} to 0:{duration:02d}]
(Visual: describe visual)
VOICEOVER: [Call to action — Follow TechNova World, comment, share]

=== THUMBNAIL IDEAS ===
1. [Thumbnail concept 1]
2. [Thumbnail concept 2]
3. [Thumbnail concept 3]

=== CAPTION (for posting) ===
[60-word caption with hook, description, and hashtags]

=== HASHTAGS ===
[10 relevant hashtags]

=== B-ROLL SUGGESTIONS ===
- [Visual 1 needed]
- [Visual 2 needed]
- [Visual 3 needed]

Rules:
- Simple language, no jargon
- Each section MUST fit the time window
- Conversational tone — like talking to a friend
- High energy, quick cuts style for Shorts
- Include [PAUSE] markers where presenter should pause
- Include [TEXT OVERLAY: text] where on-screen text should appear"""

    try:
        script = _gemini(prompt)
        logger.info(f"✅ Video script generated: {topic[:50]}")

        # Parse sections
        parsed = _parse_script(script)
        parsed["raw"] = script
        parsed["topic"] = topic
        parsed["format"] = fmt["name"]
        parsed["duration"] = duration

        return Result.success(parsed)
    except Exception as e:
        return Result.fail(str(e))


def _parse_script(raw: str) -> Dict:
    """Script ke sections parse karo"""
    sections = {
        "hook": "",
        "setup": "",
        "content": "",
        "cta": "",
        "thumbnail_ideas": [],
        "caption": "",
        "hashtags": "",
        "broll": [],
    }

    current = None
    lines = raw.split('\n')

    for line in lines:
        l = line.strip()
        if "[HOOK" in l.upper():               current = "hook"
        elif "[PROBLEM" in l.upper() or "[SETUP" in l.upper(): current = "setup"
        elif "[MAIN CONTENT" in l.upper():     current = "content"
        elif "[CTA" in l.upper():              current = "cta"
        elif "THUMBNAIL IDEAS" in l.upper():   current = "thumbnail"
        elif "CAPTION" in l.upper():           current = "caption"
        elif "HASHTAGS" in l.upper():          current = "hashtags"
        elif "B-ROLL" in l.upper():            current = "broll"
        elif l and current:
            if current == "thumbnail" and l.startswith(("1.", "2.", "3.")):
                sections["thumbnail_ideas"].append(l[2:].strip())
            elif current == "broll" and l.startswith("-"):
                sections["broll"].append(l[1:].strip())
            elif current in sections and isinstance(sections[current], str):
                sections[current] += l + "\n"

    return sections


def generate_shorts_series(topic: str, episode_count: int = 5) -> Result:
    """
    Ek topic pe short video series generate karo

    Args:
        topic: Main topic
        episode_count: Number of episodes

    Returns:
        Result with list of scripts
    """
    logger.info(f"🎬 {episode_count}-episode shorts series: {topic}")

    prompt = f"""Create a {episode_count}-episode YouTube Shorts series plan for {cfg.BRAND_NAME} about: "{topic}"

For each episode:
- Episode number and title
- 15-word hook (first line of script)
- 3 main points covered
- Cliffhanger to next episode (except last)

Format clearly. Target: {cfg.AUDIENCE}
Make each episode standalone but connected."""

    try:
        plan = _gemini(prompt)
        logger.info(f"✅ Series plan generated")
        return Result.success(plan)
    except Exception as e:
        return Result.fail(str(e))


def generate_talking_points(topic: str) -> Result:
    """
    Video ke liye bullet-point talking points generate karo
    (Teleprompter style)
    """
    prompt = f"""Create teleprompter-style talking points for a TechNova World video about: "{topic}"

Audience: {cfg.AUDIENCE}

Format:
INTRO (15 sec):
• [Opening line]
• [Hook statement]

POINT 1 (20 sec): [Title]
• [Sub-point]
• [Sub-point]
• [Example]

POINT 2 (20 sec): [Title]
• [Sub-point]
• [Sub-point]

POINT 3 (15 sec): [Title]
• [Sub-point]
• [Sub-point]

OUTRO (10 sec):
• [Summary line]
• [CTA: Follow TechNova World]

Keep each bullet under 10 words. Simple language."""

    try:
        points = _gemini(prompt)
        return Result.success(points)
    except Exception as e:
        return Result.fail(str(e))


def create_full_video_package(topic: str, format_key: str = "shorts_60") -> Result:
    """
    Complete video package banao:
    - Main script
    - Talking points
    - Caption
    - Thumbnail concepts

    Args:
        topic: Video topic
        format_key: shorts_60 / youtube_3min / linkedin_60

    Returns:
        Result with all files
    """
    fmt = VIDEO_FORMATS.get(format_key, VIDEO_FORMATS["shorts_60"])
    logger.info(f"🎬 Full video package: '{topic}' [{fmt['name']}]")

    results = {}

    # 1. Main script
    logger.info("  📝 Script generate kar raha hoon...")
    script_result = generate_video_script(topic, format_key)
    if script_result:
        results["script"] = script_result.data
    else:
        return Result.fail(f"Script generation failed: {script_result.error}")

    # 2. Talking points
    logger.info("  🎯 Talking points generate kar raha hoon...")
    tp_result = generate_talking_points(topic)
    if tp_result:
        results["talking_points"] = tp_result.data

    # Save everything
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    safe_topic = re.sub(r'\W+', '_', topic[:30])
    out_dir = Path("generated")
    out_dir.mkdir(exist_ok=True)

    # Script file
    script_path = str(out_dir / f"video_script_{safe_topic}_{ts}.txt")
    save_text(script_path, results["script"]["raw"])

    # Talking points file
    if "talking_points" in results:
        tp_path = str(out_dir / f"talking_points_{safe_topic}_{ts}.txt")
        save_text(tp_path, results["talking_points"])
        results["talking_points_file"] = tp_path

    results["script_file"] = script_path

    logger.info(f"✅ Video package ready!")
    logger.info(f"   Script: {script_path}")

    return Result.success(results)


if __name__ == "__main__":
    print("=" * 55)
    print("🎬 TechNova World — Video Script Generator Test")
    print("=" * 55)

    if not cfg.GEMINI_API_KEY:
        print("❌ config.py mein GEMINI_API_KEY set karo")
        exit(1)

    print("\nFormat options:")
    for k, v in VIDEO_FORMATS.items():
        print(f"  {k}: {v['name']}")

    topic = input("\nVideo topic? (Enter = default): ").strip()
    if not topic:
        topic = "How ChatGPT Can Replace 5 Hours of Your Work Daily"

    fmt = input("Format key? (Enter = shorts_60): ").strip() or "shorts_60"

    result = create_full_video_package(topic, fmt)

    if result:
        print(f"\n✅ Video package ready!")
        print(f"   Script file: {result.data.get('script_file')}")
        if result.data.get("talking_points_file"):
            print(f"   Talking points: {result.data.get('talking_points_file')}")
        print("\nScript preview:")
        print("-" * 40)
        raw = result.data["script"].get("raw", "")
        print(raw[:600] + "...")
    else:
        print(f"\n❌ Failed: {result.error}")
