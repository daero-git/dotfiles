"""Renders a snapshot PNG of the current Sun-Earth-Moon arrangement for the
Conky widget in ../moon.conf: Earth's orbit around the Sun, the Moon's orbit
around Earth, and Carleton Place, ON marked on Earth's rim (with a night-side
shadow). No text, just the diagram. Distances are not to scale -- see
EARTH_ORBIT_RX/MOON_ORBIT_RX below.

The Moon's and Earth's positions on their rings are NOT tied to their real
orbital position (that barely moves between 30-minute renders and reads as
static) -- they're a continuous decorative rotation at made-up but
sensible-feeling speeds (see ORBIT_PERIOD constants below). The Moon's
*phase* (shading), Earth's spin (day/night side, local time), and Carleton
Place's position are still computed from the real date/time.
"""
import math
import datetime
import os
import zoneinfo
from PIL import Image, ImageDraw, ImageChops

GOLD = (184, 160, 96)
LIT = (230, 226, 208)
DARK_MOON = (36, 36, 42)
RIM = (255, 255, 255, 130)
SUN_COLOR = (216, 168, 84)
EARTH_COLOR = (94, 148, 138)
LAND_COLOR = (146, 128, 84)
LINE_DIM = (46, 60, 46, 255)
LINE_BACK = (46, 60, 46, 110)  # dim -- the far half of a ring, behind the body it orbits

SYNODIC = 29.530588853
REF_NEW_MOON = datetime.datetime(2000, 1, 6, 18, 14, tzinfo=datetime.timezone.utc)

TZ = zoneinfo.ZoneInfo("America/Toronto")
OUT_PATH = os.path.expanduser("~/.config/conky/moon_snapshot.png")


def local_now(dt_utc=None):
    dt_utc = dt_utc or datetime.datetime.now(datetime.timezone.utc)
    return dt_utc.astimezone(TZ)


def local_day_fraction(local):
    """Fraction [0,1) through the local day, 0=midnight, 0.5=noon."""
    return (local.hour + local.minute / 60 + local.second / 3600) / 24


def moon_phase_fraction(dt=None):
    dt = dt or datetime.datetime.now(datetime.timezone.utc)
    days = (dt - REF_NEW_MOON).total_seconds() / 86400.0
    return (days % SYNODIC) / SYNODIC


# Decorative orbital motion, decoupled from real orbital position -- see
# module docstring. Moon visibly laps Earth once per real day; Earth laps
# the Sun once per real month, about 30x slower, echoing (loosely) how the
# real Moon laps Earth roughly 13x per real year.
MOON_ORBIT_PERIOD_S = 24 * 3600
EARTH_ORBIT_PERIOD_S = 30 * 24 * 3600


def orbit_angle_deg(dt_utc, period_s):
    return (dt_utc.timestamp() % period_s) / period_s * 360


def angle_to_deg(cx, cy, x, y):
    """Angle from (cx, cy) to (x, y), in this file's convention (x=cos, y=cy-sin)."""
    return math.degrees(math.atan2(-(y - cy), x - cx))


def draw_moon_disc(canvas, cx, cy, r, p, scale=3):
    """Composite a shaded moon disc for phase fraction p onto canvas (RGBA), supersampled."""
    ss_size = (canvas.size[0] * scale, canvas.size[1] * scale)
    Cx, Cy, R = cx * scale, cy * scale, r * scale
    k = math.cos(2 * math.pi * p)
    waxing = p < 0.5

    H = Image.new("L", ss_size, 0)
    hd = ImageDraw.Draw(H)
    if waxing:
        hd.rectangle([Cx, Cy - R - 2, Cx + R + 2, Cy + R + 2], fill=255)
    else:
        hd.rectangle([Cx - R - 2, Cy - R - 2, Cx, Cy + R + 2], fill=255)

    ex_r = abs(k) * R
    E = Image.new("L", ss_size, 0)
    if ex_r >= 1:
        ed = ImageDraw.Draw(E)
        ed.ellipse([Cx - ex_r, Cy - R, Cx + ex_r, Cy + R], fill=255)

    lit_mask = ImageChops.subtract(H, E) if k >= 0 else ImageChops.lighter(H, E)

    circle_mask = Image.new("L", ss_size, 0)
    cd = ImageDraw.Draw(circle_mask)
    cd.ellipse([Cx - R, Cy - R, Cx + R, Cy + R], fill=255)
    lit_mask = ImageChops.multiply(lit_mask, circle_mask)

    base = Image.new("RGBA", ss_size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(base)
    bd.ellipse([Cx - R, Cy - R, Cx + R, Cy + R], fill=DARK_MOON + (255,))
    lit_layer = Image.new("RGBA", ss_size, LIT + (255,))
    base.paste(lit_layer, mask=lit_mask)

    rim = Image.new("RGBA", ss_size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    rd.ellipse([Cx - R, Cy - R, Cx + R, Cy + R], outline=RIM, width=max(2, scale))
    base = Image.alpha_composite(base, rim)

    canvas.alpha_composite(base.resize(canvas.size, Image.LANCZOS))


# --- Body sizes -------------------------------------------------------
# Not to scale -- Sun and Moon are drawn the same size as each other on
# purpose (their real size difference is roughly cancelled out by the Sun
# being so much farther away, so equal-size reads as "both prominent,
# neither the focus by virtue of size alone").
SUN_R = 22
EARTH_R = 18
MOON_R = 22

# --- Orbit distances ----------------------------------------------------
# Not to scale, but pushed out so the Sun reads as dramatically farther
# from Earth than the Moon is. Earth's distance from the Sun is +200% over
# its previous value (110 -> 330); the widget is allowed to dominate the
# middle of the screen now, so no clearance budget against the other two
# desktop widgets. Moon's orbit is roughly doubled too (68 -> 136) to keep
# some breathing room between the two rings as the Sun's ring grew so much.
MOON_ORBIT_RX = 136
EARTH_ORBIT_RX = 330
SQUISH = 0.4  # vertical/horizontal ratio -- same tilt for both rings, since both lie in roughly the same plane
MOON_ORBIT_RY = round(MOON_ORBIT_RX * SQUISH)
EARTH_ORBIT_RY = round(EARTH_ORBIT_RX * SQUISH)

# --- Canvas -------------------------------------------------------------
# Fixed rather than measured from rendered content -- Earth's position on
# its ring moves over the year and the Moon's over the month, so an
# auto-cropped bounding box would change size run to run and drift inside
# the Conky window. Sized so the Moon's ring + Moon (its largest possible
# extent from Earth) fits no matter where Earth currently sits on its own
# ring around the Sun.
PAD = 16
MOON_REACH_X = MOON_ORBIT_RX + MOON_R
MOON_REACH_Y = MOON_ORBIT_RY + MOON_R
HALF_W = EARTH_ORBIT_RX + MOON_REACH_X + PAD
HALF_H = EARTH_ORBIT_RY + MOON_REACH_Y + PAD
CANVAS_W = HALF_W * 2
CANVAS_H = HALF_H * 2
SUN_X, SUN_Y = HALF_W, HALF_H

# --- Continents -----------------------------------------------------------
# Rough silhouettes, not accurate coastlines -- just enough to read as
# "land" against the ocean fill. Angles are in Earth's own rotating frame,
# 0 degrees = Carleton Place's meridian (so the marker always sits inside
# the Americas blob), matching real relative longitudes loosely: Africa/
# Europe/Asia sit roughly 95-195 degrees around from Ottawa's longitude.
CONTINENTS = [
    # Americas -- centered on Carleton Place's own meridian
    [(0.25, -20), (0.55, -35), (0.85, -15), (0.9, 10), (0.55, 30), (0.3, 15), (0.15, -5)],
    # Africa/Europe/Asia -- the big landmass roughly opposite-ish
    [(0.45, 95), (0.8, 100), (0.92, 125), (0.85, 155), (0.55, 185), (0.35, 150), (0.3, 120)],
    # East Asia/Australia -- small, further around
    [(0.25, 205), (0.5, 210), (0.45, 235), (0.2, 230)],
]


NIGHT_SHADE = (8, 10, 14, 150)  # semi-transparent -- dims whatever's under it rather than hiding it


def draw_earth(d, cx, cy, r, day_frac, sun_dir_deg):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=EARTH_COLOR)

    # Earth's own spin: local noon (day_frac=0.5) faces the Sun's real
    # current direction, not a fixed angle -- Earth moves around its own
    # ring now, so "toward the Sun" isn't always the same way.
    rot_deg = sun_dir_deg - (day_frac - 0.5) * 360
    for blob in CONTINENTS:
        pts = []
        for radius_frac, local_angle_deg in blob:
            ang = math.radians(rot_deg + local_angle_deg)
            pts.append((cx + radius_frac * r * math.cos(ang), cy - radius_frac * r * math.sin(ang)))
        d.polygon(pts, fill=LAND_COLOR)

    # Carleton Place marker, local frame angle 0 -- always inside the Americas blob.
    loc_ang = math.radians(rot_deg)
    loc_x = cx + (r + 3) * math.cos(loc_ang)
    loc_y = cy - (r + 3) * math.sin(loc_ang)
    d.ellipse([loc_x - 4, loc_y - 4, loc_x + 4, loc_y + 4], fill=GOLD, outline=RIM, width=1)

    # Night side: the hemisphere facing away from the Sun's real direction,
    # traced as an arc across the far side and closed by the straight
    # terminator line back to the start point.
    start, end = sun_dir_deg + 90, sun_dir_deg + 270
    pts = []
    for i in range(25):
        a = math.radians(start + (end - start) * i / 24)
        pts.append((cx + r * math.cos(a), cy - r * math.sin(a)))
    d.polygon(pts, fill=NIGHT_SHADE)


def draw_ring(d, cx, cy, rx, ry, draw_body):
    """Draw an elliptical orbit ring with its far half behind and near half
    in front of the body at its center -- the depth cue that reads as a
    tilted 3D plane instead of a flat circle."""
    bbox = [cx - rx, cy - ry, cx + rx, cy + ry]
    d.arc(bbox, 180, 360, fill=LINE_BACK, width=1)
    draw_body()
    d.arc(bbox, 0, 180, fill=LINE_DIM, width=1)


def edge_point(cx, cy, r, toward_x, toward_y):
    """Point on the circle of radius r around (cx, cy), on the side facing (toward_x, toward_y)."""
    dx, dy = toward_x - cx, toward_y - cy
    dist = math.hypot(dx, dy) or 1
    return (cx + r * dx / dist, cy + r * dy / dist)


def draw_diagram(canvas, d, p, day_frac, now_utc):
    sun_x, sun_y = SUN_X, SUN_Y

    earth_ang = math.radians(orbit_angle_deg(now_utc, EARTH_ORBIT_PERIOD_S))
    earth_x = sun_x + EARTH_ORBIT_RX * math.cos(earth_ang)
    earth_y = sun_y - EARTH_ORBIT_RY * math.sin(earth_ang)
    sun_dir_deg = angle_to_deg(earth_x, earth_y, sun_x, sun_y)

    draw_ring(
        d, sun_x, sun_y, EARTH_ORBIT_RX, EARTH_ORBIT_RY,
        lambda: d.ellipse([sun_x - SUN_R, sun_y - SUN_R, sun_x + SUN_R, sun_y + SUN_R], fill=SUN_COLOR),
    )
    d.line(
        [*edge_point(sun_x, sun_y, SUN_R, earth_x, earth_y), *edge_point(earth_x, earth_y, EARTH_R, sun_x, sun_y)],
        fill=LINE_DIM, width=2,
    )

    moon_ang = math.radians(orbit_angle_deg(now_utc, MOON_ORBIT_PERIOD_S))
    moon_x = earth_x + MOON_ORBIT_RX * math.cos(moon_ang)
    moon_y = earth_y - MOON_ORBIT_RY * math.sin(moon_ang)

    draw_ring(
        d, earth_x, earth_y, MOON_ORBIT_RX, MOON_ORBIT_RY,
        lambda: draw_earth(d, earth_x, earth_y, EARTH_R, day_frac, sun_dir_deg),
    )
    d.line(
        [*edge_point(earth_x, earth_y, EARTH_R, moon_x, moon_y), moon_x, moon_y],
        fill=LINE_DIM, width=2,
    )

    draw_moon_disc(canvas, moon_x, moon_y, MOON_R, p)


def build():
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    local = local_now(now_utc)
    p = moon_phase_fraction(now_utc)
    day_frac = local_day_fraction(local)

    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_diagram(img, d, p, day_frac, now_utc)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    img.save(OUT_PATH)
    return img.size


if __name__ == "__main__":
    build()
