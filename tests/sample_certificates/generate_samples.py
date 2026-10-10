"""
Generates 5 visually distinct, professionally laid-out sample certificate
images for testing the OCR pipeline. Run once with:

    python generate_samples.py

Each certificate uses a different design theme and slightly different text
layout on purpose, so the extraction engine (app/core/extractor.py) can be
demonstrated against varied real-world-like formats rather than one
template. All fonts used are open-source system fonts (DejaVu / Liberation
/ FreeFont), and all names/organizations are fictional.
"""

import os
from PIL import Image, ImageDraw, ImageFont

FONT_DIR_DEJAVU = "/usr/share/fonts/truetype/dejavu"
FONT_DIR_LIBERATION = "/usr/share/fonts/truetype/liberation"
FONT_DIR_FREEFONT = "/usr/share/fonts/truetype/freefont"

W, H = 1600, 1131  # A4-ish landscape at ~150dpi

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def font(path, size):
    return ImageFont.truetype(path, size)


def center_text(draw, text, y, f, fill, canvas_w=W):
    bbox = draw.textbbox((0, 0), text, font=f)
    w = bbox[2] - bbox[0]
    draw.text(((canvas_w - w) / 2, y), text, font=f, fill=fill)


# ---------------------------------------------------------------------------
# 1. Classic Academic — cream background, navy border, serif type, gold seal
# ---------------------------------------------------------------------------
def cert_academic():
    img = Image.new("RGB", (W, H), "#FBF7EC")
    d = ImageDraw.Draw(img)
    navy = "#1B2A4A"
    gold = "#A8791F"

    d.rectangle([28, 28, W - 28, H - 28], outline=navy, width=6)
    d.rectangle([46, 46, W - 46, H - 46], outline=gold, width=2)

    f_script = font(f"{FONT_DIR_DEJAVU}/DejaVuSerif-Bold.ttf", 30)
    f_title = font(f"{FONT_DIR_DEJAVU}/DejaVuSerif-Bold.ttf", 62)
    f_body = font(f"{FONT_DIR_DEJAVU}/DejaVuSerif.ttf", 28)
    f_name = font(f"{FONT_DIR_DEJAVU}/DejaVuSerif-BoldItalic.ttf", 50)
    f_small = font(f"{FONT_DIR_DEJAVU}/DejaVuSerif.ttf", 22)

    center_text(d, "RIVERBEND INSTITUTE OF TECHNOLOGY", 110, f_script, navy)
    center_text(d, "CERTIFICATE OF COMPLETION", 175, f_title, navy)
    center_text(d, "This is to certify that", 300, f_body, "#333")
    center_text(d, "Ayesha Raheel Malik", 350, f_name, gold)
    center_text(d, "has successfully completed the course", 440, f_body, "#333")
    center_text(d, "Machine Learning & Data Science Bootcamp", 490, font(f"{FONT_DIR_DEJAVU}/DejaVuSerif-Bold.ttf", 34), navy)
    center_text(d, "Duration: 12 Weeks   |   Grade: A+", 555, f_body, "#333")
    center_text(d, "Date: 15/06/2026", 610, f_small, "#333")
    center_text(d, "Certificate No: RIT-2026-04471", 645, f_small, "#333")

    d.line([(200, 900), (500, 900)], fill=navy, width=2)
    center_text(d, "Program Director", 910, f_small, "#333", canvas_w=700)
    d.line([(1100, 900), (1400, 900)], fill=navy, width=2)
    center_text(d, "Date Issued", 910, f_small, "#333", canvas_w=700)

    d.ellipse([W / 2 - 60, 780, W / 2 + 60, 900], outline=gold, width=3)
    center_text(d, "SEAL", 830, f_small, gold)

    img.save(os.path.join(OUT_DIR, "sample_01_academic_completion.png"))


# ---------------------------------------------------------------------------
# 2. Modern Minimalist — white background, teal accent bar, sans-serif
# ---------------------------------------------------------------------------
def cert_modern():
    img = Image.new("RGB", (W, H), "#FFFFFF")
    d = ImageDraw.Draw(img)
    teal = "#0F6E6A"
    dark = "#1A1A1A"

    d.rectangle([0, 0, 26, H], fill=teal)
    d.rectangle([0, H - 26, W, H], fill=teal)

    f_eyebrow = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Bold.ttf", 24)
    f_title = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Bold.ttf", 58)
    f_name = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Bold.ttf", 46)
    f_body = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Regular.ttf", 26)
    f_small = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Regular.ttf", 20)

    d.text((110, 90), "NORTHGATE DIGITAL ACADEMY", font=f_eyebrow, fill=teal)
    d.text((110, 140), "CERTIFICATE", font=f_title, fill=dark)
    d.text((110, 210), "OF ACHIEVEMENT", font=f_title, fill=teal)

    d.text((110, 340), "Awarded to:", font=f_body, fill="#555")
    d.text((110, 380), "Daniyal Ahmed Khan", font=f_name, fill=dark)

    d.text((110, 470), "For successfully completing", font=f_body, fill="#555")
    d.text((110, 505), "Full-Stack Web Development", font=font(f"{FONT_DIR_LIBERATION}/LiberationSans-Bold.ttf", 32), fill=teal)

    d.text((110, 580), "Score: 92%", font=f_body, fill="#333")
    d.text((110, 615), "Duration: 8 weeks", font=f_body, fill="#333")

    d.text((110, 700), "Issued by Northgate Digital Academy", font=f_small, fill="#555")
    d.text((110, 730), "Date: 2026-05-22", font=f_small, fill="#555")
    d.text((110, 760), "Certificate ID: NDA-2026-1183", font=f_small, fill="#555")

    d.rectangle([1200, 90, 1480, 260], outline=teal, width=2)
    center_text(d, "VERIFIED", 160, f_eyebrow, teal, canvas_w=1600)

    img.save(os.path.join(OUT_DIR, "sample_02_modern_achievement.png"))


# ---------------------------------------------------------------------------
# 3. Corporate Training — deep blue header banner, structured grid
# ---------------------------------------------------------------------------
def cert_corporate():
    img = Image.new("RGB", (W, H), "#F4F6F9")
    d = ImageDraw.Draw(img)
    blue = "#173C6B"
    accent = "#E8A93C"

    d.rectangle([0, 0, W, 220], fill=blue)
    f_header = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Bold.ttf", 44)
    f_sub = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Regular.ttf", 24)
    center_text(d, "CERTIFICATE OF TRAINING", 70, f_header, "#FFFFFF")
    center_text(d, "Vertex Corporate Solutions — Professional Development Program", 135, f_sub, "#D8E0EC")

    d.rectangle([0, 220, W, 226], fill=accent)

    f_body = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Regular.ttf", 26)
    f_name = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Bold.ttf", 44)
    f_label = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Bold.ttf", 20)

    center_text(d, "This certifies that", 300, f_body, "#333")
    center_text(d, "Sana Fatima Iqbal", 345, f_name, blue)
    center_text(d, "has completed the training program", 430, f_body, "#333")
    center_text(d, "Project Management & Agile Leadership", 470, font(f"{FONT_DIR_LIBERATION}/LiberationSans-Bold.ttf", 32), accent)

    rows = [
        ("Organization:", "Vertex Corporate Solutions"),
        ("Issue Date:", "March 3, 2026"),
        ("Certificate Number:", "VCS-TRN-8842"),
        ("Grade:", "Distinction"),
        ("Duration:", "6 months"),
    ]
    y = 580
    for label, value in rows:
        d.text((450, y), label, font=f_label, fill="#555")
        d.text((750, y), value, font=f_body, fill="#111")
        y += 44

    img.save(os.path.join(OUT_DIR, "sample_03_corporate_training.png"))


# ---------------------------------------------------------------------------
# 4. Elegant Award — dark background, gold text, ornamental border
# ---------------------------------------------------------------------------
def cert_elegant():
    img = Image.new("RGB", (W, H), "#101820")
    d = ImageDraw.Draw(img)
    gold = "#D4AF37"
    cream = "#EFE6D0"

    d.rectangle([40, 40, W - 40, H - 40], outline=gold, width=3)
    d.rectangle([56, 56, W - 56, H - 56], outline=gold, width=1)

    f_title = font(f"{FONT_DIR_FREEFONT}/FreeSerif.ttf", 60)
    f_body = font(f"{FONT_DIR_FREEFONT}/FreeSerif.ttf", 26)
    f_name = font(f"{FONT_DIR_FREEFONT}/FreeSerif.ttf", 48)
    f_small = font(f"{FONT_DIR_FREEFONT}/FreeSerif.ttf", 20)

    center_text(d, "AWARD OF EXCELLENCE", 130, f_title, gold)
    center_text(d, "Meridian Institute of Design", 210, f_body, cream)

    center_text(d, "Presented to", 330, f_body, cream)
    center_text(d, "Hamza Tariq Sheikh", 375, f_name, gold)
    center_text(d, "in recognition of outstanding performance in", 465, f_body, cream)
    center_text(d, "UI/UX Design Fundamentals", 505, font(f"{FONT_DIR_FREEFONT}/FreeSerifBold.ttf", 34), gold)

    center_text(d, "Grade: A   |   Duration: 4 weeks", 580, f_body, cream)
    center_text(d, "Date: 01/07/2026", 630, f_small, cream)
    center_text(d, "Certificate ID: MID-AE-2026-337", 665, f_small, cream)

    center_text(d, "— Meridian Institute of Design —", 940, f_small, gold)

    img.save(os.path.join(OUT_DIR, "sample_04_elegant_award.png"))


# ---------------------------------------------------------------------------
# 5. Colorful Bootcamp — gradient-style banner, playful but readable
# ---------------------------------------------------------------------------
def cert_colorful():
    img = Image.new("RGB", (W, H), "#FFFFFF")
    d = ImageDraw.Draw(img)

    # simple horizontal gradient band
    for x in range(W):
        ratio = x / W
        r = int(0x2D + (0x8E - 0x2D) * ratio)
        g = int(0x6C + (0x3D - 0x6C) * ratio)
        b = int(0xE0 + (0xC7 - 0xE0) * ratio)
        d.line([(x, 0), (x, 160)], fill=(r, g, b))

    f_title = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Bold.ttf", 46)
    center_text(d, "CERTIFICATE OF PARTICIPATION", 55, f_title, "#FFFFFF")

    f_body = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Regular.ttf", 26)
    f_name = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Bold.ttf", 44)
    dark = "#222"
    purple = "#6C3EC7"

    center_text(d, "CodeSprint Youth Bootcamp 2026", 210, font(f"{FONT_DIR_LIBERATION}/LiberationSans-Bold.ttf", 28), purple)

    center_text(d, "This certificate is proudly presented to", 300, f_body, "#555")
    center_text(d, "Zainab Noor Abbasi", 345, f_name, purple)
    center_text(d, "for active participation in the", 430, f_body, "#555")
    center_text(d, "48-Hour Python & AI Hackathon", 470, font(f"{FONT_DIR_LIBERATION}/LiberationSans-Bold.ttf", 32), dark)

    center_text(d, "Result: Top 10 Finisher", 550, f_body, dark)
    center_text(d, "Duration: 2 days", 585, f_body, dark)

    f_small = font(f"{FONT_DIR_LIBERATION}/LiberationSans-Regular.ttf", 20)
    center_text(d, "Issued by CodeSprint Youth Bootcamp   |   Date: 28/06/2026", 650, f_small, "#555")
    center_text(d, "Certificate No: CS-2026-YB-0592", 680, f_small, "#555")

    for i, cx in enumerate(range(200, 1500, 260)):
        d.ellipse([cx, 950, cx + 20, 970], fill=["#2D6CE0", "#8E3DC7", "#E0C0FF", "#F2A65A", "#3EC77A", "#E0475A"][i % 6])

    img.save(os.path.join(OUT_DIR, "sample_05_colorful_bootcamp.png"))


if __name__ == "__main__":
    cert_academic()
    cert_modern()
    cert_corporate()
    cert_elegant()
    cert_colorful()
    print("5 sample certificates generated in:", OUT_DIR)
