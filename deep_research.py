"""
TechNova World — Deep Research Mode v5.0
Senior writer jaisa multi-step content process:
  1. Research outline (facts, angles, data points needed)
  2. Gather specifics (numbers, examples, comparisons)
  3. Draft with depth (not surface-level)
  4. Self-critique pass
  5. Final polish

Why this matters:
Single-prompt generation gives surface-level content.
Multi-step process forces the AI to "think" like a researcher first.

v5.0: Ab ai_client.py ke through generate karta hai (Gemini 2.5 +
OpenRouter fallback) — purana hardcoded gemini-1.5-flash hata diya
(woh model Google ne deprecate kar diya tha, isliye fail ho raha tha).
"""

import re
import time
from typing import Dict, List, Optional
from pathlib import Path

from utils       import logger, retry, Result, save_text
from ai_client    import generate_text
from brand_voice import build_voice_context, check_voice_compliance
import config as cfg


def _gemini(prompt: str, max_tokens: int = 1500) -> Optional[str]:
    """Naam purana rakha — ab ai_client ke fallback chain se generate hota hai."""
    return generate_text(prompt, max_tokens=max_tokens)


# ════════════════════════════════════════════════════════════
# STEP 1: RESEARCH OUTLINE
# ════════════════════════════════════════════════════════════

def step1_research_outline(topic: str, audience: str) -> Optional[str]:
    """
    Pehla step — senior writer jaisa "research plan" banao.
    Yeh batata hai: kya specific facts, angles, examples chahiye.
    """
    logger.info(f"  🔬 Step 1/4: Research outline — {topic[:40]}")

    prompt = f"""You are a senior technical writer planning an article about: "{topic}"
Audience: {audience}

Before writing, create a RESEARCH OUTLINE. List:

1. KEY FACTS NEEDED (3-4 specific facts/numbers that would make this credible):
   - What specific data points should be included?
   - What comparisons would help? (vs alternatives, vs old method, etc.)

2. REAL EXAMPLES NEEDED (2-3 concrete scenarios):
   - What specific use-case or scenario illustrates this best?
   - What would a skeptical reader want proof of?

3. COMMON MISCONCEPTIONS to address:
   - What do people get wrong about this topic?

4. THE "HONEST DOWNSIDE":
   - What's a genuine limitation or tradeoff to mention? (builds trust)

5. UNIQUE ANGLE:
   - What angle would make this DIFFERENT from generic AI-written content on this topic?

Be specific. Don't write the article yet — just the research plan."""

    return _gemini(prompt, max_tokens=800)


# ════════════════════════════════════════════════════════════
# STEP 2: GATHER SPECIFICS
# ════════════════════════════════════════════════════════════

def step2_specifics(topic: str, outline: str) -> Optional[str]:
    """
    Doosra step — outline ke based pe specific details generate karo.
    (Note: yeh Gemini ke training data se hai, real-time search nahi.
     Critical/recent facts ke liye search_agent.py use karo.)
    """
    logger.info(f"  📊 Step 2/4: Gathering specifics")

    prompt = f"""Based on this research outline about "{topic}":

{outline}

Now provide the ACTUAL specifics for each point:
- Give realistic numbers/timeframes (mark as "approximately" if estimating)
- Write out 2 concrete example scenarios in full detail
- Write the honest downside/limitation in 1-2 sentences
- State the unique angle clearly

Be concrete and specific — this will be used as source material for an article.
If you're not certain about a specific statistic, say "many users report" instead
of inventing a fake precise number."""

    return _gemini(prompt, max_tokens=1000)


# ════════════════════════════════════════════════════════════
# STEP 3: DEEP DRAFT
# ════════════════════════════════════════════════════════════

def step3_deep_draft(topic: str, specifics: str, platform: str,
                      brand: str, audience: str) -> Optional[str]:
    """
    Teesra step — specifics + brand voice se actual draft banao.
    """
    logger.info(f"  ✍️  Step 3/4: Writing deep draft ({platform})")

    voice_ctx = build_voice_context()

    platform_specs = {
        "linkedin": "LinkedIn post: 900-1300 chars, hook in first 2 lines, line breaks every 2-3 lines, end with question + 5 hashtags. NO external links.",
        "medium":   "Medium article: 700-1000 words, SEO title + subtitle, subheadings every 150-200 words, specific examples in each section.",
        "twitter_thread": "Twitter thread: 8 tweets, each under 270 chars, tweet 1 = hook with 🧵, build narrative across tweets.",
    }
    spec = platform_specs.get(platform, platform_specs["linkedin"])

    prompt = f"""{voice_ctx}

Write a {spec}

Topic: {topic}
Audience: {audience}
Brand: {brand}

USE THIS RESEARCH (specific facts/examples — weave them in naturally):
{specifics}

CRITICAL RULES:
- Use the specific examples and numbers from the research above
- Include the honest downside/limitation mentioned in research
- Sound like a real person who tested this, not generic AI marketing
- Every claim needs a "because" or example attached

Return ONLY the final content."""

    return _gemini(prompt, max_tokens=1500)


# ════════════════════════════════════════════════════════════
# STEP 4: SELF-CRITIQUE + POLISH
# ════════════════════════════════════════════════════════════

def step4_critique_and_polish(draft: str, platform: str) -> Optional[str]:
    """
    Chautha step — AI khud apna kaam critique kare jaise editor karta hai.
    """
    logger.info(f"  🔍 Step 4/4: Self-critique + polish")

    voice_compliance = check_voice_compliance(draft)

    prompt = f"""You are a strict senior editor reviewing this {platform} draft:

{draft}

CRITIQUE CHECKLIST:
1. Does it sound like generic AI content or a real specific voice?
2. Are there any vague claims without specific backing? ("amazing", "game-changing" etc.)
3. Is there at least ONE genuinely useful, non-obvious insight?
4. Would a skeptical, experienced reader find this credible?
5. Brand voice issues found: {', '.join(voice_compliance['suggestions']) if voice_compliance['suggestions'] else 'None'}

Now REWRITE the draft fixing every issue you find. Make it sharper, more specific,
more credible. Cut any filler sentences. Keep the same length range.

Return ONLY the final polished version — no commentary."""

    polished = _gemini(prompt, max_tokens=1500)
    return polished if polished else draft


# ════════════════════════════════════════════════════════════
# FULL PIPELINE
# ════════════════════════════════════════════════════════════

def deep_research_generate(
    topic: str,
    platform: str = "linkedin",
    brand: str = None,
    audience: str = None,
    save_steps: bool = True,
) -> Result:
    """
    Full 4-step deep research pipeline.

    Args:
        topic:    Content topic
        platform: linkedin / medium / twitter_thread
        brand:    Brand name (default from config)
        audience: Target audience (default from config)
        save_steps: Saare intermediate steps generated/ mein save karo

    Returns:
        Result with final polished content + all intermediate steps
    """
    brand    = brand or cfg.BRAND_NAME
    audience = audience or cfg.AUDIENCE

    logger.info(f"🔬 Deep Research Mode: '{topic}' [{platform}]")
    logger.info(f"   (4-step process — takes longer but much higher quality)")

    steps = {}

    # Step 1
    outline = step1_research_outline(topic, audience)
    if not outline:
        return Result.fail("Step 1 (research outline) failed")
    steps["1_outline"] = outline
    time.sleep(1)

    # Step 2
    specifics = step2_specifics(topic, outline)
    if not specifics:
        return Result.fail("Step 2 (specifics) failed")
    steps["2_specifics"] = specifics
    time.sleep(1)

    # Step 3
    draft = step3_deep_draft(topic, specifics, platform, brand, audience)
    if not draft:
        return Result.fail("Step 3 (draft) failed")
    steps["3_draft"] = draft
    time.sleep(1)

    # Step 4
    final = step4_critique_and_polish(draft, platform)
    steps["4_final"] = final or draft

    # Voice compliance check
    compliance = check_voice_compliance(steps["4_final"])
    logger.info(f"   📊 Brand voice score: {compliance['voice_score']}/100 ({compliance['verdict']})")

    if save_steps:
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        safe_topic = re.sub(r'\W+', '_', topic[:30])
        out_dir = Path("generated/deep_research")
        out_dir.mkdir(parents=True, exist_ok=True)

        full_log = (
            f"TOPIC: {topic}\nPLATFORM: {platform}\n\n"
            f"{'='*50}\nSTEP 1 — RESEARCH OUTLINE\n{'='*50}\n{outline}\n\n"
            f"{'='*50}\nSTEP 2 — SPECIFICS\n{'='*50}\n{specifics}\n\n"
            f"{'='*50}\nSTEP 3 — DRAFT\n{'='*50}\n{draft}\n\n"
            f"{'='*50}\nSTEP 4 — FINAL POLISHED\n{'='*50}\n{steps['4_final']}\n\n"
            f"{'='*50}\nBRAND VOICE SCORE: {compliance['voice_score']}/100\n{'='*50}"
        )
        save_text(str(out_dir / f"{safe_topic}_{ts}_full_process.txt"), full_log)
        save_text(str(out_dir / f"{safe_topic}_{ts}_FINAL.txt"), steps["4_final"])
        logger.info(f"   💾 Saved: generated/deep_research/{safe_topic}_{ts}_FINAL.txt")

    logger.info(f"✅ Deep research complete!")

    return Result.success({
        "final":      steps["4_final"],
        "steps":      steps,
        "compliance": compliance,
    })


if __name__ == "__main__":
    print("=" * 55)
    print("🔬 TechNova World — Deep Research Mode v3.1")
    print("=" * 55)

    if not cfg.GEMINI_API_KEY:
        print("\n❌ config.py mein GEMINI_API_KEY set karo")
        exit(1)

    topic = input("\nTopic? (Enter=default): ").strip()
    if not topic:
        topic = "Why AI coding tools fail at debugging"

    platform = input("Platform (linkedin/medium/twitter_thread, Enter=linkedin): ").strip() or "linkedin"

    print(f"\n🔬 Starting 4-step deep research process...")
    print(f"   This takes longer (~30-60s) but produces much better content\n")

    result = deep_research_generate(topic, platform)

    if result:
        print(f"\n{'='*55}")
        print(f"✅ FINAL CONTENT:")
        print(f"{'='*55}")
        print(result.data["final"])
        print(f"\n📊 Brand voice: {result.data['compliance']['verdict']}")
    else:
        print(f"\n❌ Failed: {result.error}")
