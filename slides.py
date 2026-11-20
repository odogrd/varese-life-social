"""Varese Life slide builder.

Usage:
    python3 slides.py spec.json OUTDIR PREFIX

spec.json:
{
  "style": "A" | "B" | "C" | "D",
  "slides": [
    {"t": "cover", "title": "...", "sub": "..."},
    {"t": "items", "heading": "...", "items": ["...", "..."]},
    {"t": "cta", "heading": "...", "body": "...", "button": "..."}
  ]
}

Output: OUTDIR/PREFIX_slide1.png, PREFIX_slide2.png, ... (1080x1350, 4:5).
Brand colours only: black #111111, white, yellow #F5C518.
Styles: A stack, B giallo (yellow cover and CTA), C numerata, D banda.
"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(HERE, "assets", "va-life-white.png")
FONT = "/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf"

W, H = 1080, 1350
BG = (17, 17, 17)
WHITE = (255, 255, 255)
GREY = (190, 190, 190)
LINE = (70, 70, 70)
YELLOW = (245, 197, 24)
MARGIN = 96
LOGO_H = 120


def font(size, weight):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([weight])
    return f


_logo = Image.open(LOGO_PATH).convert("RGBA")
_logo = _logo.crop(_logo.getchannel("A").getbbox())
_logo = _logo.resize((round(_logo.width * LOGO_H / _logo.height), LOGO_H), Image.LANCZOS)
LOGO_WHITE = _logo
_black = Image.new("RGBA", _logo.size, (17, 17, 17, 255))
_black.putalpha(_logo.getchannel("A"))
LOGO_BLACK = _black


def tw(d, t, f):
    return d.textlength(t, font=f)


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if tw(d, t, f) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def fit(d, text, size, weight, maxlines, maxw):
    while True:
        f = font(size, weight)
        lines = wrap(d, text, f, maxw)
        if len(lines) <= maxlines and all(tw(d, l, f) <= maxw for l in lines):
            return f, lines, size
        size -= 4


def canvas(style, kind, n, total, arrow):
    """Return (img, d, fg, margin_left) for a slide."""
    yellow_bg = style == "B" and kind in ("cover", "cta")
    bg = YELLOW if yellow_bg else BG
    fg = BG if yellow_bg else WHITE
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    ml = MARGIN
    if style == "D":
        d.rectangle((0, 0, 44, H), fill=YELLOW)
        ml = MARGIN + 40
    # counter
    if yellow_bg:
        d.text((W - MARGIN, 60), f"{n}/{total}", font=font(120, 700), fill=YELLOW,
               stroke_width=3, stroke_fill=BG, anchor="ra")
    else:
        d.text((W - MARGIN, 60), f"{n}/{total}", font=font(120, 700), fill=BG,
               stroke_width=3, stroke_fill=YELLOW, anchor="ra")
    logo = LOGO_BLACK if yellow_bg else LOGO_WHITE
    img.paste(logo, (ml, H - 96 - LOGO_H), logo)
    if arrow:
        cx, cy, r = W - MARGIN - 38, H - 96 - LOGO_H // 2, 38
        circle = BG if yellow_bg else YELLOW
        glyph = YELLOW if yellow_bg else BG
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=circle)
        d.line((cx - 14, cy, cx + 14, cy), fill=glyph, width=5)
        d.line((cx + 3, cy - 12, cx + 15, cy), fill=glyph, width=5)
        d.line((cx + 3, cy + 12, cx + 15, cy), fill=glyph, width=5)
    return img, d, fg, ml


def top(total_h):
    return max(260, (260 + 1120) // 2 - total_h // 2)


def cover(style, n, total, s, path):
    img, d, fg, ml = canvas(style, "cover", n, total, True)
    maxw = W - ml - MARGIN
    hf, hl, hs = fit(d, s["title"].upper(), 130, 800 if style in ("B", "C", "D") else 600, 4, maxw)
    lh = int(hs * 1.1)
    sf = font(46, 600 if style == "B" else 500)
    sl = wrap(d, s.get("sub", ""), sf, maxw) if s.get("sub") else []
    extra = 70 if style == "C" else 0
    y = top(lh * len(hl) + (40 + 62 * len(sl) if sl else 0) + extra)
    if style == "C":
        d.rectangle((ml, y - 10, ml + 170, y + 6), fill=YELLOW)
        y += 60
    for i, l in enumerate(hl):
        if style == "C":
            col = YELLOW
        elif style == "D":
            col = YELLOW if i == 0 else WHITE
        else:
            col = fg
        d.text((ml, y), l, font=hf, fill=col)
        y += lh
    y += 40
    for l in sl:
        d.text((ml, y), l, font=sf, fill=(BG if style == "B" else GREY))
        y += 62
    img.save(path)


def items(style, n, total, s, path):
    img, d, fg, ml = canvas(style, "items", n, total, True)
    maxw = W - ml - MARGIN
    head_w = 800
    hf, hl, hs = fit(d, s["heading"].upper(), 110 if style != "C" else 80, head_w, 3, maxw)
    lh = int(hs * 1.1)
    f = font(44, 500 if style in ("A", "B") else 600)
    ind = 64 if style in ("A", "B", "D") else 150
    il = [wrap(d, t, f, maxw - ind) for t in s["items"]]
    row_pad = 30 if style != "C" else 44
    ih = sum(len(ls) * 62 + row_pad for ls in il)
    y = top(lh * len(hl) + 50 + ih)
    hcol = YELLOW if style == "B" else WHITE
    for l in hl:
        d.text((ml, y), l, font=hf, fill=hcol)
        y += lh
    if style == "C":
        d.rectangle((ml, y + 6, ml + 170, y + 20), fill=YELLOW)
        y += 30
    y += 50
    for idx, ls in enumerate(il):
        if style == "A":
            d.ellipse((ml, y + 18, ml + 26, y + 44), fill=YELLOW)
        elif style == "B":
            d.rectangle((ml, y + 18, ml + 26, y + 44), fill=YELLOW)
        elif style == "C":
            d.text((ml, y - 12), f"{idx + 1:02d}", font=font(84, 800), fill=YELLOW)
        elif style == "D":
            d.rectangle((ml, y + 6, ml + 8, y + 56), fill=YELLOW)
        for l in ls:
            d.text((ml + ind, y), l, font=f, fill=WHITE)
            y += 62
        if style in ("C", "D") and idx < len(il) - 1:
            d.line((ml, y + row_pad // 2, W - MARGIN, y + row_pad // 2), fill=LINE, width=2)
        y += row_pad
    img.save(path)


def cta(style, n, total, s, path):
    img, d, fg, ml = canvas(style, "cta", n, total, False)
    maxw = W - ml - MARGIN
    hf, hl, hs = fit(d, s["heading"].upper(), 100, 800 if style != "A" else 600, 4, maxw)
    lh = int(hs * 1.1)
    bf = font(42, 500)
    bl = wrap(d, s["body"], bf, maxw)
    btn_f = font(40, 700)
    button = s["button"]
    btn_w = int(tw(d, button, btn_f)) + 100
    y = top(lh * len(hl) + 50 + len(bl) * 60 + 60 + 110)
    if style == "D":
        pad = 36
        d.rectangle((ml - pad, y - pad, W - MARGIN + pad // 2, y + lh * len(hl) + pad - 10), fill=YELLOW)
        for l in hl:
            d.text((ml, y), l, font=hf, fill=BG)
            y += lh
        y += pad
    else:
        for l in hl:
            d.text((ml, y), l, font=hf, fill=fg)
            y += lh
    if style == "C":
        d.rectangle((ml, y + 18, ml + 170, y + 32), fill=YELLOW)
        y += 34
    y += 50
    for l in bl:
        d.text((ml, y), l, font=bf, fill=fg)
        y += 60
    y += 60
    if style == "B":
        d.rounded_rectangle((ml, y, ml + btn_w, y + 110), radius=55, fill=BG)
        d.text((ml + btn_w // 2, y + 55), button, font=btn_f, fill=YELLOW, anchor="mm")
    elif style == "C":
        d.rounded_rectangle((ml, y, ml + btn_w, y + 110), radius=55, outline=YELLOW, width=6)
        d.text((ml + btn_w // 2, y + 55), button, font=btn_f, fill=YELLOW, anchor="mm")
    elif style == "D":
        d.rounded_rectangle((ml, y, ml + btn_w, y + 110), radius=18, fill=WHITE)
        d.text((ml + btn_w // 2, y + 55), button, font=btn_f, fill=BG, anchor="mm")
    else:
        d.rounded_rectangle((ml, y, ml + btn_w, y + 110), radius=55, fill=YELLOW)
        d.text((ml + btn_w // 2, y + 55), button, font=btn_f, fill=BG, anchor="mm")
    img.save(path)


def build(spec, outdir, prefix):
    style = spec.get("style", "A")
    slides = spec["slides"]
    total = len(slides)
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for i, s in enumerate(slides, 1):
        path = os.path.join(outdir, f"{prefix}_slide{i}.png")
        {"cover": cover, "items": items, "cta": cta}[s["t"]](style, i, total, s, path)
        paths.append(path)
    return paths


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        spec = json.load(fh)
    for p in build(spec, sys.argv[2], sys.argv[3]):
        print(p)
