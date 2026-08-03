"""
TechNova World — Brand Voice Engine v3.1

Defines TechNova World’s distinct writing identity and enforces it
across all AI-generated content.

Purpose:
  Leading brands (Anthropic, Google) maintain a consistent, recognisable voice
  because it is explicitly documented.  This module does the same for
  TechNova World — storing the voice configuration, scoring compliance,
  and injecting context strings into every generation prompt.
"""

import json
from pathlib import Path
from typing import Dict, List
from utils import logger, save_json, load_json


# ════════════════════════════════════════════════════════════
# DEFAULT BRAND VOICE — edit this to match YOUR actual voice
# ════════════════════════════════════════════════════════════

DEFAULT_VOICE = {
    "brand_name": "TechNova World",

    "personality": {
        "primary_trait":   "The honest senior engineer friend",
        "secondary_traits": ["Direct", "No-hype", "Practical", "Slightly skeptical of AI hype"],
        "avoid_being":     ["Salesy", "Overly hyped", "Corporate", "Vague"],
    },

    "tone_rules": {
        "formality":       "Casual-professional — like explaining to a smart friend",
        "confidence":       "Confident but admits uncertainty ('I think', 'in my experience')",
        "humor":            "Occasional dry humor, never forced",
        "emotion":          "Genuine enthusiasm for tools that ACTUALLY work, honest about ones that don't",
    },

    "signature_phrases": [
        "Here's what actually works:",
        "In my experience,",
        "The honest truth is",
        "Let's be real —",
        "Here's the thing nobody tells you:",
        "I tested this so you don't have to",
    ],

    "banned_phrases": [
        "game-changer", "revolutionize", "disrupt", "synergy",
        "leverage", "unlock the power of", "in today's fast-paced world",
        "I am excited to announce", "thrilled to share",
        "this is huge", "mind-blowing", "next-level",
    ],

    "vocabulary_level": "Plain English. Explain jargon when first used. Grade 8 reading level.",

    "content_principles": [
        "Always give a specific number or example, never vague claims",
        "If a tool has a downside, mention it — builds trust",
        "Compare to alternatives when relevant",
        "End with what reader should DO, not just think about",
        "Never claim something is '#1' or 'the best' without comparison data",
    ],

    "structural_preferences": {
        "opening_style":  "Start with a specific moment/problem, not a general statement",
        "use_of_lists":   "Yes — but each item needs 1 concrete detail, not just a label",
        "use_of_data":    "Always — even rough numbers beat vague claims",
        "closing_style":  "Specific next action + genuine question",
    },

    "example_good": (
        "I spent 4 hours last week debugging code ChatGPT wrote. "
        "Here's the thing nobody tells you: AI is great at the first 80% "
        "and terrible at the last 20%. That's exactly the part that matters."
    ),

    "example_bad": (
        "AI is revolutionizing the way we work! This game-changing technology "
        "is unlocking new levels of productivity for everyone in today's fast-paced world."
    ),
}

VOICE_FILE = "assets/brand_voice.json"


# ════════════════════════════════════════════════════════════
# VOICE MANAGEMENT
# ════════════════════════════════════════════════════════════

def load_voice() -> Dict:
    """Load the saved brand voice configuration, or return the default if none exists."""
    voice = load_json(VOICE_FILE, default=None)
    if voice:
        return voice
    save_voice(DEFAULT_VOICE)
    return DEFAULT_VOICE


def save_voice(voice: Dict) -> bool:
    """Persist the brand voice configuration to disk."""
    Path("assets").mkdir(exist_ok=True)
    ok = save_json(VOICE_FILE, voice)
    if ok:
        logger.info("✅ Brand voice saved")
    return ok


def update_voice_field(path: str, value) -> bool:
    """
    Update a nested field inside the brand voice configuration.

    Example:
        update_voice_field("banned_phrases", ["new phrase"])
    """
    voice = load_voice()
    keys = path.split(".")
    target = voice
    for k in keys[:-1]:
        target = target.setdefault(k, {})
    target[keys[-1]] = value
    return save_voice(voice)


def add_signature_phrase(phrase: str) -> bool:
    """Append a new signature phrase to the brand voice configuration."""
    voice = load_voice()
    if phrase not in voice["signature_phrases"]:
        voice["signature_phrases"].append(phrase)
        return save_voice(voice)
    return True


def add_banned_phrase(phrase: str) -> bool:
    """Append a new banned phrase to the brand voice configuration."""
    voice = load_voice()
    if phrase not in voice["banned_phrases"]:
        voice["banned_phrases"].append(phrase)
        return save_voice(voice)
    return True


# ════════════════════════════════════════════════════════════
# VOICE PROMPT INJECTION
# ════════════════════════════════════════════════════════════

def build_voice_context() -> str:
    """
    Serialise the brand voice configuration into a prompt-ready string.

    The returned string is injected into every content-generation prompt
    so the AI respects tone, banned phrases, and content principles.
    """
    v = load_voice()

    banned = ", ".join(v["banned_phrases"][:10])
    sigs   = "\n".join(f"  - {p}" for p in v["signature_phrases"][:4])
    principles = "\n".join(f"  - {p}" for p in v["content_principles"])

    return f"""BRAND VOICE — {v['brand_name']} (follow strictly):

Personality: {v['personality']['primary_trait']}
Traits: {', '.join(v['personality']['secondary_traits'])}
NEVER sound: {', '.join(v['personality']['avoid_being'])}

Tone: {v['tone_rules']['formality']}
Confidence: {v['tone_rules']['confidence']}

BANNED WORDS/PHRASES (never use these — they sound like generic AI marketing):
{banned}

Use phrases LIKE these (not verbatim every time, but this energy):
{sigs}

Content Principles:
{principles}

Vocabulary: {v['vocabulary_level']}

GOOD EXAMPLE TONE:
"{v['example_good']}"

BAD EXAMPLE (never write like this):
"{v['example_bad']}"
"""


def check_voice_compliance(text: str) -> Dict:
    """
    Evaluate whether generated content adheres to the brand voice guidelines.

    Returns a dict with:
      voice_score  — 0-100 compliance score
      violations   — list of banned phrases found in the text
      vague_claims — list of unsubstantiated superlative claims found
      has_number   — whether a specific number is present (credibility signal)
      suggestions  — human-readable list of fixes
      verdict      — emoji-prefixed summary string
    """
    v = load_voice()
    text_lower = text.lower()

    violations = [p for p in v["banned_phrases"] if p.lower() in text_lower]

    has_specific_number = any(c.isdigit() for c in text)
    has_signature_energy = any(
        p.lower()[:15] in text_lower for p in v["signature_phrases"]
    )

    # Vague claim detector
    vague_claims = ["best ai tool", "#1 tool", "amazing results", "incredible",
                    "game-changing", "revolutionary"]
    vague_found = [c for c in vague_claims if c in text_lower]

    score = 100
    score -= len(violations) * 15
    score -= len(vague_found) * 10
    if not has_specific_number:
        score -= 15
    score = max(0, score)

    suggestions = []
    if violations:
        suggestions.append(f"Remove banned phrases: {', '.join(violations)}")
    if vague_found:
        suggestions.append(f"Replace vague claims with specifics: {', '.join(vague_found)}")
    if not has_specific_number:
        suggestions.append("Add a specific number, stat, or timeframe — builds credibility")

    return {
        "voice_score":  score,
        "violations":   violations,
        "vague_claims": vague_found,
        "has_number":   has_specific_number,
        "suggestions":  suggestions,
        "verdict": (
            "🟢 On-brand"        if score >= 80 else
            "🟡 Needs polish"    if score >= 50 else
            "🔴 Off-brand — rewrite"
        ),
    }


def rewrite_in_brand_voice(text: str, gemini_fn) -> str:
    """
    Rewrite generic content to conform to the TechNova World brand voice.

    Args:
        text:       The original draft content to rewrite.
        gemini_fn:  Any callable that accepts a prompt string and returns text
                    (e.g. ``ai_generator._gemini`` or ``ai_client.generate_text``).

    Returns:
        The rewritten content string, or the original text if the AI call fails.
    """
    voice_ctx = build_voice_context()
    compliance = check_voice_compliance(text)

    prompt = f"""{voice_ctx}

Rewrite this content to match the brand voice above. Keep the same core message
and information, but change the TONE, remove banned phrases, and add specificity.

ISSUES IN CURRENT DRAFT:
{chr(10).join('- ' + s for s in compliance['suggestions'])}

CURRENT DRAFT:
{text}

Return ONLY the rewritten version."""

    result = gemini_fn(prompt)
    return result if result else text


# ════════════════════════════════════════════════════════════
# CLI — Voice Setup Wizard
# ════════════════════════════════════════════════════════════

def voice_setup_wizard():
    """Interactive wizard — TechNova World ki voice define karo."""
    print("\n" + "="*55)
    print("  🎙️  Brand Voice Setup — TechNova World")
    print("="*55)
    print("\n  Yeh wizard tumhari brand ki UNIQUE voice define karega.")
    print("  Jitna specific jawab doge, utna better content milega.\n")

    voice = load_voice()

    print(f"  Current personality: {voice['personality']['primary_trait']}")
    new_trait = input("  Naya primary trait (Enter = keep current): ").strip()
    if new_trait:
        voice["personality"]["primary_trait"] = new_trait

    print(f"\n  Current banned phrases: {', '.join(voice['banned_phrases'][:5])}...")
    new_banned = input("  Aur konsi phrases ban karni hain? (comma-separated, Enter=skip): ").strip()
    if new_banned:
        new_list = [p.strip() for p in new_banned.split(",")]
        voice["banned_phrases"].extend(new_list)

    print(f"\n  Current signature style:")
    for p in voice["signature_phrases"][:3]:
        print(f"    - {p}")
    new_sig = input("  Naya signature phrase add karna hai? (Enter=skip): ").strip()
    if new_sig:
        voice["signature_phrases"].append(new_sig)

    save_voice(voice)
    print("\n  ✅ Brand voice updated! Saved to assets/brand_voice.json")
    print("  Ab har generated post is voice ko follow karega.\n")


if __name__ == "__main__":
    voice_setup_wizard()
