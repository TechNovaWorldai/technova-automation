"""
TechNova World — Image Watermark v2.0
Pillow se images pe watermark lagata hai
Proper error handling + batch support

Install: pip install Pillow
Usage:
  Single:  python watermark.py image.jpg
  Batch:   python watermark.py images/
"""

import sys
import os
from pathlib import Path
from typing import Optional, List
from utils import logger, Result
import config as cfg

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False


FONT_PATHS_WIN = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/verdanab.ttf",
]
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _check_pillow():
    if not PILLOW_OK:
        logger.error("Pillow install nahi hai! Run: pip install Pillow")
        return False
    return True


def _load_font(size: int) -> "ImageFont":
    for path in FONT_PATHS_WIN:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    logger.warning("System font nahi mila — default use ho raha hai")
    return ImageFont.load_default()


def _get_position(pos: str, img_w, img_h, badge_w, badge_h, margin=12):
    positions = {
        "bottom_right": (img_w - badge_w - margin, img_h - badge_h - margin),
        "bottom_left":  (margin, img_h - badge_h - margin),
        "top_right":    (img_w - badge_w - margin, margin),
        "top_left":     (margin, margin),
        "center":       ((img_w - badge_w) // 2, (img_h - badge_h) // 2),
    }
    return positions.get(pos, positions["bottom_right"])


def add_watermark(
    image_path: str,
    output_path: str = None,
    text: str = None,
    position: str = None,
    opacity: int = 180,
    font_size: int = None,
    text_color: tuple = (255, 255, 255),
    bg_color: tuple = (0, 0, 0),
    bg_alpha: int = 140,
) -> Optional[str]:
    """
    Image pe watermark lagao.

    Returns output path on success, None on failure.
    """
    if not _check_pillow():
        return None

    text     = text     or cfg.WATERMARK_TEXT
    position = position or cfg.WATERMARK_POSITION

    # Validate input
    if not Path(image_path).exists():
        logger.error(f"Image nahi mili: {image_path}")
        return None

    if Path(image_path).suffix.lower() not in SUPPORTED_FORMATS:
        logger.error(f"Unsupported format: {image_path}")
        return None

    try:
        img = Image.open(image_path).convert("RGBA")
    except Exception as e:
        logger.error(f"Image open failed ({image_path}): {e}")
        return None

    w, h = img.size

    # Auto font size
    if font_size is None:
        font_size = max(14, int(min(w, h) * 0.042))

    font   = _load_font(font_size)
    pad_x  = int(font_size * 0.65)
    pad_y  = int(font_size * 0.38)

    # Measure text
    dummy = Image.new("RGBA", (1, 1))
    dd    = ImageDraw.Draw(dummy)
    bbox  = dd.textbbox((0, 0), text, font=font)
    tw    = bbox[2] - bbox[0]
    th    = bbox[3] - bbox[1]

    badge_w = tw + pad_x * 2
    badge_h = th + pad_y * 2
    x, y    = _get_position(position, w, h, badge_w, badge_h)

    # Draw on transparent layer
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw  = ImageDraw.Draw(layer)

    # Background badge
    radius = int(badge_h * 0.3)
    try:
        draw.rounded_rectangle(
            [x, y, x + badge_w, y + badge_h],
            radius=radius,
            fill=(*bg_color, bg_alpha),
        )
    except AttributeError:
        # Pillow < 8.2 fallback
        draw.rectangle([x, y, x + badge_w, y + badge_h], fill=(*bg_color, bg_alpha))

    # Text
    draw.text(
        (x + pad_x, y + pad_y),
        text,
        font=font,
        fill=(*text_color, opacity),
    )

    # Composite + save
    result_img = Image.alpha_composite(img, layer).convert("RGB")

    if output_path is None:
        p = Path(image_path)
        output_path = str(p.parent / f"{p.stem}_wm{p.suffix}")

    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        result_img.save(output_path, quality=95)
        logger.info(f"✅ Watermarked: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Save failed ({output_path}): {e}")
        return None


def batch_watermark(
    folder_path: str,
    output_folder: str = None,
    text: str = None,
    position: str = None,
) -> List[str]:
    """
    Folder ke saare images watermark karo.

    Returns list of successfully watermarked file paths.
    """
    if not _check_pillow():
        return []

    folder = Path(folder_path)
    if not folder.exists():
        logger.error(f"Folder nahi mili: {folder_path}")
        return []

    out_dir = Path(output_folder) if output_folder else folder / "watermarked"
    out_dir.mkdir(parents=True, exist_ok=True)

    images  = [f for f in folder.iterdir() if f.suffix.lower() in SUPPORTED_FORMATS]
    total   = len(images)

    if total == 0:
        logger.warning(f"Koi supported image nahi mili: {folder_path}")
        return []

    logger.info(f"🖼️  Batch watermark: {total} images in {folder_path}")
    results = []

    for i, img_path in enumerate(sorted(images), 1):
        out = str(out_dir / img_path.name)
        r   = add_watermark(str(img_path), out, text=text, position=position)
        if r:
            results.append(r)
        # Progress
        pct = int(100 * i / total)
        print(f"\r  Progress: [{('█'*int(pct/4)):25s}] {pct}% ({i}/{total})", end="")

    print()  # newline after progress bar
    logger.info(f"✅ Batch done: {len(results)}/{total} watermarked → {out_dir}")
    return results


def watermark_for_platform(image_path: str, platform: str = "linkedin") -> Optional[str]:
    """Platform-specific settings ke saath watermark karo."""
    settings = {
        "linkedin": {"font_size": 26, "position": "bottom_right", "opacity": 200},
        "twitter":  {"font_size": 20, "position": "bottom_right", "opacity": 170},
        "medium":   {"font_size": 22, "position": "bottom_right", "opacity": 185},
    }
    s = settings.get(platform, settings["linkedin"])
    p = Path(image_path)
    out = str(p.parent / f"{p.stem}_{platform}_wm{p.suffix}")
    return add_watermark(image_path, out, **s)


if __name__ == "__main__":
    if not PILLOW_OK:
        print("❌ Pillow install karo: pip install Pillow")
        sys.exit(1)

    print("=" * 50)
    print("🖼️  TechNova World — Watermark Tool v2.0")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python watermark.py photo.jpg")
        print("  python watermark.py images/")
        print("  python watermark.py photo.jpg twitter")
        sys.exit(0)

    path     = sys.argv[1]
    platform = sys.argv[2] if len(sys.argv) > 2 else None

    if os.path.isdir(path):
        batch_watermark(path)
    elif os.path.isfile(path):
        if platform:
            watermark_for_platform(path, platform)
        else:
            add_watermark(path)
    else:
        print(f"❌ File/folder nahi mila: {path}")
