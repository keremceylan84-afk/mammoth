#!/usr/bin/env python3
"""Generates the Mammoth Sport watch face resources.

Produces, under app/src/main/res:
  raw/watchface.xml        Watch Face Format (v2) document
  drawable/*.png           background, runner figure, weather and moon icons
  drawable/preview.png     picker preview rendered with sample data

Run from the repository root:  python3 tools/generate_watchface.py
Requires Pillow.
"""
import math
import os
import random
import re
from xml.sax.saxutils import escape, quoteattr

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "app", "src", "main", "res")
DRAWABLE = os.path.join(RES, "drawable")
FONT_DIR = os.path.join(RES, "font")

W = 450
C = W / 2
SS = 4  # supersampling factor for drawn assets

GREEN = "#ff2bf58c"
GREEN_RGB = (43, 245, 140)
TEAL_RGB = (32, 200, 190)
WHITE = "#ffffffff"
GREY = "#ff8a9099"
DIM = "#ff4a5058"
TRACK = "#ff2a3038"
RED = "#ffff3b3b"

FONTS = {
    "barlow_bold": os.path.join(FONT_DIR, "barlow_bold.ttf"),
    "barlow_semibold": os.path.join(FONT_DIR, "barlow_semibold.ttf"),
    "dseg7_bold": os.path.join(FONT_DIR, "dseg7_bold.ttf"),
}

# Sample values used only for the preview image.
SAMPLE = {
    "steps": "7985", "step_pct": "79%", "battery": "74%", "sunrise": "8:24",
    "distance": "6,08", "hr": "78", "zone": "2", "date": "NOVEMBER 03",
    "event": "15:15 Team Meeting @ Head Office", "time": "12:48", "sec": "56",
    "ampm": "PM", "notif": "4",
}


def argb_to_rgba(c):
    c = c.lstrip("#")
    if len(c) == 6:
        c = "ff" + c
    a, r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4, 6))
    return (r, g, b, a)


def save(img, name):
    os.makedirs(DRAWABLE, exist_ok=True)
    img.save(os.path.join(DRAWABLE, name + ".png"), optimize=True)


def circle_mask(size):
    m = Image.new("L", (size * SS, size * SS), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size * SS - 1, size * SS - 1), fill=255)
    return m.resize((size, size), Image.LANCZOS)


# --------------------------------------------------------------------------
# Drawn assets
# --------------------------------------------------------------------------

def draw_background():
    s = SS
    img = Image.new("RGBA", (W * s, W * s), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)

    # Carbon base with diagonal hatching.
    d.rectangle((0, 0, W * s, W * s), fill=(20, 23, 27, 255))
    for k in range(-W, W * 2, 6):
        d.line(((k * s, 0), ((k + W) * s, W * s)), fill=(27, 31, 36, 255), width=2 * s)

    # Right data panel with slanted left edge and row separators.
    d.polygon([(262 * s, 44 * s), (W * s, 44 * s), (W * s, 168 * s), (240 * s, 168 * s)],
              fill=(11, 13, 16, 255), outline=(44, 50, 58, 255), width=2 * s)
    for y in (86, 127):
        x0 = 262 - (y - 44) * 0.175
        d.line(((x0 * s, y * s), (W * s, y * s)), fill=(44, 50, 58, 255), width=2 * s)

    # Clock band and day-list column.
    d.polygon([(0, 198 * s), (W * s, 198 * s), (W * s, 292 * s), (118 * s, 292 * s),
               (106 * s, 340 * s), (0, 340 * s)], fill=(10, 11, 13, 255))
    d.line(((0, 198 * s), (W * s, 198 * s)), fill=(48, 54, 62, 255), width=2 * s)

    # Aurora weather area.
    aur = Image.new("RGBA", (W, W), (4, 14, 16, 255))
    ad = ImageDraw.Draw(aur)
    rnd = random.Random(7)
    for _ in range(26):
        x = rnd.uniform(90, 420)
        y = rnd.uniform(300, 360)
        rx = rnd.uniform(18, 50)
        ry = rnd.uniform(40, 90)
        col = rnd.choice([(30, 210, 120), (20, 170, 160), (60, 240, 150), (15, 120, 110)])
        ad.ellipse((x - rx, y - ry, x + rx, y + ry), fill=col + (90,))
    aur = aur.filter(ImageFilter.GaussianBlur(14))
    ad = ImageDraw.Draw(aur)
    for _ in range(40):
        x, y = rnd.uniform(100, 400), rnd.uniform(296, 330)
        ad.point((x, y), fill=(220, 255, 240, rnd.randint(80, 200)))
    # Dark fade at the bottom so the current temperature stays readable.
    fade = Image.new("L", (W, W), 0)
    fd = ImageDraw.Draw(fade)
    for y in range(W):
        fd.line(((0, y), (W, y)), fill=int(max(0, min(1, (y - 330) / 90)) * 170))
    aur = Image.composite(Image.new("RGBA", (W, W), (3, 8, 10, 255)), aur, fade)
    area = Image.new("L", (W * s, W * s), 0)
    ImageDraw.Draw(area).polygon([(118 * s, 293 * s), (W * s, 293 * s), (W * s, W * s), (0, W * s),
                                  (0, 341 * s), (106 * s, 341 * s)], fill=255)
    img.paste(aur.resize((W * s, W * s), Image.BICUBIC), (0, 0), area)
    d = ImageDraw.Draw(img)
    d.line(((118 * s, 293 * s), (W * s, 293 * s)), fill=(48, 54, 62, 255), width=2 * s)

    # Date tab.
    d.rounded_rectangle((44 * s, 168 * s, 206 * s, 195 * s), radius=6 * s, fill=(43, 47, 53, 255))
    d.polygon([(200 * s, 168 * s), (218 * s, 168 * s), (206 * s, 195 * s), (200 * s, 195 * s)],
              fill=(43, 47, 53, 255))
    d.line(((48 * s, 169 * s), (214 * s, 169 * s)), fill=(90, 96, 104, 255), width=1 * s)

    # Static icons: footprints, location pin, heart.
    g = GREEN_RGB + (255,)
    for (fx, fy, rot) in ((92, 96, -0.2), (100, 104, 0.2)):
        d.ellipse(((fx - 3) * s, (fy - 6) * s, (fx + 3) * s, (fy + 4) * s), fill=g)
        d.ellipse(((fx - 2) * s, (fy + 5) * s, (fx + 2) * s, (fy + 9) * s), fill=g)
    px, py = 265, 106
    d.ellipse(((px - 8) * s, (py - 12) * s, (px + 8) * s, (py + 4) * s), fill=g)
    d.polygon([((px - 7) * s, (py - 1) * s), ((px + 7) * s, (py - 1) * s), (px * s, (py + 12) * s)], fill=g)
    d.ellipse(((px - 3) * s, (py - 7) * s, (px + 3) * s, (py - 1) * s), fill=(11, 13, 16, 255))
    hx, hy = 258, 148
    d.ellipse(((hx - 9) * s, (hy - 8) * s, (hx + 1) * s, (hy + 2) * s), fill=g)
    d.ellipse(((hx - 1) * s, (hy - 8) * s, (hx + 9) * s, (hy + 2) * s), fill=g)
    d.polygon([((hx - 9) * s, (hy - 2) * s), ((hx + 9) * s, (hy - 2) * s), (hx * s, (hy + 10) * s)], fill=g)
    d.line(((hx - 7) * s, (hy - 1) * s, (hx - 3) * s, (hy - 1) * s, (hx - 1) * s, (hy - 5) * s,
            (hx + 2) * s, (hy + 3) * s, (hx + 4) * s, (hy - 1) * s, (hx + 7) * s, (hy - 1) * s),
           fill=(11, 13, 16, 255), width=int(1.5 * s))

    # Minute ticks around the edge.
    for i in range(60):
        a = math.radians(i * 6)
        r0 = 216 if i % 5 else 211
        x0, y0 = C + r0 * math.sin(a), C - r0 * math.cos(a)
        x1, y1 = C + 223 * math.sin(a), C - 223 * math.cos(a)
        d.line(((x0 * s, y0 * s), (x1 * s, y1 * s)),
               fill=(70, 76, 84, 255) if i % 5 else (150, 156, 164, 255), width=(1 if i % 5 else 2) * s)

    img = img.resize((W, W), Image.LANCZOS)
    out = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    out.paste(img, (0, 0), circle_mask(W))
    return out


def draw_runner():
    w, h = 74, 116
    s = SS * 2
    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def limb(pts, width, col):
        pts = [(x * s, y * s) for x, y in pts]
        d.line(pts, fill=col, width=int(width * s), joint="curve")
        for x, y in pts:
            r = width * s / 2
            d.ellipse((x - r, y - r, x + r, y + r), fill=col)

    back = (150, 154, 160, 255)
    front = (245, 246, 248, 255)
    limb([(40, 36), (54, 52), (60, 68)], 7, back)              # back arm
    limb([(42, 68), (58, 84), (70, 100), (73, 96)], 9, back)  # back leg
    limb([(38, 30), (42, 68)], 15, front)                    # torso
    limb([(36, 68), (26, 90), (12, 108), (5, 108)], 10, front)  # front leg
    limb([(36, 36), (22, 50), (14, 42)], 7, front)           # front arm
    d.ellipse((30 * s, 2 * s, 54 * s, 26 * s), fill=front)    # head
    # Soft shading on the right side of the figure.
    shade = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shade).ellipse((40 * s, 0, 90 * s, 120 * s), fill=(0, 0, 0, 40))
    alpha = img.getchannel("A")
    img = Image.alpha_composite(img, Image.composite(shade, Image.new("RGBA", img.size, (0, 0, 0, 0)), alpha))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.putalpha(alpha.point(lambda v: v * 0.5).filter(ImageFilter.GaussianBlur(3 * s)))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(shadow, (2 * s, 3 * s))
    out.alpha_composite(img)
    return out.resize((w, h), Image.LANCZOS)


ICON = 128


def _cloud(d, ox, oy, sc, top=(250, 252, 255), bottom=(170, 200, 225), dark=False):
    if dark:
        top, bottom = (150, 158, 170), (90, 98, 112)
    blobs = [(-30, 6, 24), (-4, -12, 30), (26, 2, 24), (0, 12, 26)]
    mask = Image.new("L", d.im.size, 0)
    md = ImageDraw.Draw(mask)
    for bx, by, r in blobs:
        cx, cy, rr = ox + bx * sc, oy + by * sc, r * sc
        md.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=255)
    md.rectangle((ox - 30 * sc, oy + 6 * sc, ox + 26 * sc, oy + 38 * sc), fill=255)
    grad = Image.new("RGBA", d.im.size)
    gd = ImageDraw.Draw(grad)
    y0, y1 = oy - 42 * sc, oy + 38 * sc
    for y in range(d.im.size[1]):
        t = max(0.0, min(1.0, (y - y0) / max(1, y1 - y0)))
        gd.line(((0, y), (d.im.size[0], y)), fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,))
    return grad, mask


def _sun(img, cx, cy, r):
    s = img.size[0]
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((cx - r * 1.5, cy - r * 1.5, cx + r * 1.5, cy + r * 1.5), fill=(255, 170, 40, 120))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(r * 0.35)))
    disc = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(disc)
    for i in range(int(r), 0, -1):
        t = i / r
        col = (255, int(140 + 90 * (1 - t)), int(20 + 80 * (1 - t)), 255)
        dd.ellipse((cx - i - r * 0.15 * (1 - t), cy - i - r * 0.25 * (1 - t), cx + i, cy + i), fill=col)
    img.alpha_composite(disc)
    del s


def _moon(img, cx, cy, r):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(250, 236, 170, 255))
    d.ellipse((cx - r * 0.35, cy - r * 1.1, cx + r * 1.5, cy + r * 0.75), fill=(0, 0, 0, 0))


def draw_weather_icon(kind):
    s = SS
    n = ICON * s
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = n / 2
    sc = s * 1.15

    def put_cloud(ox, oy, k=1.0, dark=False):
        grad, mask = _cloud(d, ox, oy, sc * k, dark=dark)
        img.paste(grad, (0, 0), mask)

    def drops(color, count, length, start_y, heavy=False):
        dd = ImageDraw.Draw(img)
        xs = [cx - 30 * sc + i * (60 * sc / max(1, count - 1)) for i in range(count)]
        for i, x in enumerate(xs):
            y = start_y + (i % 2) * 8 * sc
            dd.line(((x, y), (x - 6 * sc, y + length * sc)), fill=color, width=int((5 if heavy else 4) * s))

    if kind == "sun":
        _sun(img, cx, cy, 34 * sc)
    elif kind == "moon":
        _moon(img, cx, cy, 34 * sc)
    elif kind in ("partly_day", "partly_night"):
        if kind == "partly_day":
            _sun(img, cx - 16 * sc, cy - 18 * sc, 26 * sc)
        else:
            _moon(img, cx - 16 * sc, cy - 18 * sc, 24 * sc)
        put_cloud(cx + 10 * sc, cy + 8 * sc, 0.85)
    elif kind == "cloudy":
        put_cloud(cx + 14 * sc, cy - 10 * sc, 0.7, dark=True)
        put_cloud(cx - 4 * sc, cy + 6 * sc, 0.9)
    elif kind == "fog":
        put_cloud(cx, cy - 12 * sc, 0.85)
        for i, y in enumerate((28, 40, 52)):
            d.rounded_rectangle((cx - (40 - i * 6) * sc, cy + (y - 4) * sc, cx + (40 - i * 4) * sc, cy + y * sc),
                                radius=2 * s, fill=(200, 210, 220, 230))
    elif kind in ("rain", "heavy_rain"):
        put_cloud(cx, cy - 14 * sc, 0.9, dark=kind == "heavy_rain")
        drops((90, 190, 255, 255), 5 if kind == "heavy_rain" else 4, 20 if kind == "heavy_rain" else 14,
              cy + 26 * sc, heavy=kind == "heavy_rain")
    elif kind in ("snow", "sleet"):
        put_cloud(cx, cy - 14 * sc, 0.9)
        dd = ImageDraw.Draw(img)
        for i in range(4):
            x = cx - 27 * sc + i * 18 * sc
            y = cy + (32 + (i % 2) * 10) * sc
            if kind == "sleet" and i % 2:
                dd.line(((x, y - 6 * sc), (x - 4 * sc, y + 8 * sc)), fill=(90, 190, 255, 255), width=4 * s)
            else:
                r = 4.5 * sc
                dd.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 255))
    elif kind == "thunder":
        put_cloud(cx, cy - 14 * sc, 0.9, dark=True)
        d = ImageDraw.Draw(img)
        bolt = [(4, 18), (-12, 44), (0, 44), (-8, 62), (16, 34), (4, 34), (12, 18)]
        d.polygon([(cx + x * sc, cy + y * sc) for x, y in bolt], fill=(255, 210, 40, 255))
    elif kind == "wind":
        d = ImageDraw.Draw(img)
        for y, ln in ((-18, 40), (0, 52), (18, 34)):
            d.line(((cx - 44 * sc, cy + y * sc), (cx + (ln - 44) * sc, cy + y * sc)), fill=(220, 235, 245, 255), width=6 * s)
            d.arc((cx + (ln - 52) * sc, cy + (y - 16) * sc, cx + (ln - 36) * sc, cy + y * sc), 270, 160,
                  fill=(220, 235, 245, 255), width=6 * s)
    else:  # unknown
        put_cloud(cx, cy, 0.9, dark=True)
    return img.resize((ICON, ICON), Image.LANCZOS)


def draw_moon_phase(phase):
    """phase 0..7 as MOON_PHASE_TYPE (0 = new, 4 = full)."""
    n = 48
    s = SS
    img = Image.new("RGBA", (n * s, n * s), (0, 0, 0, 0))
    px = img.load()
    r = n * s / 2 - 2 * s
    cx = cy = n * s / 2
    # Illuminated fraction going from new (0) to full (4) and back.
    frac = phase / 8.0
    k = math.cos(frac * 2 * math.pi)  # 1 = new, -1 = full
    waxing = phase <= 4
    for y in range(n * s):
        for x in range(n * s):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy > r * r:
                continue
            half = math.sqrt(r * r - dy * dy)
            term = k * half
            lit = (dx > term) if waxing else (dx < -term)
            px[x, y] = (235, 238, 225, 255) if lit else (52, 56, 62, 255)
    return img.resize((n, n), Image.LANCZOS)


# --------------------------------------------------------------------------
# Watch face XML + preview renderer
# --------------------------------------------------------------------------

class Face:
    def __init__(self):
        self.out = []
        self.preview = Image.new("RGBA", (W, W), (0, 0, 0, 255))
        self.pd = ImageDraw.Draw(self.preview)

    def add(self, s):
        self.out.append(s)

    # Preview helpers -----------------------------------------------------
    def p_text(self, x, y, w, h, s, size, color, font, align):
        if not s:
            return
        f = ImageFont.truetype(FONTS[font], int(size))
        bb = self.pd.textbbox((0, 0), s, font=f)
        tw = bb[2] - bb[0]
        tx = {"START": x, "CENTER": x + (w - tw) / 2, "END": x + w - tw}[align] - bb[0]
        asc, desc = f.getmetrics()
        ty = y + (h - (asc + desc)) / 2
        self.pd.text((tx, ty), s, font=f, fill=argb_to_rgba(color))

    def p_image(self, x, y, w, h, name):
        im = Image.open(os.path.join(DRAWABLE, name + ".png")).convert("RGBA").resize((int(w), int(h)), Image.LANCZOS)
        self.preview.alpha_composite(im, (int(x), int(y)))

    # XML helpers ---------------------------------------------------------
    def text(self, x, y, w, h, template, params=(), size=20, color=WHITE, font="barlow_bold",
             align="START", sample=None, upper=False, launch=None, name=None, inner_extra="", ellipsis=False,
             preview=True):
        ps = "".join('<Parameter expression=%s/>' % quoteattr(p) for p in params)
        body = "<Template>%s%s</Template>" % (escape(template), ps) if params else escape(template)
        if upper:
            body = "<Upper>%s</Upper>" % body
        attrs = ' name=%s' % quoteattr(name) if name else ""
        launch_xml = '<Launch target="%s"/>' % launch if launch else ""
        self.add('<PartText x="%d" y="%d" width="%d" height="%d"%s>'
                 '<Text align="%s"%s><Font family="%s" size="%g" color="%s">%s</Font></Text>%s%s</PartText>'
                 % (x, y, w, h, attrs, align, ' ellipsis="TRUE"' if ellipsis else "", font, size, color, body,
                    launch_xml, inner_extra))
        if preview:
            self.p_text(x, y, w, h, sample if sample is not None else template, size, color, font, align)

    def image(self, x, y, w, h, res, preview=True, extra=""):
        self.add('<PartImage x="%d" y="%d" width="%d" height="%d"><Image resource="%s"/>%s</PartImage>'
                 % (x, y, w, h, res, extra))
        if preview:
            self.p_image(x, y, w, h, res)

    def arc(self, r, start, end, color, thickness, end_expr=None, preview_end=None):
        tr = '<Transform target="endAngle" value=%s/>' % quoteattr(end_expr) if end_expr else ""
        self.add('<PartDraw x="0" y="0" width="%d" height="%d"><Arc centerX="%g" centerY="%g" width="%g" height="%g" '
                 'startAngle="%g" endAngle="%g"><Stroke color="%s" thickness="%g" cap="ROUND"/>%s</Arc></PartDraw>'
                 % (W, W, C, C, r * 2, r * 2, start, end, color, thickness, tr))
        e = preview_end if preview_end is not None else end
        bb = (C - r, C - r, C + r, C + r)
        self.pd.arc(bb, start - 90, e - 90, fill=argb_to_rgba(color), width=int(thickness))

    def condition(self, branches, default=None):
        """branches: list of (expression, xml_fragment)."""
        exprs = "".join('<Expression name="c%d"><![CDATA[%s]]></Expression>' % (i, e) for i, (e, _) in enumerate(branches))
        comps = "".join('<Compare expression="c%d">%s</Compare>' % (i, frag) for i, (_, frag) in enumerate(branches))
        dflt = "<Default>%s</Default>" % default if default else ""
        self.add("<Condition><Expressions>%s</Expressions>%s%s</Condition>" % (exprs, comps, dflt))

    def capture(self, fn, preview=False):
        """Runs fn and returns the XML it emitted instead of adding it."""
        saved, self.out = self.out, []
        saved_prev = self.preview.copy()
        fn()
        frag = "".join(self.out)
        self.out = saved
        if not preview:
            self.preview = saved_prev
            self.pd = ImageDraw.Draw(self.preview)
        return frag


WEATHER_GROUPS = [
    ("sun", "1,8"), ("partly_day", "14"), ("cloudy", "2"), ("fog", "3,13"), ("heavy_rain", "4"),
    ("rain", "6,12"), ("snow", "5,7,11"), ("thunder", "9"), ("sleet", "10"), ("wind", "15"),
]


def weather_icon(face, x, y, size, source, is_day=None, sample="partly_day"):
    branches = []
    for icon, codes in WEATHER_GROUPS:
        cond = " || ".join("%s == %s" % (source, c) for c in codes.split(","))
        if is_day and icon in ("sun", "partly_day"):
            night = "moon" if icon == "sun" else "partly_night"
            branches.append(("(%s) && !%s" % (cond, is_day), face.capture(lambda n=night: face.image(x, y, size, size, n))))
        branches.append((cond, face.capture(lambda i=icon: face.image(x, y, size, size, i))))
    face.condition(branches, face.capture(lambda: face.image(x, y, size, size, "unknown")))
    face.p_image(x, y, size, size, sample)


def build_face():
    face = Face()
    face.preview.alpha_composite(Image.open(os.path.join(DRAWABLE, "background.png")).convert("RGBA"))

    face.add('<?xml version="1.0" encoding="utf-8"?>')
    face.add('<!-- Generated by tools/generate_watchface.py. Edit the generator, not this file. -->')
    face.add('<WatchFace width="%d" height="%d">' % (W, W))
    face.add('<Metadata key="CLOCK_TYPE" value="DIGITAL"/>')
    face.add('<Metadata key="PREVIEW_TIME" value="12:48:56"/>')
    face.add('<Scene backgroundColor="#ff000000">')

    # Everything except the time is hidden in ambient mode to save power.
    face.add('<Group name="interactive" x="0" y="0" width="%d" height="%d">' % (W, W))
    face.add('<Variant mode="AMBIENT" target="alpha" value="0"/>')
    face.image(0, 0, W, W, "background")

    # Step goal arc and battery arc.
    face.arc(196, 288, 346, TRACK, 8)
    face.arc(196, 288, 289, GREEN, 8, end_expr="288 + clamp([STEP_PERCENT], 1, 100) * 0.58", preview_end=334)
    face.arc(196, 352, 382, TRACK, 8)
    face.arc(196, 352, 353, "#ff20c8be", 8, end_expr="352 + clamp([BATTERY_PERCENT], 1, 100) * 0.3", preview_end=374)
    face.text(190, 41, 70, 20, "%d%%", ["[BATTERY_PERCENT]"], 17, WHITE, "barlow_semibold", "CENTER",
              SAMPLE["battery"], launch="BATTERY_STATUS")

    # Steps.
    face.text(108, 86, 80, 28, "%d%%", ["[STEP_PERCENT]"], 26, WHITE, "barlow_semibold", "START", SAMPLE["step_pct"])
    face.text(30, 110, 156, 56, "%d", ["[STEP_COUNT]"], 54, WHITE, "barlow_bold", "END", SAMPLE["steps"])
    face.image(184, 64, 66, 104, "runner")

    # Row 1: sunrise / sunset complication (user configurable).
    face.add(
        '<ComplicationSlot x="288" y="48" width="96" height="38" slotId="0" supportedTypes="SHORT_TEXT" '
        'isCustomizable="TRUE" displayName="slot_top">'
        '<DefaultProviderPolicy defaultSystemProvider="SUNRISE_SUNSET" defaultSystemProviderType="SHORT_TEXT"/>'
        '<BoundingBox x="0" y="0" width="96" height="38"/>'
        '<Complication type="SHORT_TEXT">'
        '<PartImage x="0" y="8" width="22" height="22" tintColor="%s"><Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]"/></PartImage>'
        '<PartText x="26" y="0" width="70" height="38"><Text align="START" ellipsis="TRUE">'
        '<Font family="barlow_bold" size="32" color="%s"><Template>%%s<Parameter expression="[COMPLICATION.TEXT]"/></Template></Font>'
        '</Text></PartText></Complication></ComplicationSlot>' % (GREEN, WHITE))
    face.p_image(288, 56, 22, 22, "sun")
    face.p_text(314, 48, 70, 38, SAMPLE["sunrise"], 32, WHITE, "barlow_bold", "START")

    # Row 2: distance estimated from steps (0.762 m per step).
    face.text(286, 88, 84, 38, "%.2f", ["[STEP_COUNT] * 0.000762"], 34, WHITE, "barlow_bold", "START", SAMPLE["distance"])
    face.text(370, 98, 44, 18, "unit_km", ["0"], 14, GREY, "barlow_bold", "START", "KM")

    # Row 3: heart rate with zone.
    face.text(280, 129, 56, 38, "%d", ["round([HEART_RATE])"], 34, WHITE, "barlow_bold", "START", SAMPLE["hr"],
              launch="HEALTH_HEART_RATE")
    face.text(336, 128, 44, 18, "label_zone", ["0"], 13, GREY, "barlow_bold", "START", "ZONE")
    zone = ("[HEART_RATE] &lt; 100 ? 1 : ([HEART_RATE] &lt; 120 ? 2 : ([HEART_RATE] &lt; 140 ? 3 : "
            "([HEART_RATE] &lt; 160 ? 4 : 5)))").replace("&lt;", "<")
    face.text(378, 124, 24, 24, "%d", [zone], 20, GREEN, "barlow_bold", "START", SAMPLE["zone"])
    face.add('<PartDraw x="336" y="151" width="76" height="7">'
             '<RoundRectangle x="0" y="0" width="76" height="7" cornerRadiusX="3.5" cornerRadiusY="3.5"><Fill color="%s"/></RoundRectangle>'
             '<RoundRectangle x="0" y="0" width="7" height="7" cornerRadiusX="3.5" cornerRadiusY="3.5"><Fill color="%s"/>'
             '<Transform target="width" value="7 + 69 * clamp(([HEART_RATE] - 40) / 150, 0, 1)"/></RoundRectangle>'
             '</PartDraw>' % (TRACK, GREEN))
    face.pd.rounded_rectangle((336, 151, 412, 158), radius=3.5, fill=argb_to_rgba(TRACK))
    face.pd.rounded_rectangle((336, 151, 336 + 7 + 69 * 38 / 150, 158), radius=3.5, fill=argb_to_rgba(GREEN))

    # Date and next event.
    face.text(52, 169, 150, 26, "%s %s", ["[MONTH_F]", "[DAY_Z]"], 21, WHITE, "barlow_bold", "START",
              SAMPLE["date"], upper=True, launch="CALENDAR")
    face.add(
        '<ComplicationSlot x="212" y="171" width="200" height="24" slotId="1" supportedTypes="LONG_TEXT SHORT_TEXT" '
        'isCustomizable="TRUE" displayName="slot_event">'
        '<DefaultProviderPolicy defaultSystemProvider="NEXT_EVENT" defaultSystemProviderType="LONG_TEXT"/>'
        '<BoundingBox x="0" y="0" width="200" height="24"/>'
        + "".join(
            '<Complication type="%s"><PartText x="0" y="0" width="200" height="24"><Text align="START" ellipsis="TRUE">'
            '<Font family="barlow_semibold" size="17" color="%s"><Template>%%s %%s'
            '<Parameter expression="[COMPLICATION.TITLE]"/><Parameter expression="[COMPLICATION.TEXT]"/>'
            '</Template></Font></Text></PartText></Complication>' % (t, WHITE)
            for t in ("LONG_TEXT", "SHORT_TEXT"))
        + '</ComplicationSlot>')
    face.p_text(212, 171, 200, 24, SAMPLE["event"], 17, WHITE, "barlow_semibold", "START")

    # Day-of-week column (1 = Sunday ... 7 = Saturday).
    for i in range(1, 8):
        y = 200 + (i - 1) * 19
        active = face.capture(lambda y=y, i=i: (
            face.add('<PartDraw x="34" y="%d" width="70" height="18">'
                     '<RoundRectangle x="6" y="0" width="64" height="18" cornerRadiusX="5" cornerRadiusY="5">'
                     '<Fill color="#ff23272d"/></RoundRectangle>'
                     '<Rectangle x="0" y="4" width="5" height="10"><Fill color="%s"/></Rectangle>'
                     '</PartDraw>' % (y, RED)),
            face.text(44, y, 58, 18, "day_%d" % i, ["0"], 16, WHITE, "barlow_bold", "START")))
        idle = face.capture(lambda y=y, i=i: face.text(48, y, 54, 18, "day_%d" % i, ["0"], 14, DIM, "barlow_bold", "START"))
        face.condition([("[DAY_OF_WEEK] == %d" % i, active)], idle)
    sample_days = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"]
    for i, lbl in enumerate(sample_days):
        y = 200 + i * 19
        if i == 1:
            face.pd.rounded_rectangle((40, y, 104, y + 18), radius=5, fill=(35, 39, 45, 255))
            face.pd.rectangle((34, y + 4, 39, y + 14), fill=argb_to_rgba(RED))
            face.p_text(44, y, 58, 18, lbl, 16, WHITE, "barlow_bold", "START")
        else:
            face.p_text(48, y, 54, 18, lbl, 14, DIM, "barlow_bold", "START")

    # Ghost LCD segments behind the time.
    face.text(98, 208, 224, 76, "88:88", (), 64, "#ff16231c", "dseg7_bold", "END")

    # AM / PM pill (hidden in 24-hour mode).
    ampm = face.capture(lambda: (
        face.add('<PartDraw x="330" y="204" width="58" height="26"><RoundRectangle x="0" y="0" width="58" height="26" '
                 'cornerRadiusX="13" cornerRadiusY="13"><Fill color="#ff102a1d"/></RoundRectangle>'
                 '<RoundRectangle x="1" y="1" width="56" height="24" cornerRadiusX="12" cornerRadiusY="12">'
                 '<Stroke color="#ff1f6b45" thickness="1.5"/></RoundRectangle></PartDraw>'),
        face.text(330, 204, 58, 26, "%s", ["[AMPM_STRING]"], 19, GREEN, "barlow_bold", "CENTER")), preview=False)
    face.condition([("![IS_24_HOUR_MODE]", ampm)])
    face.pd.rounded_rectangle((330, 204, 388, 230), radius=13, fill=(16, 42, 29, 255), outline=(31, 107, 69, 255))
    face.p_text(330, 204, 58, 26, SAMPLE["ampm"], 19, GREEN, "barlow_bold", "CENTER")

    # Seconds.
    face.add('<DigitalClock x="328" y="232" width="68" height="60">'
             '<TimeText format="ss" align="START" x="0" y="0" width="68" height="60">'
             '<Font family="barlow_bold" size="62" color="%s"/></TimeText></DigitalClock>' % GREEN)
    face.p_text(328, 232, 68, 60, SAMPLE["sec"], 62, GREEN, "barlow_bold", "START")

    # Notification count and moon phase.
    face.add('<PartDraw x="396" y="204" width="28" height="28"><Ellipse x="0" y="0" width="28" height="28">'
             '<Fill color="#ff1a1d22"/></Ellipse><Ellipse x="1" y="1" width="26" height="26">'
             '<Stroke color="#ff3a4048" thickness="1.5"/></Ellipse></PartDraw>')
    face.pd.ellipse((396, 204, 424, 232), fill=(26, 29, 34, 255), outline=(58, 64, 72, 255), width=2)
    face.text(396, 204, 28, 28, "%s", ["[UNREAD_NOTIFICATION_COUNT]"], 17, WHITE, "barlow_bold", "CENTER",
              SAMPLE["notif"], launch="MESSAGE")
    face.condition([("[MOON_PHASE_TYPE] == %d" % p, face.capture(lambda p=p: face.image(397, 244, 26, 26, "moon_%d" % p)))
                    for p in range(8)])
    face.p_image(397, 244, 26, 26, "moon_5")

    # Shortcut complication bottom-left (defaults to an app shortcut).
    sc_text = ('<Complication type="SHORT_TEXT"><PartText x="0" y="0" width="36" height="36"><Text align="CENTER" ellipsis="TRUE">'
               '<Font family="barlow_bold" size="14" color="%s"><Template>%%s<Parameter expression="[COMPLICATION.TEXT]"/>'
               '</Template></Font></Text></PartText></Complication>' % GREEN)
    face.add('<ComplicationSlot x="62" y="342" width="36" height="36" slotId="2" '
             'supportedTypes="SMALL_IMAGE MONOCHROMATIC_IMAGE SHORT_TEXT" isCustomizable="TRUE" displayName="slot_shortcut">'
             '<DefaultProviderPolicy defaultSystemProvider="APP_SHORTCUT" defaultSystemProviderType="SMALL_IMAGE"/>'
             '<BoundingOval x="0" y="0" width="36" height="36"/>'
             '<Complication type="SMALL_IMAGE"><PartDraw x="0" y="0" width="36" height="36"><Ellipse x="0" y="0" width="36" height="36">'
             '<Fill color="#ff1a1d22"/></Ellipse></PartDraw>'
             '<PartImage x="6" y="6" width="24" height="24"><Image resource="[COMPLICATION.SMALL_IMAGE]"/></PartImage></Complication>'
             '<Complication type="MONOCHROMATIC_IMAGE"><PartDraw x="0" y="0" width="36" height="36"><Ellipse x="0" y="0" width="36" height="36">'
             '<Fill color="#ff1a1d22"/></Ellipse></PartDraw>'
             '<PartImage x="8" y="8" width="20" height="20" tintColor="%s"><Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]"/></PartImage>'
             '</Complication>%s</ComplicationSlot>' % (GREEN, sc_text))
    face.pd.ellipse((62, 342, 98, 378), fill=(26, 29, 34, 255))
    face.pd.ellipse((71, 351, 89, 369), outline=GREEN_RGB + (255,), width=3)
    face.pd.line((80, 360, 80, 354), fill=GREEN_RGB + (255,), width=2)

    # Weather (Watch Face Format v2 data).
    def weather():
        cols = [172, 258, 344]
        sample_fc = [("TUE", "sun", "72°"), ("WED", "rain", "64°"), ("THU", "partly_day", "55°")]
        for k, cx in enumerate(cols, start=1):
            idx = "WEATHER.DAYS.%d" % k

            def day_column(k=k, cx=cx, idx=idx):
                face.condition(
                    [("(([DAY_OF_WEEK] - 1 + %d) %% 7) + 1 == %d" % (k, d),
                      face.capture(lambda d=d: face.text(cx - 40, 296, 80, 18, "day_%d" % d, ["0"], 15, WHITE,
                                                         "barlow_bold", "CENTER", preview=False)))
                     for d in range(1, 8)])
                weather_icon(face, cx - 42, 316, 36, "[%s.CONDITION_DAY]" % idx)
                face.text(cx - 4, 313, 52, 40, "%d°", ["[%s.TEMPERATURE_HIGH]" % idx], 32, WHITE, "barlow_bold",
                          "START", preview=False)

            face.condition([("[%s.IS_AVAILABLE]" % idx, face.capture(day_column))])
            name, icon, temp = sample_fc[k - 1]
            face.p_text(cx - 40, 296, 80, 18, name, 15, WHITE, "barlow_bold", "CENTER")
            face.p_image(cx - 42, 316, 36, 36, icon)
            face.p_text(cx - 4, 313, 52, 40, temp, 32, WHITE, "barlow_bold", "START")

        face.text(100, 352, 112, 68, "%d°", ["[WEATHER.TEMPERATURE]"], 66, WHITE, "barlow_bold", "END", "58°")
        weather_icon(face, 212, 344, 78, "[WEATHER.CONDITION]", is_day="[WEATHER.IS_DAY]", sample="partly_day")
        face.text(292, 362, 92, 36, "%d/%d", ["[WEATHER.DAY_TEMPERATURE_HIGH]", "[WEATHER.DAY_TEMPERATURE_LOW]"],
                  30, WHITE, "barlow_bold", "START", "62/44")

    available = face.capture(weather, preview=True)
    missing = face.capture(lambda: face.text(120, 352, 210, 40, "weather_unavailable", ["0"], 18, GREY,
                                             "barlow_semibold", "CENTER"))
    face.condition([("[WEATHER.IS_AVAILABLE]", available)], missing)

    # ComplicationSlot must be a direct child of Scene, so lift the slots out of the group.
    slots = [x for x in face.out if x.startswith("<ComplicationSlot")]
    face.out = [x for x in face.out if not x.startswith("<ComplicationSlot")]
    face.add('</Group>')
    for x in slots:
        face.add(x.replace("</ComplicationSlot>", '<Variant mode="AMBIENT" target="alpha" value="0"/></ComplicationSlot>'))

    # Time: always visible, also in ambient mode.
    face.add('<DigitalClock x="98" y="208" width="224" height="76">'
             '<TimeText format="hh:mm" align="END" x="0" y="0" width="224" height="76">'
             '<Font family="dseg7_bold" size="64" color="%s"/></TimeText>'
             '</DigitalClock>' % GREEN)
    face.p_text(98, 208, 224, 76, SAMPLE["time"], 64, GREEN, "dseg7_bold", "END")

    face.add('</Scene>')
    face.add('</WatchFace>')
    return face


def pretty(doc):
    from xml.dom import minidom
    body = doc.split("?>", 1)[1]
    dom = minidom.parseString(body)
    lines = dom.toprettyxml(indent="  ").splitlines()
    out = "\n".join(l for l in lines[1:] if l.strip())
    # Indentation inside text content would be rendered, so keep each Text block on one line.
    out = re.sub(r"<Text\b.*?</Text>", lambda m: re.sub(r"\s+<", "<", re.sub(r">\s+", ">", m.group(0))), out,
                 flags=re.S)
    return '<?xml version="1.0" encoding="utf-8"?>\n' + out + "\n"


def main():
    save(draw_background(), "background")
    save(draw_runner(), "runner")
    for icon in ["sun", "moon", "partly_day", "partly_night", "cloudy", "fog", "rain", "heavy_rain", "snow",
                 "sleet", "thunder", "wind", "unknown"]:
        save(draw_weather_icon(icon), icon)
    for p in range(8):
        save(draw_moon_phase(p), "moon_%d" % p)

    face = build_face()
    xml = "".join(face.out)
    os.makedirs(os.path.join(RES, "raw"), exist_ok=True)
    with open(os.path.join(RES, "raw", "watchface.xml"), "w", encoding="utf-8") as f:
        f.write(pretty(xml))

    prev = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    prev.paste(face.preview, (0, 0), circle_mask(W))
    save(prev, "preview")


if __name__ == "__main__":
    main()
