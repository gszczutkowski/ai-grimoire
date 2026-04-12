#!/usr/bin/env python3
"""Generate handwriting practice PDF pages for children.

Layout: A4 page with a readable story at the top, then each word
on a separate line with Polish three-line handwriting guidelines.
"""

import sys
import os
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# Auto-install dependencies
for pkg, import_name in [("fpdf2", "fpdf")]:
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

from fpdf import FPDF

SCRIPT_DIR = Path(__file__).parent
FONT_DIR = SCRIPT_DIR / "fonts"

# ElementarzDwa - Polish school handwriting font
FONT_FILE = "ElementarzDwa-Regular.ttf"


def ensure_font():
    """Ensure the handwriting font is available."""
    FONT_DIR.mkdir(exist_ok=True)
    font_path = FONT_DIR / FONT_FILE
    if not font_path.exists():
        # Try to copy from Windows user fonts
        import shutil
        win_font = Path(os.environ.get("USERPROFILE", "")) / "AppData/Local/Microsoft/Windows/Fonts/ElementarzDwa Regular.ttf"
        if win_font.exists():
            shutil.copy2(win_font, font_path)
            print(f"Font copied from {win_font}")
        else:
            print(f"ERROR: {FONT_FILE} not found. Please place it in {FONT_DIR}")
            sys.exit(1)
    return str(font_path)


def draw_dashed_line(pdf, x1, y, x2, dash=2, gap=2):
    """Draw a horizontal dashed line."""
    x = x1
    while x < x2:
        end_x = min(x + dash, x2)
        pdf.line(x, y, end_x, y)
        x += dash + gap


def generate_pdf(words, story, size, output_dir="."):
    """Generate the handwriting practice PDF."""
    font_path = ensure_font()

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # Page dimensions — margins minimised for EPSON L3150 (3mm printable area)
    page_w = 210
    margin_x = 3
    margin_top = 3
    margin_bottom = 3
    usable_w = page_w - 2 * margin_x

    # Register handwriting font
    pdf.add_font("Handwriting", "", font_path)

    # --- Header: Story text (readable, using handwriting font for Polish support) ---
    pdf.set_font("Handwriting", "", 11)
    pdf.set_xy(margin_x, margin_top)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(usable_w, 6, story, align="L")

    # Separator line
    story_bottom = pdf.get_y() + 4
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.2)
    pdf.line(margin_x, story_bottom, page_w - margin_x, story_bottom)

    y_start = story_bottom + 6

    # --- Practice zone parameters ---
    # ElementarzDwa font metrics (unitsPerEm=2048):
    #   x-height (top of 'a','e','o') ≈ 800 units
    #   cap-height (top of 'A','B','H') ≈ 1610 units
    #   descender (bottom of 'g','p') ≈ -700 units
    #
    # Three-line system (bottom to top):
    #   Line 1 (bottom) - baseline: where the bottom of letters sits
    #   Line 2 (middle) - x-height: top of lowercase letters
    #   Line 3 (top) - cap-height: top of capital letters
    #
    # With line_gap=5mm, cap-height spans ~10mm (2 gaps), x-height spans ~5mm (1 gap).
    # Font size calibrated so x-height = 5mm: 36pt
    line_gap = 5        # 5mm between each of the 3 guidelines
    zone_h = 10         # 3 lines span 10mm (top to bottom)
    between_rows = 5    # 5mm from baseline of one row to top line of next row
    row_h = zone_h + between_rows  # 15mm from top line to top line

    # Colors
    color_solid = (170, 170, 170)
    color_dashed = (200, 200, 200)
    color_text = (60, 60, 60)

    # Font size: target x-height = 5mm (one line_gap).
    # ElementarzDwa x-height = 800/2048 of em.
    # 36pt * (800/2048) * (25.4/72) ≈ 4.96mm ≈ 5mm
    practice_font_size = 36

    # Maximum content area based on page size mode
    if size == "half":
        max_y = 297 / 2
    else:
        max_y = 297 - margin_bottom

    # First pass: attach standalone punctuation to the preceding word.
    # E.g. ["serca", ",", "niebieską"] → ["serca,", "niebieską"]
    punct_chars = set(".,!?;:…–-")
    cleaned = []
    for w in words:
        if w and all(ch in punct_chars for ch in w) and cleaned:
            cleaned[-1] += w
        else:
            cleaned.append(w)
    words = cleaned

    # Merge single-letter words (i, z, w, a, o, etc.) with the following word
    # so they share one practice line instead of wasting a line on one letter.
    merged = []
    i = 0
    while i < len(words):
        if len(words[i]) == 1 and i + 1 < len(words):
            merged.append(words[i] + " " + words[i + 1])
            i += 2
        else:
            merged.append(words[i])
            i += 1

    for i, word in enumerate(merged):
        y_top = y_start + i * row_h  # top line (cap-height)

        # Stop only at the absolute page bottom (always render all words)
        if y_top + zone_h > 297 - margin_bottom:
            break

        y_middle = y_top + line_gap        # x-height line
        y_bottom = y_top + 2 * line_gap    # baseline

        # Line 3 (top) - solid: cap-height (top of capital letters)
        pdf.set_draw_color(*color_solid)
        pdf.set_line_width(0.3)
        pdf.line(margin_x, y_top, page_w - margin_x, y_top)

        # Line 2 (middle) - dashed: x-height (top of lowercase letters)
        pdf.set_draw_color(*color_dashed)
        pdf.set_line_width(0.2)
        draw_dashed_line(pdf, margin_x, y_middle, page_w - margin_x)

        # Line 1 (bottom) - solid: baseline (where letters sit)
        pdf.set_draw_color(*color_solid)
        pdf.set_line_width(0.3)
        pdf.line(margin_x, y_bottom, page_w - margin_x, y_bottom)

        # Write the word: baseline aligned with Line 1 (bottom line)
        pdf.set_font("Handwriting", "", practice_font_size)
        pdf.set_text_color(*color_text)

        # pdf.text() places text with baseline at the given y coordinate
        pdf.text(margin_x + 2, y_bottom, word)

    # Save PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"handwriting_practice_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)
    pdf.output(filepath)

    return filepath


def main():
    parser = argparse.ArgumentParser(description="Generate handwriting practice PDF")
    parser.add_argument("--size", choices=["half", "full"], default="full")
    parser.add_argument(
        "--words", required=True, help="Comma-separated list of words"
    )
    parser.add_argument("--story", required=True, help="Full story/fact text")
    parser.add_argument("--output-dir", default=".", help="Output directory")

    args = parser.parse_args()

    words = [w.strip() for w in args.words.split(",") if w.strip()]

    filepath = generate_pdf(words, args.story, args.size, args.output_dir)
    print(f"PDF generated: {filepath}")


if __name__ == "__main__":
    main()
