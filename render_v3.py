#!/usr/bin/env python3
"""Render the v3 one-page newspaper for Thursday 19 November 2026.

Fresh renderer for the make.fun news-image-20261119 competition, account
@huaminyo (second account). Draws a 1024x1024 broadsheet with PIL:
masthead, numbers strip, region bar, UTC timeline, 16 illustrated
stories, a pin map, 34 briefs, a markets strip and a DATE CHECK footer.

Run:  python3 render_v3.py            -> writes entry.png next to this file
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 241, 227)
PAPER_DARK = (238, 231, 210)
INK = (24, 24, 24)
INK_SOFT = (60, 60, 60)
NAVY = (27, 42, 74)
NAVY_LIGHT = (43, 63, 105)
RED = (179, 38, 30)
RED_DARK = (140, 28, 22)
GOLD = (176, 141, 58)
GREEN_TAG = (30, 120, 70)
AMBER_TAG = (176, 120, 20)
BLUE_TAG = (36, 100, 160)
CARD = (255, 252, 244)
RULE = (180, 172, 150)
SKY = (168, 205, 225)
SKY_DUSK = (245, 180, 120)

REGION_COLORS = {
    "ASIA": (178, 58, 44),
    "EUROPE": (36, 113, 163),
    "MIDDLE EAST": (165, 125, 20),
    "AFRICA": (30, 132, 73),
    "AMERICAS": (125, 60, 152),
    "OCEANIA": (20, 143, 119),
    "GLOBAL": (93, 109, 126),
}

# ---------------------------------------------------------------- fonts
FD = "/usr/share/fonts/truetype/dejavu/"


def F(name, size):
    return ImageFont.truetype(FD + name, size)


SERIF_B = "DejaVuSerif-Bold.ttf"
SERIF = "DejaVuSerif.ttf"
SANS_B = "DejaVuSans-Bold.ttf"
SANS = "DejaVuSans.ttf"

# ---------------------------------------------------------------- helpers


def tw(draw, text, font):
    """Text width in px."""
    return draw.textlength(text, font=font)


def wrap(draw, text, font, max_w):
    """Greedy word wrap; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if tw(draw, trial, font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, font, color, max_w, leading, max_lines=None):
    lines = wrap(draw, text, font, max_w)
    if max_lines:
        lines = lines[:max_lines]
    for i, line in enumerate(lines):
        draw.text((x, y + i * leading), line, font=font, fill=color)
    return y + len(lines) * leading


def vgrad(draw, box, c_top, c_bot):
    x0, y0, x1, y1 = box
    h = max(1, y1 - y0)
    for i in range(h):
        t = i / h
        c = tuple(int(c_top[k] + (c_bot[k] - c_top[k]) * t) for k in range(3))
        draw.line([(x0, y0 + i), (x1, y0 + i)], fill=c)


def sun(draw, cx, cy, r, color=(252, 214, 110)):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    draw.ellipse([cx - r * 0.72, cy - r * 0.72, cx + r * 0.72, cy + r * 0.72],
                 fill=(255, 236, 170))


def cloud(draw, x, y, s, color=(255, 255, 255)):
    draw.ellipse([x, y, x + 26 * s, y + 14 * s], fill=color)
    draw.ellipse([x + 8 * s, y - 7 * s, x + 30 * s, y + 10 * s], fill=color)
    draw.ellipse([x + 20 * s, y, x + 44 * s, y + 13 * s], fill=color)


def person(draw, x, y, s, suit, skin=(232, 190, 150), hair=(40, 30, 25)):
    """Simple seated/standing figure, s = scale (~1.0 -> 26px tall)."""
    draw.ellipse([x - 5 * s, y - 13 * s, x + 5 * s, y - 3 * s], fill=skin)
    draw.pieslice([x - 5 * s, y - 13 * s, x + 5 * s, y - 5 * s], 180, 360,
                  fill=hair)
    draw.rounded_rectangle([x - 9 * s, y - 3 * s, x + 9 * s, y + 13 * s],
                           radius=4 * s, fill=suit)
    draw.polygon([(x - 2 * s, y - 3 * s), (x + 2 * s, y - 3 * s),
                  (x, y + 4 * s)], fill=(240, 240, 240))
    draw.polygon([(x - 1.5 * s, y - 1 * s), (x + 1.5 * s, y - 1 * s),
                  (x, y + 9 * s)], fill=RED)


def flag(draw, x, y, w, h, code):
    """Simplified recognisable flags."""
    if code == "US":
        for i in range(7):
            draw.rectangle([x, y + i * h / 7, x + w, y + (i + 1) * h / 7],
                           fill=(179, 38, 60) if i % 2 == 0 else (245, 245, 245))
        draw.rectangle([x, y, x + w * 0.4, y + h * 4 / 7], fill=(40, 60, 140))
        for r in range(3):
            for c in range(4):
                draw.ellipse([x + 2 + c * w * 0.09, y + 2 + r * h * 0.13,
                              x + 4 + c * w * 0.09, y + 4 + r * h * 0.13],
                             fill=(255, 255, 255))
    elif code == "CN":
        draw.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
        draw.text((x + 2, y - 1), "*", font=F(SANS_B, int(h * 0.8)),
                  fill=(255, 220, 60))
    elif code == "RU":
        draw.rectangle([x, y, x + w, y + h / 3], fill=(245, 245, 245))
        draw.rectangle([x, y + h / 3, x + w, y + 2 * h / 3],
                       fill=(40, 90, 180))
        draw.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(200, 40, 40))
    elif code == "DK":
        draw.rectangle([x, y, x + w, y + h], fill=(200, 30, 45))
        draw.rectangle([x + w * 0.28, y, x + w * 0.44, y + h],
                       fill=(245, 245, 245))
        draw.rectangle([x, y + h * 0.38, x + w, y + h * 0.62],
                       fill=(245, 245, 245))
    elif code == "KR":
        draw.rectangle([x, y, x + w, y + h], fill=(250, 250, 250))
        draw.ellipse([x + w * 0.36, y + h * 0.2, x + w * 0.64, y + h * 0.8],
                     fill=(200, 40, 60))
        draw.pieslice([x + w * 0.36, y + h * 0.2, x + w * 0.64, y + h * 0.8],
                      90, 270, fill=(30, 70, 160))
    elif code == "AU":
        draw.rectangle([x, y, x + w, y + h], fill=(30, 60, 140))
        draw.rectangle([x, y, x + w * 0.45, y + h * 0.5], fill=(150, 30, 50))
        draw.ellipse([x + w * 0.68, y + h * 0.2, x + w * 0.78, y + h * 0.4],
                     fill=(255, 255, 255))
        draw.ellipse([x + w * 0.6, y + h * 0.55, x + w * 0.7, y + h * 0.75],
                     fill=(255, 255, 255))
    elif code == "CO":
        draw.rectangle([x, y, x + w, y + h * 0.5], fill=(250, 200, 40))
        draw.rectangle([x, y + h * 0.5, x + w, y + h * 0.75],
                       fill=(40, 90, 180))
        draw.rectangle([x, y + h * 0.75, x + w, y + h], fill=(200, 40, 40))
    elif code == "KE":
        draw.rectangle([x, y, x + w, y + h * 0.33], fill=(30, 30, 30))
        draw.rectangle([x, y + h * 0.33, x + w, y + h * 0.66],
                       fill=(180, 30, 30))
        draw.rectangle([x, y + h * 0.66, x + w, y + h], fill=(30, 130, 60))
        draw.ellipse([x + w * 0.42, y + h * 0.3, x + w * 0.58, y + h * 0.7],
                     fill=(240, 240, 240))
    elif code == "ZA":
        draw.rectangle([x, y, x + w, y + h], fill=(30, 120, 70))
        draw.polygon([(x, y), (x + w * 0.45, y + h * 0.5), (x, y + h)],
                     fill=(30, 30, 30))
        draw.polygon([(x, y), (x + w * 0.38, y + h * 0.5), (x, y + h)],
                     fill=(250, 200, 40))
        draw.rectangle([x, y, x + w, y + h * 0.18], fill=(200, 40, 40))
        draw.rectangle([x, y + h * 0.82, x + w, y + h], fill=(40, 90, 180))
    elif code == "SO":
        draw.rectangle([x, y, x + w, y + h], fill=(110, 170, 230))
        cx, cy = x + w / 2, y + h / 2
        draw.text((cx - 5, cy - 8), "*", font=F(SANS_B, int(h * 0.9)),
                  fill=(255, 255, 255))
    elif code == "AE":
        draw.rectangle([x, y, x + w * 0.25, y + h], fill=(200, 30, 40))
        draw.rectangle([x + w * 0.25, y, x + w, y + h / 3],
                       fill=(30, 130, 60))
        draw.rectangle([x + w * 0.25, y + h / 3, x + w, y + 2 * h / 3],
                       fill=(245, 245, 245))
        draw.rectangle([x + w * 0.25, y + 2 * h / 3, x + w, y + h],
                       fill=(30, 30, 30))
    elif code == "IN":
        draw.rectangle([x, y, x + w, y + h / 3], fill=(255, 150, 50))
        draw.rectangle([x, y + h / 3, x + w, y + 2 * h / 3],
                       fill=(245, 245, 245))
        draw.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(30, 130, 60))
        draw.ellipse([x + w * 0.44, y + h * 0.38, x + w * 0.56, y + h * 0.62],
                     outline=(30, 70, 160), width=1)
    elif code == "MM":
        draw.rectangle([x, y, x + w, y + h / 3], fill=(250, 200, 40))
        draw.rectangle([x, y + h / 3, x + w, y + 2 * h / 3],
                       fill=(30, 130, 60))
        draw.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(200, 40, 40))
        draw.text((x + w * 0.42, y + h * 0.28), "*", font=F(SANS_B, int(h * 0.7)),
                  fill=(255, 255, 255))
    elif code == "GL":
        draw.rectangle([x, y, x + w, y + h / 2], fill=(250, 250, 250))
        draw.rectangle([x, y + h / 2, x + w, y + h], fill=(200, 40, 50))
        draw.ellipse([x + w * 0.3, y + h * 0.25, x + w * 0.7, y + h * 0.75],
                     fill=(200, 40, 50))
        draw.pieslice([x + w * 0.3, y + h * 0.25, x + w * 0.7, y + h * 0.75],
                      180, 360, fill=(250, 250, 250))
    draw.rectangle([x, y, x + w, y + h], outline=(90, 90, 90), width=1)


def skyline(draw, x, y, w, h, color=(70, 85, 110), lit=(255, 210, 110),
            windows=True):
    """Row of buildings with lit windows, base at y+h."""
    bx = x
    while bx < x + w - 8:
        bw = 14 + ((bx * 7) % 18)
        bh = h * (0.35 + ((bx * 13) % 55) / 100.0)
        draw.rectangle([bx, y + h - bh, bx + bw, y + h], fill=color)
        if windows:
            for wy in range(int(y + h - bh + 4), int(y + h - 4), 9):
                for wx in range(int(bx + 3), int(bx + bw - 3), 7):
                    if (wx * 3 + wy * 5) % 7 < 3:
                        draw.rectangle([wx, wy, wx + 3, wy + 4], fill=lit)
        bx += bw + 3


def stamp(draw, x, y, text, font, color=RED, angle=0):
    """Angled rubber-stamp label."""
    pad = 4
    w = int(tw(draw, text, font)) + pad * 2
    h = 16
    layer = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rectangle([2, 2, w + 2, h + 2], outline=color, width=2)
    ld.text((pad + 2, 2), text, font=font, fill=color)
    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    return layer, (x, y)


# ---------------------------------------------------------------- illustrations
# Each ill_* draws into (x, y, w, h) and returns nothing. All art is drawn
# in code: no photos, no external assets.

def ill_summit(draw, x, y, w, h):
    """Lead 1: three leaders at one table, Shenzhen."""
    vgrad(draw, (x, y, x + w, y + h), (38, 58, 100), (24, 34, 66))
    # banner
    draw.rectangle([x, y, x + w, y + 18], fill=(178, 58, 44))
    draw.text((x + 8, y + 3), "APEC 2026  ·  SHENZHEN  ·  FIRST TRILATERAL",
              font=F(SANS_B, 10), fill=(255, 255, 255))
    # flags on poles
    for i, code in enumerate(("US", "CN", "RU")):
        fx = x + 28 + i * (w // 3)
        draw.line([fx + 14, y + 20, fx + 14, y + 52], fill=(200, 200, 200),
                  width=2)
        flag(draw, fx, y + 22, 30, 19, code)
    # table
    ty = y + h - 34
    draw.rectangle([x + 6, ty, x + w - 6, ty + 10], fill=(150, 105, 60))
    draw.rectangle([x + 6, ty + 10, x + w - 6, ty + 13], fill=(110, 75, 40))
    # three figures
    for i, suit in enumerate(((30, 50, 90), (90, 30, 30), (40, 40, 40))):
        px = x + w // 6 + i * (w // 3)
        person(draw, px, ty - 6, 1.5, suit)
        draw.rectangle([px - 26, ty + 16, px + 26, ty + 28],
                       fill=(240, 235, 220))
        draw.rectangle([px - 26, ty + 16, px + 26, ty + 28],
                       outline=(120, 110, 90))
    names = ["TRUMP", "XI", "PUTIN"]
    for i, nm in enumerate(names):
        px = x + w // 6 + i * (w // 3)
        fnt = F(SANS_B, 9)
        draw.text((px - tw(draw, nm, fnt) / 2, ty + 17), nm, font=fnt,
                  fill=(30, 30, 30))


def ill_hague(draw, x, y, w, h):
    """Lead 2: Peace Palace + scales + 9-6 badge."""
    vgrad(draw, (x, y, x + w, y + h), (170, 208, 228), (220, 235, 240))
    sun(draw, x + w - 34, y + 24, 13)
    cloud(draw, x + 14, y + 14, 0.8)
    # Peace Palace: brick hall + tower
    bx, by, bw, bh = x + 14, y + h - 52, w - 90, 44
    draw.rectangle([bx, by, bx + bw, by + bh], fill=(178, 110, 80))
    draw.polygon([(bx - 4, by), (bx + bw + 4, by), (bx + bw - 14, by - 12),
                  (bx + 14, by - 12)], fill=(120, 70, 55))
    for i in range(5):
        wx = bx + 8 + i * (bw - 16) // 5
        draw.rectangle([wx, by + 12, wx + 8, by + 30], fill=(60, 80, 110))
        draw.pieslice([wx, by + 6, wx + 8, by + 16], 180, 360,
                      fill=(60, 80, 110))
    draw.rectangle([bx + bw - 26, by - 34, bx + bw - 6, by + bh],
                   fill=(160, 95, 70))
    draw.polygon([(bx + bw - 30, by - 34), (bx + bw - 2, by - 34),
                  (bx + bw - 16, by - 48)], fill=(100, 60, 50))
    draw.rectangle([bx + bw - 22, by - 28, bx + bw - 10, by - 18],
                   fill=(240, 235, 210))
    # scales of justice
    sx = x + w - 52
    sy = y + h - 46
    draw.line([sx, sy - 30, sx, sy], fill=(150, 110, 30), width=3)
    draw.line([sx - 20, sy - 28, sx + 20, sy - 28], fill=(150, 110, 30),
              width=3)
    for dx in (-20, 20):
        draw.line([sx + dx, sy - 28, sx + dx, sy - 14], fill=(150, 110, 30),
                  width=2)
        draw.pieslice([sx + dx - 10, sy - 16, sx + dx + 10, sy + 2], 0, 180,
                      fill=(200, 160, 60))
    draw.ellipse([sx - 12, sy - 2, sx + 12, sy + 4], fill=(150, 110, 30))
    # 9-6 badge
    draw.rectangle([x + w - 62, y + 6, x + w - 6, y + 34], fill=RED)
    draw.text((x + w - 52, y + 9), "9–6", font=F(SERIF_B, 17),
              fill=(255, 255, 255))
    draw.rectangle([x, y + h - 16, x + w, y + h], fill=NAVY)
    draw.text((x + 8, y + h - 14), "WORLD COURT  ·  THE HAGUE",
              font=F(SANS_B, 9), fill=(255, 255, 255))
    flag(draw, x + w - 34, y + h - 14, 26, 12, "MM")


def ill_cop31(draw, x, y, w, h):
    """Lead 3: COP31 draft drops fossil fuels."""
    vgrad(draw, (x, y, x + w, y + h), (150, 200, 210), (210, 235, 225))
    sun(draw, x + 30, y + 22, 12)
    # hills + turbines
    draw.ellipse([x - 30, y + h - 40, x + w * 0.6, y + h + 30],
                 fill=(120, 180, 120))
    draw.ellipse([x + w * 0.4, y + h - 30, x + w + 30, y + h + 40],
                 fill=(100, 165, 105))
    for tx in (x + 34, x + w - 60):
        draw.line([tx, y + h - 44, tx, y + h - 78], fill=(240, 240, 240),
                  width=3)
        for a in (90, 210, 330):
            ex = tx + 16 * math.cos(math.radians(a))
            ey = y + h - 78 + 16 * math.sin(math.radians(a))
            draw.line([tx, y + h - 78, ex, ey], fill=(245, 245, 245),
                      width=3)
    # draft document
    dx, dy, dw, dh = x + w // 2 - 44, y + 12, 88, 62
    draw.rectangle([dx, dy, dx + dw, dy + dh], fill=(255, 255, 255),
                   outline=(100, 100, 100))
    draw.text((dx + 6, dy + 4), "DRAFT DEAL", font=F(SANS_B, 9),
              fill=(30, 30, 30))
    draw.text((dx + 6, dy + 18), "FOSSIL FUELS", font=F(SANS_B, 11),
              fill=(150, 30, 30))
    draw.line([dx + 5, dy + 28, dx + dw - 5, dy + 24], fill=RED, width=3)
    draw.text((dx + 6, dy + 34), "$120bn aid", font=F(SANS_B, 10),
              fill=(150, 30, 30))
    draw.line([dx + 5, dy + 44, dx + 62, dy + 41], fill=RED, width=3)
    # CUT stamp
    layer, pos = stamp(draw, x + w - 66, y + h - 44, "CUT", F(SANS_B, 13),
                       RED, -12)
    draw._image.paste(layer, (int(x + w - 66), int(y + h - 46)), layer)
    draw.rectangle([x, y + h - 16, x + w, y + h], fill=NAVY)
    draw.text((x + 8, y + h - 14), "COP31  ·  ANTALYA",
              font=F(SANS_B, 9), fill=(255, 255, 255))


def draw_ill(img, ill_fn, x, y, w, h):
    """Draw an illustration clipped to its box via a temp layer."""
    w, h = int(w), int(h)
    layer = Image.new("RGB", (w, h), PAPER)
    ld = ImageDraw.Draw(layer)
    ill_fn(ld, 0, 0, w, h)
    img.paste(layer, (int(x), int(y)))


def ill_anthropic(draw, x, y, w, h):
    """4: Anthropic IPO — candles up, then fade."""
    draw.rectangle([x, y, x + w, y + h], fill=(16, 34, 52))
    draw.text((x + 6, y + 3), "ANT  ·  NASDAQ", font=F(SANS_B, 9),
              fill=(140, 200, 255))
    draw.text((x + w - 52, y + 3), "IPO $83", font=F(SANS_B, 9),
              fill=(255, 220, 100))
    # candlesticks rising then falling
    base = y + h - 14
    tops = [22, 19, 16, 13, 10, 12, 15, 18]
    for i, t in enumerate(tops):
        cx = x + 10 + i * ((w - 20) // 8)
        col = (60, 200, 120) if i < 5 else (230, 90, 80)
        draw.line([cx + 4, base - t - 5, cx + 4, base - 2], fill=col, width=2)
        draw.rectangle([cx, base - t, cx + 8, base - 2], fill=col)
    draw.text((x + 6, y + h - 13), "OPEN $111.50", font=F(SANS_B, 8),
              fill=(120, 220, 150))
    draw.text((x + w - 78, y + h - 13), "CLOSE $97.17  +17%",
              font=F(SANS_B, 8), fill=(255, 180, 120))


def ill_gta(draw, x, y, w, h):
    """5: GTA VI launch — neon night city."""
    vgrad(draw, (x, y, x + w, y + h), (40, 20, 70), (16, 10, 36))
    for i in range(14):
        px = x + (i * 37) % w
        py = y + (i * 23) % (h // 2)
        draw.ellipse([px, py, px + 2, py + 2], fill=(255, 255, 255))
    draw.ellipse([x + w - 34, y + 8, x + w - 10, y + 32],
                 fill=(255, 240, 200))
    skyline(draw, x, y + 8, w, h - 26, color=(52, 32, 88),
            lit=(255, 120, 200))
    # road + car
    draw.rectangle([x, y + h - 18, x + w, y + h], fill=(20, 20, 30))
    draw.line([x, y + h - 9, x + w, y + h - 9], fill=(255, 220, 90), width=2)
    cx, cy = x + w // 2 - 20, y + h - 30
    draw.rounded_rectangle([cx, cy, cx + 44, cy + 12], radius=4,
                           fill=(255, 60, 120))
    draw.rounded_rectangle([cx + 9, cy - 7, cx + 32, cy + 2], radius=3,
                           fill=(255, 100, 150))
    draw.ellipse([cx + 6, cy + 8, cx + 14, cy + 15], fill=(20, 20, 20))
    draw.ellipse([cx + 30, cy + 8, cx + 38, cy + 15], fill=(20, 20, 20))
    draw.text((x + 6, y + 4), "VI", font=F(SERIF_B, 26),
              fill=(255, 220, 90))
    draw.text((x + 6, y + 32), "OUT NOW", font=F(SANS_B, 9),
              fill=(255, 255, 255))


def ill_cyclone(draw, x, y, w, h):
    """6: Cyclone Akvan over the Bay of Bengal."""
    vgrad(draw, (x, y, x + w, y + h), (120, 180, 210), (190, 225, 240))
    # India coast (right) + sea (left)
    draw.polygon([(x + w * 0.62, y), (x + w, y), (x + w, y + h),
                  (x + w * 0.7, y + h), (x + w * 0.55, y + h * 0.55)],
                 fill=(210, 200, 160))
    draw.polygon([(x + w * 0.62, y), (x + w * 0.72, y + h * 0.3),
                  (x + w * 0.55, y + h * 0.55), (x + w * 0.66, y + h * 0.4)],
                 fill=(150, 190, 130))
    # spiral
    cx, cy = x + w * 0.36, y + h * 0.5
    for r in range(8, 34, 5):
        a0 = r * 14
        draw.arc([cx - r, cy - r, cx + r, cy + r], a0, a0 + 250,
                 fill=(255, 255, 255), width=4)
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(240, 240, 240))
    draw.text((x + 4, y + 3), "AKVAN", font=F(SANS_B, 9), fill=(20, 50, 90))
    draw.text((x + w - 62, y + h - 15), "90–100 km/h",
              font=F(SANS_B, 8), fill=(20, 50, 90))


def ill_kerch(draw, x, y, w, h):
    """7: Kerch Bridge hit — night explosion."""
    vgrad(draw, (x, y, x + w, y + h), (20, 30, 60), (50, 60, 100))
    for i in range(10):
        px = x + (i * 41) % w
        py = y + (i * 17) % (h // 2)
        draw.ellipse([px, py, px + 2, py + 2], fill=(255, 255, 255))
    # water
    draw.rectangle([x, y + h * 0.62, x + w, y + h], fill=(30, 60, 100))
    # bridge deck + arch
    draw.rectangle([x, y + h * 0.55, x + w, y + h * 0.62], fill=(120, 120, 130))
    draw.arc([x + w * 0.3, y + h * 0.18, x + w * 0.75, y + h * 0.62],
             180, 360, fill=(160, 160, 170), width=4)
    draw.line([x + w * 0.4, y + h * 0.3, x + w * 0.4, y + h * 0.55],
              fill=(160, 160, 170), width=2)
    draw.line([x + w * 0.52, y + h * 0.22, x + w * 0.52, y + h * 0.55],
              fill=(160, 160, 170), width=2)
    # explosion
    ex, ey = x + w * 0.52, y + h * 0.42
    for r, c in ((16, (255, 120, 40)), (11, (255, 200, 80)),
                 (6, (255, 245, 200))):
        draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill=c)
    draw.ellipse([ex - 20, ey - 30, ex - 4, ey - 12], fill=(90, 90, 90))
    draw.ellipse([ex + 2, ey - 34, ex + 18, ey - 14], fill=(110, 110, 110))
    draw.rectangle([x, y, x + w, y + 14], fill=RED)
    draw.text((x + 6, y + 2), "RAIL HALTED", font=F(SANS_B, 9),
              fill=(255, 255, 255))


def ill_riyadh(draw, x, y, w, h):
    """8: Riyadh intercept — missiles over the skyline."""
    vgrad(draw, (x, y, x + w, y + h), (30, 40, 80), (90, 80, 110))
    skyline(draw, x, y + 6, w, h - 14, color=(60, 55, 85),
            lit=(255, 200, 110))
    # KAFD tower (twisted look: stacked offset rects)
    tx = x + w - 34
    for i in range(5):
        draw.rectangle([tx + (i % 2) * 3, y + 10 + i * 8, tx + 22,
                        y + 18 + i * 8], fill=(140, 130, 160))
    # intercept streaks
    draw.line([x + 12, y + 8, x + w * 0.55, y + h * 0.5],
              fill=(255, 220, 120), width=2)
    draw.line([x + w - 10, y + 14, x + w * 0.5, y + h * 0.45],
              fill=(255, 180, 100), width=2)
    draw.ellipse([x + w * 0.5 - 5, y + h * 0.45 - 5, x + w * 0.5 + 5,
                  y + h * 0.45 + 5], fill=(255, 240, 180))
    draw.rectangle([x, y, x + w, y + 14], fill=(30, 130, 70))
    draw.text((x + 6, y + 2), "INTERCEPTED", font=F(SANS_B, 9),
              fill=(255, 255, 255))


def ill_greenland(draw, x, y, w, h):
    """9: Arctic pact — icy peaks, Danish + US flags, 109-0."""
    vgrad(draw, (x, y, x + w, y + h), (150, 195, 225), (225, 240, 248))
    sun(draw, x + w - 26, y + 16, 10)
    # mountains
    draw.polygon([(x, y + h), (x + w * 0.3, y + h * 0.25),
                  (x + w * 0.55, y + h)], fill=(140, 170, 200))
    draw.polygon([(x + w * 0.2, y + h), (x + w * 0.3, y + h * 0.25),
                  (x + w * 0.4, y + h * 0.45), (x + w * 0.32, y + h * 0.45),
                  (x + w * 0.38, y + h * 0.6)], fill=(255, 255, 255))
    draw.polygon([(x + w * 0.45, y + h), (x + w * 0.7, y + h * 0.35),
                  (x + w, y + h)], fill=(120, 155, 190))
    draw.polygon([(x + w * 0.62, y + h * 0.5), (x + w * 0.7, y + h * 0.35),
                  (x + w * 0.78, y + h * 0.5), (x + w * 0.7, y + h * 0.58)],
                 fill=(255, 255, 255))
    # sea ice
    draw.rectangle([x, y + h - 12, x + w, y + h], fill=(190, 220, 240))
    flag(draw, x + 6, y + h - 34, 26, 16, "DK")
    flag(draw, x + 36, y + h - 34, 26, 16, "US")
    draw.rectangle([x + w - 52, y + 4, x + w - 4, y + 22], fill=NAVY)
    draw.text((x + w - 47, y + 6), "109–0", font=F(SANS_B, 11),
              fill=(255, 255, 255))


def ill_jobless(draw, x, y, w, h):
    """10: Australia jobless 4.9% — big number + rising mini bars."""
    draw.rectangle([x, y, x + w, y + h], fill=(20, 40, 70))
    draw.text((x + 6, y + 3), "AUSTRALIA · OCT", font=F(SANS_B, 8),
              fill=(150, 200, 240))
    draw.text((x + 6, y + 12), "4.9%", font=F(SERIF_B, 24),
              fill=(255, 255, 255))
    draw.text((x + 6, y + h - 13), "753.7k out of work", font=F(SANS_B, 8),
              fill=(255, 220, 100))
    # mini rising bars, right side
    bx0 = x + w - 74
    vals = [3.9, 4.1, 4.7, 4.9]
    for i, v in enumerate(vals):
        bh = int((v - 3.4) / 1.5 * (h - 22))
        bx = bx0 + i * 18
        col = (230, 90, 70) if i == 3 else (90, 160, 220)
        draw.rectangle([bx, y + h - 10 - bh, bx + 13, y + h - 10], fill=col)
    draw.line([bx0, y + h - 22, bx0 + 70, y + h - 34],
              fill=(255, 220, 100), width=2)
    draw.polygon([(bx0 + 70, y + h - 34), (bx0 + 64, y + h - 32),
                  (bx0 + 68, y + h - 28)], fill=(255, 220, 100))


def ill_suneung(draw, x, y, w, h):
    """11: Suneung exam — hall of candidates, clock."""
    draw.rectangle([x, y, x + w, y + h], fill=(235, 225, 200))
    draw.rectangle([x, y, x + w, y + 16], fill=(40, 80, 60))
    draw.text((x + 6, y + 3), "SUNEUNG  ·  SEOUL", font=F(SANS_B, 9),
              fill=(255, 255, 255))
    # desks + candidates
    for r in range(3):
        for c in range(6):
            dx = x + 10 + c * ((w - 20) // 6)
            dy = y + 24 + r * 13
            draw.ellipse([dx + 3, dy, dx + 9, dy + 6], fill=(50, 40, 35))
            draw.rectangle([dx, dy + 6, dx + 12, dy + 11], fill=(70, 90, 120))
    # clock
    cx, cy = x + w - 20, y + 30
    draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(255, 255, 255),
                 outline=(30, 30, 30))
    draw.line([cx, cy, cx, cy - 7], fill=(30, 30, 30), width=2)
    draw.line([cx, cy, cx + 5, cy + 2], fill=(30, 30, 30), width=2)
    draw.rectangle([x + 6, y + h - 16, x + 92, y + h - 4], fill=NAVY)
    draw.text((x + 10, y + h - 15), "551,864 SIT", font=F(SANS_B, 9),
              fill=(255, 255, 255))


def ill_mogadishu(draw, x, y, w, h):
    """12: Somalia expels UAE envoy — flags + 72 hours."""
    vgrad(draw, (x, y, x + w, y + h), (200, 220, 240), (240, 240, 230))
    flag(draw, x + 10, y + 10, 44, 28, "SO")
    flag(draw, x + w - 54, y + 10, 44, 28, "AE")
    # red X between
    cx, cy = x + w // 2, y + 24
    draw.line([cx - 10, cy - 10, cx + 10, cy + 10], fill=RED, width=4)
    draw.line([cx - 10, cy + 10, cx + 10, cy - 10], fill=RED, width=4)
    # plane taking off
    draw.polygon([(x + 14, y + h - 22), (x + 44, y + h - 22),
                  (x + 50, y + h - 28), (x + 20, y + h - 28)],
                 fill=(120, 120, 130))
    draw.polygon([(x + 44, y + h - 22), (x + 62, y + h - 30),
                  (x + 62, y + h - 26), (x + 48, y + h - 18)],
                 fill=(100, 100, 110))
    draw.line([x + 14, y + h - 18, x + 70, y + h - 34],
              fill=(180, 180, 180), width=1)
    draw.rectangle([x + w - 58, y + h - 20, x + w - 4, y + h - 4],
                   fill=RED)
    draw.text((x + w - 54, y + h - 19), "72 HRS", font=F(SANS_B, 9),
              fill=(255, 255, 255))


def ill_bogota(draw, x, y, w, h):
    """13: Colombia national strike — march with banners."""
    vgrad(draw, (x, y, x + w, y + h), (190, 215, 235), (235, 235, 220))
    draw.rectangle([x, y, x + w, y + 16], fill=(250, 200, 40))
    draw.text((x + 6, y + 3), "PARO NACIONAL", font=F(SANS_B, 9),
              fill=(30, 30, 30))
    # crowd
    for i in range(9):
        px = x + 12 + i * ((w - 24) // 9)
        py = y + h - 14
        col = ((200, 60, 60), (60, 120, 200), (60, 160, 80),
               (200, 160, 60))[i % 4]
        person(draw, px, py, 0.85, col)
    # placards
    for i, px in enumerate((x + 16, x + w // 2 - 4, x + w - 30)):
        draw.rectangle([px, y + 22, px + 22, y + 34], fill=(255, 255, 255),
                       outline=(30, 30, 30))
        draw.line([px + 11, y + 34, px + 11, y + 44], fill=(80, 80, 80),
                  width=2)
    draw.text((x + 19, y + 24), "NO", font=F(SANS_B, 8), fill=RED)


def ill_doping(draw, x, y, w, h):
    """14: Marathon champion banned — track + BANNED stamp."""
    draw.rectangle([x, y, x + w, y + h], fill=(232, 205, 170))
    # track lanes
    for i in range(4):
        ly = y + 12 + i * 11
        draw.line([x, ly, x + w, ly], fill=(255, 255, 255), width=1)
    # runner, left of centre
    rx, ry = x + w // 2 - 34, y + 20
    draw.ellipse([rx + 8, ry - 6, rx + 16, ry + 2], fill=(90, 60, 40))
    draw.line([rx + 10, ry + 2, rx + 6, ry + 16], fill=(30, 30, 30), width=3)
    draw.line([rx + 6, ry + 16, rx - 2, ry + 26], fill=(30, 30, 30), width=3)
    draw.line([rx + 6, ry + 16, rx + 16, ry + 24], fill=(30, 30, 30),
              width=3)
    draw.line([rx + 10, ry + 4, rx + 2, ry + 10], fill=(30, 30, 30), width=3)
    draw.line([rx + 10, ry + 4, rx + 18, ry + 12], fill=(30, 30, 30),
              width=3)
    # finish post
    draw.line([x + w // 2 + 6, y + 4, x + w // 2 + 6, y + h - 4],
              fill=(255, 255, 255), width=2)
    layer, _ = stamp(draw, 0, 0, "BANNED · 3 YRS", F(SANS_B, 10), RED, -8)
    draw._image.paste(layer, (int(x + w - 108), int(y + 6)), layer)
    flag(draw, x + 6, y + h - 18, 24, 14, "KE")


def ill_seoulcourt(draw, x, y, w, h):
    """15: Korea's top court clears ex-PM Han — courthouse + gavel."""
    vgrad(draw, (x, y, x + w, y + h), (170, 200, 225), (225, 235, 240))
    # courthouse
    cx = x + 12
    draw.rectangle([cx, y + 22, cx + w - 60, y + h - 10],
                   fill=(220, 215, 195))
    draw.polygon([(cx - 4, y + 22), (cx + w - 56, y + 22),
                  (cx + (w - 60) // 2, y + 8)], fill=(150, 60, 60))
    for i in range(4):
        px = cx + 8 + i * ((w - 76) // 4)
        draw.rectangle([px, y + 30, px + 6, y + h - 10],
                       fill=(255, 255, 255))
    # gavel
    gx, gy = x + w - 26, y + 18
    draw.line([gx - 8, gy + 14, gx + 8, gy - 6], fill=(120, 80, 40), width=3)
    draw.rectangle([gx - 2, gy - 12, gx + 14, gy - 2], fill=(120, 80, 40))
    draw.ellipse([gx - 12, gy + 16, gx + 10, gy + 24], fill=(150, 100, 50))
    layer, _ = stamp(draw, 0, 0, "OVERTURNED", F(SANS_B, 9),
                     (30, 130, 70), -6)
    draw._image.paste(layer, (int(x + w - 104), int(y + h - 24)), layer)


def ill_cricket(draw, x, y, w, h):
    """16: South Africa win by 9 wickets — oval + stumps."""
    draw.ellipse([x - 10, y + 6, x + w + 10, y + h + 16],
                 fill=(110, 180, 100))
    draw.ellipse([x + 6, y + 14, x + w - 6, y + h + 4],
                 fill=(140, 200, 120))
    # pitch
    draw.rectangle([x + w // 2 - 12, y + 10, x + w // 2 + 12, y + h - 8],
                   fill=(220, 200, 160))
    # stumps
    for sx in (x + w // 2 - 7, x + w // 2, x + w // 2 + 7):
        draw.line([sx, y + 12, sx, y + 24], fill=(250, 220, 120), width=3)
    for sx in (x + w // 2 - 7, x + w // 2, x + w // 2 + 7):
        draw.line([sx, y + h - 20, sx, y + h - 8], fill=(250, 220, 120),
                  width=3)
    # ball + bat
    draw.ellipse([x + w // 2 + 18, y + h // 2 - 3, x + w // 2 + 24,
                  y + h // 2 + 3], fill=(200, 40, 40))
    draw.rectangle([x + w // 2 - 30, y + h // 2 - 2, x + w // 2 - 14,
                    y + h // 2 + 10], fill=(200, 170, 120))
    draw.rectangle([x + 4, y + 4, x + 74, y + 20], fill=NAVY)
    draw.text((x + 8, y + 6), "9 WICKETS", font=F(SANS_B, 10),
              fill=(255, 255, 255))
    flag(draw, x + w - 30, y + 4, 24, 14, "ZA")


# ---------------------------------------------------------------- map
# Simplified continent outlines in (lon, lat) pairs, equirectangular.
CONTINENTS = [
    # North America
    [(-168, 66), (-158, 71), (-140, 70), (-128, 70), (-115, 68), (-95, 69),
     (-85, 66), (-80, 73), (-65, 62), (-55, 52), (-65, 45), (-75, 35),
     (-80, 25), (-90, 21), (-97, 16), (-92, 14), (-83, 9), (-79, 9),
     (-85, 15), (-95, 18), (-105, 23), (-114, 29), (-125, 40), (-124, 48),
     (-135, 58), (-155, 58), (-168, 66)],
    # Greenland
    [(-58, 64), (-45, 60), (-32, 68), (-25, 70), (-35, 76), (-55, 76),
     (-62, 70), (-58, 64)],
    # South America
    [(-79, 9), (-72, 12), (-62, 10), (-52, 5), (-44, -3), (-35, -8),
     (-39, -17), (-48, -27), (-57, -38), (-65, -45), (-68, -52),
     (-72, -54), (-73, -37), (-70, -20), (-77, -12), (-81, -6), (-80, 1),
     (-79, 9)],
    # Africa
    [(-17, 15), (-10, 5), (4, 6), (9, 4), (13, -12), (12, -18), (18, -34),
     (25, -34), (32, -29), (36, -18), (40, -10), (41, -2), (48, 11),
     (43, 12), (38, 18), (32, 31), (20, 32), (10, 37), (-6, 35), (-10, 31),
     (-17, 21), (-17, 15)],
    # Eurasia (rough)
    [(-10, 36), (-9, 43), (-2, 48), (-5, 50), (3, 51), (8, 57), (12, 54),
     (18, 56), (21, 60), (24, 58), (28, 71), (40, 68), (55, 69), (70, 72),
     (90, 75), (110, 74), (130, 72), (150, 70), (170, 67), (178, 65),
     (170, 60), (158, 52), (142, 50), (140, 40), (130, 33), (122, 30),
     (120, 23), (109, 18), (105, 9), (100, 7), (98, 12), (92, 16),
     (88, 22), (80, 7), (76, 8), (73, 20), (66, 25), (57, 26), (52, 28),
     (48, 30), (44, 29), (39, 21), (43, 12), (35, 28), (36, 36), (30, 36),
     (27, 41), (23, 36), (19, 42), (12, 44), (8, 44), (3, 43), (-2, 37),
     (-10, 36)],
    # UK
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (1, 57), (1, 51), (-5, 50)],
    # Japan
    [(130, 31), (133, 34), (137, 35), (140, 38), (141, 42), (145, 44),
     (143, 40), (140, 36), (135, 33), (130, 31)],
    # SE Asia islands
    [(95, 5), (105, -5), (115, -8), (125, -9), (135, -4), (141, -3),
     (131, -1), (120, 1), (110, 2), (100, 0), (95, 5)],
    # Australia
    [(114, -22), (114, -30), (118, -35), (124, -33), (130, -32),
     (135, -35), (140, -38), (147, -39), (150, -37), (153, -27),
     (146, -19), (142, -11), (136, -12), (132, -11), (126, -14),
     (122, -17), (114, -22)],
    # New Zealand
    [(167, -46), (171, -42), (174, -39), (178, -38), (175, -41),
     (170, -43), (167, -46)],
]

# story number -> (lon, lat) for map pins
PINS = {
    1: (114, 22), 2: (4, 52), 3: (31, 37), 4: (-74, 41), 5: (172, -35),
    6: (86, 20), 7: (36, 45), 8: (47, 25), 9: (-42, 64), 10: (149, -35),
    11: (127, 37), 12: (46, 2), 13: (-74, 5), 14: (37, -1), 15: (127, 37),
    16: (28, -26), 17: (30, 50), 18: (13, 52), 19: (2, 49), 20: (4, 51),
    21: (12, 42), 22: (-4, 40), 23: (7, 45), 24: (107, 47), 25: (114, 22),
    26: (90, 24), 27: (107, -6), 28: (121, 25), 29: (116, 40),
    30: (57, 26), 31: (34, 31), 32: (44, 15), 33: (16, 48), 34: (-17, 15),
    35: (39, 9), 36: (28, -26), 37: (32, 16), 38: (-77, 39), 39: (-89, 14),
    40: (-48, -16), 41: (-58, -35), 42: (-72, 19), 43: (-84, 39),
    44: (-77, 39), 45: (175, -41), 46: (178, -18), 47: (-160, -21),
    48: (0, 0), 49: (8, 47), 50: (0, 0),
}

# pins shown on the map: the 16 illustrated stories + 6 key briefs,
# so the map stays legible instead of a smear of dots over Europe.
MAP_PINS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
            17, 26, 27, 38, 40, 45}
PIN_NUDGE = {2: (-6, 2), 7: (4, -2), 15: (8, 5), 18: (5, 3), 19: (-7, 4),
             20: (-4, -4), 21: (6, 4), 22: (-8, 2), 23: (4, -3),
             25: (-7, 6), 33: (6, -2), 36: (8, -5), 44: (7, 6),
             47: (-5, -3), 49: (5, 3)}


def draw_map(draw, x, y, w, h):
    """Equirectangular world map with numbered pins."""
    draw.rectangle([x, y, x + w, y + h], fill=(198, 224, 240))
    # graticule
    for gx in range(1, 12):
        lx = x + gx * w / 12
        draw.line([lx, y, lx, y + h], fill=(175, 205, 225), width=1)
    for gy in range(1, 6):
        ly = y + gy * h / 6
        draw.line([x, ly, x + w, ly], fill=(175, 205, 225), width=1)

    def proj(lon, lat):
        px = x + (lon + 180) / 360 * w
        py = y + (90 - lat) / 180 * h
        return px, py

    for cont in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in cont]
        draw.polygon(pts, fill=(214, 204, 170), outline=(160, 150, 120))
    draw.rectangle([x, y, x + w, y + h], outline=(120, 120, 110))
    # pins: illustrated stories first (bigger), then key briefs
    for num in sorted(MAP_PINS):
        lon, lat = PINS[num]
        if (lon, lat) == (0, 0):
            continue
        px, py = proj(lon, lat)
        dx, dy = PIN_NUDGE.get(num, (0, 0))
        px += dx
        py += dy
        big = num <= 16
        r = 7 if big else 6
        col = RED if big else NAVY
        draw.ellipse([px - r, py - r, px + r, py + r], fill=col,
                     outline=(255, 255, 255))
        fnt = F(SANS_B, 7 if big else 6)
        t = str(num)
        draw.text((px - tw(draw, t, fnt) / 2, py - r + 1), t, font=fnt,
                  fill=(255, 255, 255))


# ---------------------------------------------------------------- data
# Every story happened, or was first reported, on Thursday 19 November
# 2026 (any time zone). Tags: REPORTED = confirmed by named sources;
# CLAIM = one side's account, not independently verified; FORECAST =
# outlook, poll, draft or schedule.

NUMBERS = [
    ("3", "presidents at one table"),
    ("9–6", "World Court genocide vote"),
    ("$81.3bn", "Anthropic's record IPO"),
    ("109–0", "Danish vote on Arctic pact"),
    ("4.9%", "Australian jobless rate"),
    ("204,070", "listed to evacuate in Odisha"),
    ("551,864", "candidates in Korea's exam"),
]

REGIONS = [("ASIA", 10), ("EUROPE", 11), ("MIDDLE EAST", 5), ("AFRICA", 7),
           ("AMERICAS", 9), ("OCEANIA", 4), ("GLOBAL", 4)]

TIMELINE = [
    ("00:30", "CANBERRA", "Jobless rate 4.9%"),
    ("02:05", "RIYADH", "Missile intercepted"),
    ("08:16", "SHENZHEN", "Three leaders sit down"),
    ("09:00", "THE HAGUE", "Genocide ruling read"),
    ("10:15", "HORMUZ", "Tankers hit mines"),
    ("13:30", "WASHINGTON", "Jobless claims 203,000"),
    ("14:30", "NEW YORK", "Anthropic opens $111.50"),
    ("21:00", "NEW YORK", "Dow closes down 1,101"),
]

# num, place, beat, tag, headline, deck, source, illustration
LEADS = [
    (1, "SHENZHEN", "SUMMIT", "REPORTED",
     "Trump, Xi and Putin hold first three-way summit",
     "The three leaders met for 90 minutes and issued a joint "
     "declaration on nuclear risk. Kyiv was not in the room.",
     "Reuters · AP · Xinhua", ill_summit),
    (2, "THE HAGUE", "JUSTICE", "REPORTED",
     "World Court: Myanmar committed genocide",
     "By 9 votes to 6 the ICJ found Myanmar guilty of genocide against "
     "the Rohingya and ordered reparations.",
     "Al Jazeera · UN News", ill_hague),
    (3, "ANTALYA", "CLIMATE", "REPORTED",
     "COP31 draft drops fossil fuels and $120bn aid goal",
     "The slimmer text has no fossil-fuel phase-out and no figure for "
     "adaptation aid. Talks are due to end on Friday.",
     "Reuters · AFP", ill_cop31),
]

SMALL_ROWS = [
    [
        (4, "NEW YORK", "MARKETS", "REPORTED",
         "Anthropic debuts in the biggest IPO on record",
         "ANT priced at $83, opened at $111.50, closed up 17% at $97.17. "
         "The $81.3bn sale tops the record.",
         "AP · CNBC", ill_anthropic),
        (5, "WORLDWIDE", "GAMES", "REPORTED",
         "GTA VI goes on sale after 13 years",
         "Midnight launches, NZ first. 17.1m pre-orders; $2bn day-one sales.",
         "ABC · Sensor Tower", ill_gta),
        (6, "ODISHA", "STORM", "FORECAST",
         "Cyclone Akvan nears India's coast",
         "204,070 told to evacuate; landfall due Friday near Gopalpur.",
         "IMD", ill_cyclone),
        (7, "CRIMEA", "WAR", "REPORTED",
         "Kerch Bridge hit again",
         "Third strike in a week halts trains to Russia.",
         "Euronews", ill_kerch),
        (8, "RIYADH", "WAR", "REPORTED",
         "Saudis shoot down Houthi missiles",
         "Debris fell on the capital; no casualties reported.",
         "Reuters", ill_riyadh),
    ],
    [
        (9, "GREENLAND", "SECURITY", "REPORTED",
         "Denmark backs Arctic pact with US",
         "Parliament approves the Greenland security deal 109–0.",
         "AP", ill_greenland),
        (10, "CANBERRA", "ECONOMY", "REPORTED",
         "Australia's jobless rate hits 4.9%",
         "Highest since 2021; 43,500 jobs lost in October.",
         "ABS", ill_jobless),
        (11, "SEOUL", "EDUCATION", "REPORTED",
         "551,864 sit Suneung exam",
         "Flights pause for the listening section.",
         "Yonhap", ill_suneung),
        (12, "MOGADISHU", "DIPLOMACY", "REPORTED",
         "Somalia expels UAE envoy",
         "72 hours to leave; Mogadishu cites “open invasion”.",
         "Al Jazeera", ill_mogadishu),
    ],
    [
        (13, "BOGOTÁ", "LABOUR", "REPORTED",
         "Colombia's unions hold national strike",
         "Marches in three cities against a rescue law.",
         "Infobae", ill_bogota),
        (14, "NAIROBI", "SPORT", "REPORTED",
         "Marathon champion banned for doping",
         "Kenya's Peres Jepchirchir gets three years.",
         "ABC", ill_doping),
        (15, "SEOUL", "JUSTICE", "REPORTED",
         "Korea's top court clears ex-PM Han",
         "Han Duck-soo's martial-law conviction is overturned.",
         "AP", ill_seoulcourt),
        (16, "JOHANNESBURG", "SPORT", "REPORTED",
         "South Africa beat Bangladesh by 9 wickets",
         "Harmer takes 6–51; SA lead the series 1–0.",
         "AP", ill_cricket),
    ],
]

# num, place, text, source — single-line briefs
BRIEFS = [
    (17, "Kyiv", "Drones hit Kyiv by day; embassies hit.", "Kyiv Independent"),
    (18, "Berlin", "Europe seeks winter truce.", "Euronews"),
    (19, "Paris", "French left splits over pact.", "AP"),
    (20, "Brussels", "EU delays methane rules two years.", "Euronews"),
    (21, "Rome", "Author Corrado Augias dies at 91.", "Euronews"),
    (22, "Madrid", "Sánchez, Feijóo clash on TV.", "AP"),
    (23, "Turin", "Alcaraz reaches ATP Finals semis.", "AP"),
    (24, "Ulaanbaatar", "MPs accept president's exit.", "AP"),
    (25, "Shenzhen", "Xi urges ban on all nuclear arms.", "Al Jazeera"),
    (26, "Dhaka", "Yunus home torched; 28 districts hit.", "AP"),
    (27, "Jakarta", "Asset-seizure law passes at last.", "Antara"),
    (28, "Taipei", "TSMC tightens China AI chip curbs.", "Reuters"),
    (29, "Beijing", "Alibaba beats revenue estimates.", "Reuters"),
    (30, "Hormuz", "Iran says tankers hit mines.", "Al Jazeera"),
    (31, "Gaza", "Israel says tank raid is over.", "BBC"),
    (32, "Sanaa", "Saudi strikes kill 10, Houthis claim.", "Al Jazeera"),
    (33, "Vienna", "West seeks Iran inspections.", "Reuters"),
    (34, "Dakar", "Dozens missing as boats sink.", "Reuters"),
    (35, "Addis Ababa", "Airline probes loyalty hack.", "Reuters"),
    (36, "Pretoria", "Central bank holds rate at 7.25%.", "SABC"),
    (37, "Khartoum", "RSF claims Bau district taken.", "AP"),
    (38, "Washington", "Senate rejects Iran war curb, 51–48.", "AP"),
    (39, "San Salvador", "Bukele seeks third term.", "AP"),
    (40, "Brasília", "Lula moves to shield Raoni's land.", "AP"),
    (41, "Buenos Aires", "Disability law passes 71–0.", "AP"),
    (42, "Port-au-Prince", "34 gang suspects killed.", "AP"),
    (43, "Cincinnati", "Fiona the hippo dies at zoo.", "AP"),
    (44, "Washington", "Trump pardons Pete Rose.", "AP"),
    (45, "Wellington", "Pay-equity cuts broke rights law.", "RNZ"),
    (46, "Nadi", "Cyclone Xavier weakens to category 4.", "RNZ"),
    (47, "Avarua", "Cook Islands declare emergency.", "RNZ"),
    (48, "Space", "Red giant eats a Sun-sized star.", "Nature"),
    (49, "Zurich", "Two rivals to challenge Infantino.", "ABC"),
    (50, "World", "Google taps Blue Origin for AI sats.", "Reuters"),
]

MARKETS = [
    ("S&P 500", "7,175.83", "−2.02%"),
    ("DOW", "49,097", "−2.19%"),
    ("NASDAQ", "23,879", "−2.25%"),
    ("BRENT", "$92.27", "+0.35%"),
    ("GOLD", "$3,675", "−1.36%"),
    ("BITCOIN", "$61,974", "−0.88%"),
]

DATE_CHECK = (
    "DATE CHECK ✓  Every story here happened, or was first reported, on "
    "Thursday 19 November 2026.  LEFT OUT (earlier days): Anthropic's $83 "
    "pricing (Wed 18) · EU's €45bn Ukraine loan (Wed 18) · Van Gogh "
    "$190.4m sale (Wed 18) · Voyager 1 light-day (Wed 18) · Nvidia results "
    "(Tue 17).  NOT YET NEWS: Akvan's landfall · COP31's close (Fri 20 Nov)."
)

FOOTER = ("Every story here happened on, or was first reported on, Thursday "
          "19 November 2026 (any time zone). Claims are attributed, not "
          "stated as fact. Pictures and map: original, drawn in code. "
          "Sources: Reuters, AP, AFP, BBC, Al Jazeera, UN News, Euronews, "
          "ABC, RNZ, Xinhua, Yonhap, Antara, ABS, IMD, NASA, Infobae.")

TAG_COLORS = {"REPORTED": GREEN_TAG, "CLAIM": AMBER_TAG,
              "FORECAST": BLUE_TAG}


def tag_chip(draw, x, y, tag):
    fnt = F(SANS_B, 8)
    w = int(tw(draw, tag, fnt)) + 8
    draw.rectangle([x, y, x + w, y + 11], fill=TAG_COLORS[tag])
    draw.text((x + 4, y + 1), tag, font=fnt, fill=(255, 255, 255))
    return w


def num_badge(draw, x, y, num, r=8):
    draw.ellipse([x - r, y - r, x + r, y + r], fill=RED)
    fnt = F(SANS_B, 9)
    t = str(num)
    draw.text((x - tw(draw, t, fnt) / 2, y - 6), t, font=fnt,
              fill=(255, 255, 255))


# ---------------------------------------------------------------- layout
def build_page():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    M = 8                      # outer margin
    CW = W - 2 * M             # content width = 1008

    # ---- top bar
    draw.rectangle([0, 0, W, 22], fill=NAVY)
    draw.text((M, 5), "THE WORLD IN ONE DAY", font=F(SANS_B, 11),
              fill=(255, 255, 255))
    rt = "50 STORIES  ·  7 REGIONS  ·  16 DRAWN  ·  ALL FROM THIS ONE DAY"
    draw.text((W - M - tw(draw, rt, F(SANS_B, 11)), 5), rt,
              font=F(SANS_B, 11), fill=(220, 220, 220))

    # ---- masthead
    title = "Thursday 19 November 2026"
    tf = F(SERIF_B, 58)
    draw.text((M, 24), title, font=tf, fill=INK)
    draw.line([M, 88, W - M, 88], fill=RED, width=2)
    sub = ("Trump, Xi and Putin share one table  ·  The World Court finds "
           "genocide in Myanmar  ·  COP31's draft drops fossil fuels")
    draw.text((M, 92), sub, font=F(SERIF, 15), fill=RED_DARK)

    # ---- numbers strip
    y0, y1 = 112, 152
    draw.rectangle([M, y0, W - M, y1], fill=CARD, outline=RULE)
    cell = CW / len(NUMBERS)
    for i, (num, lab) in enumerate(NUMBERS):
        cx = M + i * cell
        if i:
            draw.line([cx, y0 + 5, cx, y1 - 5], fill=RULE)
        nf = F(SERIF_B, 23)
        draw.text((cx + (cell - tw(draw, num, nf)) / 2, y0 + 3), num,
                  font=nf, fill=RED_DARK)
        lf = F(SANS, 8)
        draw.text((cx + (cell - tw(draw, lab, lf)) / 2, y0 + 28), lab,
                  font=lf, fill=INK_SOFT)

    # ---- region bar (widths proportional to counts)
    y0, y1 = 156, 176
    total = sum(c for _, c in REGIONS)
    rx = M
    for name, count in REGIONS:
        rw = CW * count / total
        draw.rectangle([rx, y0, rx + rw, y1],
                       fill=REGION_COLORS[name])
        label = f"{name} {count}"
        lf = F(SANS_B, 9)
        draw.text((rx + (rw - tw(draw, label, lf)) / 2, y0 + 5), label,
                  font=lf, fill=(255, 255, 255))
        rx += rw

    # ---- timeline
    y0, y1 = 180, 220
    draw.rectangle([M, y0, M + 96, y1], fill=RED)
    draw.text((M + 8, y0 + 5), "THE DAY", font=F(SANS_B, 10),
              fill=(255, 255, 255))
    draw.text((M + 8, y0 + 18), "IN UTC", font=F(SANS_B, 10),
              fill=(255, 255, 255))
    tx0 = M + 104
    twidth = W - M - tx0
    ly = y0 + 26
    draw.line([tx0, ly, W - M, ly], fill=RULE, width=2)
    slot = twidth / len(TIMELINE)
    for i, (t, place, what) in enumerate(TIMELINE):
        cx = tx0 + i * slot + slot / 2
        draw.ellipse([cx - 4, ly - 4, cx + 4, ly + 4], fill=RED)
        tf2 = F(SANS_B, 9)
        draw.text((cx - tw(draw, t, tf2) / 2, y0 + 2), t, font=tf2,
                  fill=RED_DARK)
        pf = F(SANS_B, 7)
        draw.text((cx - tw(draw, place, pf) / 2, y0 + 13), place, font=pf,
                  fill=NAVY)
        wf = F(SANS, 8)
        lines = wrap(draw, what, wf, slot - 6)
        for j, ln in enumerate(lines[:2]):
            draw.text((cx - tw(draw, ln, wf) / 2, ly + 6 + j * 10), ln,
                      font=wf, fill=INK)

    # ---- lead stories
    y0 = 226
    lead_h = 200
    gap = 8
    col_w = (CW - 2 * gap) / 3
    for i, (num, place, beat, tag, head, deck, src, ill) in enumerate(LEADS):
        cx = M + i * (col_w + gap)
        draw.rectangle([cx, y0, cx + col_w, y0 + lead_h], fill=CARD,
                       outline=RULE)
        draw_ill(img, ill, cx + 1, y0 + 1, col_w - 2, 104)
        ty = y0 + 110
        num_badge(draw, cx + 12, ty + 7, num)
        kf = F(SANS_B, 9)
        draw.text((cx + 24, ty + 2), f"{place} · {beat}", font=kf,
                  fill=NAVY)
        tag_chip(draw, cx + col_w - 66, ty + 2, tag)
        hf = F(SERIF_B, 19)
        hy = draw_wrapped(draw, cx + 8, ty + 17, head, hf, INK,
                          col_w - 16, 22, max_lines=2)
        df = F(SANS, 11)
        dy = draw_wrapped(draw, cx + 8, hy + 3, deck, df, INK_SOFT,
                          col_w - 16, 13, max_lines=2)
        draw.text((cx + 8, dy + 2), "— " + src, font=F(SANS, 8),
                  fill=(130, 120, 100))

    # ---- small story rows
    y = 432
    row_h = 118
    for row in SMALL_ROWS:
        n = len(row)
        gap2 = 6
        col_w2 = (CW - (n - 1) * gap2) / n
        for i, (num, place, beat, tag, head, deck, src, ill) in enumerate(row):
            cx = M + i * (col_w2 + gap2)
            draw.rectangle([cx, y, cx + col_w2, y + row_h], fill=CARD,
                           outline=RULE)
            draw_ill(img, ill, cx + 1, y + 1, col_w2 - 2, 50)
            ty = y + 54
            num_badge(draw, cx + 11, ty + 6, num, r=7)
            kf = F(SANS_B, 8)
            draw.text((cx + 21, ty + 1), f"{place} · {beat}", font=kf,
                      fill=NAVY)
            tag_chip(draw, cx + col_w2 - 62, ty + 1, tag)
            hf = F(SERIF_B, 13)
            hy = draw_wrapped(draw, cx + 6, ty + 14, head, hf, INK,
                              col_w2 - 12, 15, max_lines=2)
            df = F(SANS, 9)
            dy = draw_wrapped(draw, cx + 6, hy + 1, deck, df, INK_SOFT,
                              col_w2 - 12, 11, max_lines=2)
            draw.text((cx + 6, dy), "— " + src, font=F(SANS, 7),
                      fill=(130, 120, 100))
        y += row_h + 4

    # ---- bottom: map + briefs
    y0 = y + 2                      # 798
    bot_h = 148
    # left: map + markets
    map_w = 310
    draw.text((M, y0), "WHERE IT HAPPENED", font=F(SANS_B, 10), fill=NAVY)
    draw.text((M + 132, y0 + 1), "numbers match the stories",
              font=F(SANS, 8), fill=INK_SOFT)
    draw_map(draw, M, y0 + 15, map_w, 96)
    # markets strip under the map
    my = y0 + 116
    draw.rectangle([M, my, M + map_w, my + 32], fill=NAVY)
    draw.text((M + 6, my + 2), "MARKETS · THU CLOSE", font=F(SANS_B, 8),
              fill=(255, 220, 100))
    mf = F(SANS_B, 8)
    for i, (name, val, chg) in enumerate(MARKETS):
        mx = M + 6 + (i % 3) * 102
        myy = my + 13 + (i // 3) * 11
        col = (120, 220, 150) if chg.startswith("+") else (255, 130, 120)
        draw.text((mx, myy), f"{name} {chg}", font=mf, fill=col)
    # right: briefs
    bx = M + map_w + 10
    bw = W - M - bx
    draw.text((bx, y0), "ALSO ON THURSDAY 19 NOVEMBER — 34 MORE STORIES",
              font=F(SANS_B, 10), fill=NAVY)
    cols = 3
    per = 12
    col_w3 = bw / cols
    bf = F(SANS, 9)
    bfb = F(SANS_B, 9)
    for idx, (num, place, text, src) in enumerate(BRIEFS):
        c = idx // per
        r = idx % per
        px = bx + c * col_w3
        py = y0 + 15 + r * 11.5
        draw.text((px, py), str(num), font=bfb, fill=RED_DARK)
        label = f"{place} — {text}"
        max_w = col_w3 - 20
        while tw(draw, label, bf) > max_w and len(label) > 12:
            label = label[:-1]
        if label != f"{place} — {text}":
            label = label[:-1] + "…"
        draw.text((px + 18, py), label, font=bf, fill=INK)

    # ---- DATE CHECK
    y0 = 952
    draw.rectangle([M, y0, W - M, y0 + 40], outline=RED, width=2)
    df2 = F(SANS, 9)
    lines = wrap(draw, DATE_CHECK, df2, CW - 16)
    for j, ln in enumerate(lines[:3]):
        draw.text((M + 8, y0 + 4 + j * 12), ln, font=df2, fill=INK)

    # ---- footer
    ff = F(SANS, 7.5)
    flines = wrap(draw, FOOTER, ff, CW)
    for j, ln in enumerate(flines[:2]):
        draw.text((M + (CW - tw(draw, ln, ff)) / 2, 996 + j * 10), ln,
                  font=ff, fill=(130, 120, 100))

    return img


def main():
    img = build_page()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "entry.png")
    img.save(out, optimize=True)
    size = os.path.getsize(out)
    print(f"wrote {out}  {img.size}  {size} bytes  "
          f"({'OK' if size <= 1048576 else 'OVER 1MiB'})")
    print("stories: 50 (16 illustrated, 34 briefs); regions:",
          dict(REGIONS))


if __name__ == "__main__":
    main()
