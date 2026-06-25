"""
TechNova World — PDF Carousel Generator v2.0
LinkedIn ke liye professional carousel PDF banata hai
ReportLab library use karta hai (free)

Install: pip install reportlab
"""

import os
import re
import textwrap
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.colors import (
        HexColor, white, black, Color
    )
    from reportlab.lib.units import mm, cm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import Paragraph
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

from utils import logger, retry, Result, save_text
import config as cfg

# ── BRAND COLORS ─────────────────────────────────────────────
C_BG        = HexColor("#04080f")   # dark background
C_CARD      = HexColor("#0a1220")   # card background
C_ACCENT    = HexColor("#2563eb")   # blue accent
C_ACCENT2   = HexColor("#8b5cf6")   # purple accent
C_GREEN     = HexColor("#10b981")   # green
C_AMBER     = HexColor("#f59e0b")   # amber
C_TEXT      = HexColor("#e1eaf8")   # light text
C_TEXT2     = HexColor("#6e8fb0")   # muted text
C_BORDER    = HexColor("#1c2d45")   # border

# ── SLIDE SIZE (LinkedIn square) ─────────────────────────────
SLIDE_W = 1080
SLIDE_H = 1080
SCALE   = 0.4   # reportlab units

W = SLIDE_W * SCALE / 2.835   # mm
H = SLIDE_H * SCALE / 2.835   # mm

# ── AI CALL — routed through unified ai_client (Gemini 2.5 + OpenRouter) ──
from ai_client import generate_text as _gemini



# ── SLIDE DATA GENERATOR ─────────────────────────────────────

def generate_carousel_content(topic: str, slide_count: int = 8) -> Result:
    """
    Gemini se carousel content generate karo

    Returns list of slide dicts:
    [{"slide_num": 1, "type": "cover", "title": ..., "subtitle": ..., "points": [...]}, ...]
    """
    if not cfg.GEMINI_API_KEY:
        return Result.fail("GEMINI_API_KEY config.py mein set karo")

    prompt = f"""Create a LinkedIn carousel PDF for TechNova World about: "{topic}"
Audience: {cfg.AUDIENCE}

Generate exactly {slide_count} slides in this JSON format:

[
  {{
    "slide_num": 1,
    "type": "cover",
    "title": "Eye-catching title (max 8 words)",
    "subtitle": "Compelling subtitle (max 12 words)",
    "emoji": "🚀"
  }},
  {{
    "slide_num": 2,
    "type": "problem",
    "title": "The Problem / Hook",
    "points": ["Point 1 (max 10 words)", "Point 2", "Point 3"],
    "emoji": "❓"
  }},
  {{
    "slide_num": 3,
    "type": "content",
    "title": "Section title",
    "points": ["Key insight 1", "Key insight 2", "Key insight 3"],
    "emoji": "💡"
  }},
  ... (slides 4-7 same as slide 3 but different content)
  {{
    "slide_num": {slide_count},
    "type": "cta",
    "title": "Follow TechNova World",
    "subtitle": "For daily AI insights",
    "cta_text": "Follow + Share this carousel!",
    "emoji": "🌐"
  }}
]

Rules:
- Each point max 12 words (must fit in slide)
- Titles max 8 words
- Educational, simple language
- No jargon
- Return ONLY valid JSON array, nothing else"""

    try:
        raw = _gemini(prompt)
        if raw is None:
            return Result.fail("AI generation failed (all providers exhausted)")
        # Extract JSON from response
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"```[a-z]*\n?", "", raw).strip()

        # Try parse
        import json
        slides = json.loads(raw)

        if not isinstance(slides, list) or len(slides) < 3:
            return Result.fail("Invalid slide data from Gemini")

        logger.info(f"✅ {len(slides)} slides generated for: {topic}")
        return Result.success(slides)

    except Exception as e:
        logger.error(f"Carousel content generation failed: {e}")
        # Fallback: plain text parse
        return _parse_plain_carousel(raw if 'raw' in dir() else "", topic, slide_count)


def _parse_plain_carousel(text: str, topic: str, count: int) -> Result:
    """Fallback — plain text se basic slides banao"""
    logger.warning("⚠️  JSON parse failed — fallback slide structure use kar raha hoon")
    slides = [
        {"slide_num": 1, "type": "cover", "title": topic[:40], "subtitle": f"A TechNova World guide", "emoji": "🚀"},
    ]
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 10]
    chunk = max(1, len(lines) // (count - 2))
    for i in range(2, count):
        chunk_lines = lines[(i-2)*chunk:(i-1)*chunk] or [f"Key insight {i}"]
        slides.append({
            "slide_num": i,
            "type": "content",
            "title": f"Point {i-1}",
            "points": [l[:60] for l in chunk_lines[:3]],
            "emoji": ["💡","🔑","📊","⚡","🎯","✅"][i % 6]
        })
    slides.append({"slide_num": count, "type": "cta", "title": "Follow TechNova World",
                   "subtitle": "Daily AI insights", "cta_text": "Follow + Share!", "emoji": "🌐"})
    return Result.success(slides)


# ── PDF RENDERER ─────────────────────────────────────────────

def _draw_rounded_rect(c, x, y, w, h, r, fill_color, stroke_color=None):
    """Rounded rectangle draw karo"""
    c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(0.5)
    else:
        c.setStrokeColor(fill_color)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1 if stroke_color else 0)


def _draw_gradient_bg(c, w, h):
    """Dark gradient background"""
    c.setFillColor(C_BG)
    c.rect(0, 0, w, h, fill=1, stroke=0)
    # Subtle accent glow top-left
    glow = Color(0.15, 0.39, 0.92, alpha=0.08)
    c.setFillColor(glow)
    c.circle(w * 0.15, h * 0.85, w * 0.4, fill=1, stroke=0)


def _draw_slide_num(c, num, total, w, h):
    """Slide number badge"""
    badge_text = f"{num} / {total}"
    c.setFillColor(C_BORDER)
    c.roundRect(w - 22*mm, h - 10*mm, 20*mm, 7*mm, 2*mm, fill=1, stroke=0)
    c.setFillColor(C_TEXT2)
    c.setFont("Helvetica", 8)
    c.drawCentredString(w - 12*mm, h - 7.5*mm, badge_text)


def _draw_brand_footer(c, w):
    """Brand watermark footer"""
    c.setFillColor(C_TEXT2)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(8*mm, 6*mm, f"🌐 {cfg.BRAND_NAME}")
    c.setFont("Helvetica", 6)
    c.drawRightString(w - 8*mm, 6*mm, "Follow for daily AI insights")


def _draw_cover_slide(c, slide: dict, w, h):
    """Cover slide render karo"""
    _draw_gradient_bg(c, w, h)

    # Accent bar top
    c.setFillColor(C_ACCENT)
    c.rect(0, h - 3*mm, w, 3*mm, fill=1, stroke=0)

    # Big emoji
    c.setFont("Helvetica-Bold", 48)
    c.setFillColor(white)
    emoji = slide.get("emoji", "🚀")
    c.drawCentredString(w/2, h * 0.62, emoji)

    # Title
    title = slide.get("title", cfg.BRAND_NAME)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 22)
    # Word wrap if long
    if len(title) > 30:
        words = title.split()
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        c.drawCentredString(w/2, h * 0.50, line1)
        c.drawCentredString(w/2, h * 0.44, line2)
    else:
        c.drawCentredString(w/2, h * 0.50, title)

    # Subtitle
    subtitle = slide.get("subtitle", "")
    if subtitle:
        c.setFillColor(C_TEXT2)
        c.setFont("Helvetica", 12)
        c.drawCentredString(w/2, h * 0.37, subtitle)

    # Brand badge
    badge_w = 50*mm
    badge_x = (w - badge_w) / 2
    _draw_rounded_rect(c, badge_x, h * 0.18, badge_w, 10*mm, 2*mm, C_ACCENT)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(w/2, h * 0.195, f"🌐 {cfg.BRAND_NAME}")

    _draw_slide_num(c, slide.get("slide_num", 1), slide.get("_total", 8), w, h)


def _draw_content_slide(c, slide: dict, w, h):
    """Content slide render karo"""
    _draw_gradient_bg(c, w, h)

    # Top accent line
    c.setFillColor(C_ACCENT)
    c.rect(0, h - 2*mm, w, 2*mm, fill=1, stroke=0)

    # Emoji
    emoji = slide.get("emoji", "💡")
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(white)
    c.drawString(8*mm, h - 22*mm, emoji)

    # Title
    title = slide.get("title", "Key Insight")
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(8*mm, h - 33*mm, title[:45])

    # Divider line
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.5)
    c.line(8*mm, h - 36*mm, w - 8*mm, h - 36*mm)

    # Points / bullets
    points = slide.get("points", [])
    y_start = h - 45*mm
    y_step  = 18*mm

    for i, point in enumerate(points[:4]):
        y = y_start - (i * y_step)
        if y < 18*mm:
            break

        # Bullet card
        _draw_rounded_rect(c, 8*mm, y - 12*mm, w - 16*mm, 13*mm, 2*mm, C_CARD)
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.3)
        c.roundRect(8*mm, y - 12*mm, w - 16*mm, 13*mm, 2*mm, fill=0, stroke=1)

        # Bullet dot
        c.setFillColor(C_ACCENT)
        c.circle(16*mm, y - 5.5*mm, 1.5*mm, fill=1, stroke=0)

        # Bullet text
        c.setFillColor(C_TEXT)
        c.setFont("Helvetica", 11)
        wrapped = point[:65]
        c.drawString(20*mm, y - 7*mm, wrapped)

    _draw_brand_footer(c, w)
    _draw_slide_num(c, slide.get("slide_num", 2), slide.get("_total", 8), w, h)


def _draw_cta_slide(c, slide: dict, w, h):
    """CTA / last slide render karo"""
    _draw_gradient_bg(c, w, h)

    # Gradient accent circle bg
    c.setFillColor(Color(0.15, 0.39, 0.92, alpha=0.12))
    c.circle(w/2, h/2, w * 0.55, fill=1, stroke=0)

    # Top bar
    c.setFillColor(C_ACCENT)
    c.rect(0, h - 2*mm, w, 2*mm, fill=1, stroke=0)

    # Emoji
    c.setFont("Helvetica-Bold", 42)
    c.setFillColor(white)
    c.drawCentredString(w/2, h * 0.64, slide.get("emoji", "🌐"))

    # Title
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(white)
    c.drawCentredString(w/2, h * 0.53, slide.get("title", "Follow TechNova World"))

    # Subtitle
    c.setFont("Helvetica", 13)
    c.setFillColor(C_TEXT2)
    c.drawCentredString(w/2, h * 0.46, slide.get("subtitle", "Daily AI insights"))

    # CTA Button
    cta = slide.get("cta_text", "Follow + Share!")
    btn_w = 70*mm
    btn_x = (w - btn_w) / 2
    _draw_rounded_rect(c, btn_x, h * 0.33, btn_w, 12*mm, 3*mm, C_GREEN)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(w/2, h * 0.355, cta)

    # Hashtags
    c.setFillColor(C_TEXT2)
    c.setFont("Helvetica", 9)
    tags = "#AI  #ArtificialIntelligence  #AITools  #TechNova"
    c.drawCentredString(w/2, h * 0.26, tags)

    _draw_brand_footer(c, w)
    _draw_slide_num(c, slide.get("slide_num", 8), slide.get("_total", 8), w, h)


def render_carousel_pdf(slides: List[Dict], output_path: str) -> Result:
    """
    Slides list se PDF generate karo

    Args:
        slides: List of slide dicts from generate_carousel_content()
        output_path: Output .pdf file path

    Returns:
        Result with file path
    """
    if not REPORTLAB_OK:
        return Result.fail(
            "ReportLab install nahi hai! Run karo: pip install reportlab"
        )

    if not slides:
        return Result.fail("Slides list empty hai")

    total = len(slides)

    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        c = rl_canvas.Canvas(output_path, pagesize=(W*mm, H*mm))
        # Convert W,H from mm to points for canvas
        pw = W * mm
        ph = H * mm

        # Re-define in points (reportlab default unit)
        PW = W * 2.835  # points
        PH = H * 2.835

        # Recreate with correct page size in points
        c = rl_canvas.Canvas(output_path, pagesize=(PW, PH))

        for i, slide in enumerate(slides):
            slide["_total"] = total
            slide_type = slide.get("type", "content")

            if slide_type == "cover":
                _draw_cover_slide(c, slide, PW, PH)
            elif slide_type == "cta":
                _draw_cta_slide(c, slide, PW, PH)
            else:
                _draw_content_slide(c, slide, PW, PH)

            if i < len(slides) - 1:
                c.showPage()

        c.save()
        size_kb = Path(output_path).stat().st_size // 1024
        logger.info(f"✅ PDF carousel saved: {output_path} ({size_kb} KB, {total} slides)")
        return Result.success(output_path)

    except Exception as e:
        logger.error(f"❌ PDF render failed: {e}")
        return Result.fail(str(e))


# ── HIGH-LEVEL FUNCTION ───────────────────────────────────────

def create_linkedin_carousel(topic: str, slide_count: int = 8,
                              output_dir: str = "generated") -> Result:
    """
    Topic se complete LinkedIn carousel PDF banao

    Args:
        topic: Carousel ka topic
        slide_count: Number of slides (default 8)
        output_dir: Output folder

    Returns:
        Result with PDF file path
    """
    logger.info(f"🎨 LinkedIn carousel banao: '{topic}' ({slide_count} slides)")

    # Step 1: Content generate karo
    content_result = generate_carousel_content(topic, slide_count)
    if not content_result:
        return content_result

    slides = content_result.data

    # Step 2: PDF render karo
    filename = f"carousel_{topic[:30].replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    output_path = str(Path(output_dir) / filename)

    pdf_result = render_carousel_pdf(slides, output_path)
    if not pdf_result:
        return pdf_result

    # Step 3: Text version bhi save karo (for reference)
    text_content = f"LINKEDIN CAROUSEL: {topic}\n"
    text_content += "=" * 50 + "\n\n"
    for slide in slides:
        text_content += f"SLIDE {slide['slide_num']}: {slide.get('title','')}\n"
        for p in slide.get("points", []):
            text_content += f"  • {p}\n"
        text_content += "\n"

    text_path = output_path.replace(".pdf", "_outline.txt")
    save_text(text_path, text_content)

    logger.info(f"✅ Carousel ready: {pdf_result.data}")
    logger.info(f"📄 Outline: {text_path}")

    return Result.success({
        "pdf": pdf_result.data,
        "outline": text_path,
        "slides": slides
    })


if __name__ == "__main__":
    print("=" * 55)
    print("🎨 TechNova World — PDF Carousel Generator Test")
    print("=" * 55)

    if not REPORTLAB_OK:
        print("❌ ReportLab install karo: pip install reportlab")
        exit(1)

    if not cfg.GEMINI_API_KEY:
        print("❌ config.py mein GEMINI_API_KEY set karo")
        exit(1)

    topic = input("\nCarousel topic kya hai? (Enter = default): ").strip()
    if not topic:
        topic = "5 AI Tools That Will Replace Your Entire Workflow"

    result = create_linkedin_carousel(topic, slide_count=8)

    if result:
        print(f"\n✅ SUCCESS!")
        print(f"   PDF: {result.data['pdf']}")
        print(f"   Outline: {result.data['outline']}")
        print(f"\nLinkedIn pe is PDF ko carousel ke roop mein upload karo!")
    else:
        print(f"\n❌ Failed: {result.error}")
