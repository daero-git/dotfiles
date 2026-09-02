"""Renders a snapshot PNG of the current Sun-Earth-Moon arrangement for the
Conky widget in ../moon.conf: Earth's orbit around the Sun, the Moon's orbit
around Earth, and Carleton Place, ON marked on a real 3D globe (with a
night-side shadow). No text, just the diagram. Distances are not to scale --
see EARTH_ORBIT_RX/MOON_ORBIT_RX below.

The Moon's and Earth's positions on their rings are NOT tied to their real
orbital position (that barely moves between 30-minute renders and reads as
static) -- they're a continuous decorative rotation at made-up but
sensible-feeling speeds (see ORBIT_PERIOD constants below). The Moon's
*phase* (shading), Earth's spin (day/night side, local time, and Carleton
Place's real latitude/longitude), and the Sun's shading are still computed
from the real date/time and real geometry.

Earth is rendered as an actual lit sphere (viewed from a fixed elevation
angle, EARTH_VIEW_TILT_DEG) rather than a flat rotating disc -- this is what
lets Carleton Place's real latitude (CARLETON_PLACE_LAT_DEG) place it
correctly, instead of a rim-angle scheme that had no notion of latitude at
all and could swing the marker up near the poles as the day rotated it.
Carleton Place itself is marked with a small maroon triangle. A faint
vertical line through the globe is its rotation axis (see AXIS_LINE); the
day/night terminator tilts relative to that axis over the widget's fake
"year" via a real axial-tilt declination (see AXIAL_TILT_DEG), the same
mechanism that causes real seasons.

The Earth-Sun ring and the Moon-Earth ring are NOT coplanar, matching real
life: Earth's own orbit defines the reference plane (there's nothing for it
to be inclined relative to), but the Moon's orbit around Earth really is
tilted about 5.14 degrees off that plane (see MOON_ORBIT_INCLINATION_DEG).
That tilt is modeled as a genuine third (Z) axis, not just a flatter ellipse
-- the Moon has real depth, so it's drawn in front of or behind Earth
depending which is actually closer to the viewer each render (see
moon_orbit_point's depth value and its use in draw_diagram), and its orbit
ring is traced point-by-point rather than assumed to be a flat ellipse.
"""
import math
import datetime
import os
import zoneinfo
from PIL import Image, ImageDraw, ImageChops

from continents_data import CONTINENTS

MAROON = (115, 20, 30)
MAROON_DIM = (200, 90, 100, 130)  # marker outline when Carleton Place is on the far side right now
LIT = (230, 226, 208)
DARK_MOON = (36, 36, 42)
RIM = (255, 255, 255, 130)
SUN_COLOR = (216, 168, 84)
EARTH_COLOR = (94, 148, 138)
LAND_COLOR = (146, 128, 84)
LINE_DIM = (46, 60, 46, 255)
LINE_BACK = (46, 60, 46, 110)  # dim -- the far half of a ring, behind the body it orbits
AXIS_LINE = (222, 226, 214, 130)  # Earth's rotation axis -- faint, reads as structure not a highlight

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


def draw_sun(canvas, cx, cy, r, scale=3):
    """Composite a limb-darkened sun disc onto canvas (RGBA), supersampled --
    a radial gradient instead of a flat fill so it reads as a sphere too."""
    ss = scale
    R = r * ss
    size = (2 * R + 4, 2 * R + 4)
    Cx, Cy = size[0] / 2, size[1] / 2
    bright = tuple(min(255, c + 45) for c in SUN_COLOR)

    core = Image.new("RGBA", size, (0, 0, 0, 0))
    px = core.load()
    for j in range(size[1]):
        ny = (j - Cy) / R
        for i in range(size[0]):
            nx = (i - Cx) / R
            d2 = nx * nx + ny * ny
            if d2 > 1:
                continue
            t = 1 - d2  # 1 at center, 0 at the limb
            col = tuple(int(bright[k] * t + SUN_COLOR[k] * (1 - t)) for k in range(3))
            px[i, j] = col + (255,)

    rim = ImageDraw.Draw(core)
    rim.ellipse([Cx - R, Cy - R, Cx + R, Cy + R], outline=RIM, width=max(2, ss))

    canvas.alpha_composite(
        core.resize((size[0] // ss, size[1] // ss), Image.LANCZOS),
        (round(cx - size[0] / (2 * ss)), round(cy - size[1] / (2 * ss))),
    )


# --- Body sizes -------------------------------------------------------
# Not to scale. Sun 100% bigger, Earth 50% bigger, Moon 50% smaller than
# their original equal-ish sizes -- a deliberate size hierarchy (Sun >
# Earth > Moon) rather than the previous "Sun and Moon the same size."
SUN_R = 44
EARTH_R = 27
MOON_R = 11

# --- Orbit distances ----------------------------------------------------
# Not to scale, but pushed out so the Sun reads as dramatically farther
# from Earth than the Moon is. Earth 25% closer to the Sun and the Moon 25%
# closer to Earth than their previous values (330 -> 248, 136 -> 102).
MOON_ORBIT_RX = 102
EARTH_ORBIT_RX = 248
SQUISH = 0.4  # vertical/horizontal ratio -- same viewing angle for both rings, since both are seen by the same camera
EARTH_ORBIT_RY = round(EARTH_ORBIT_RX * SQUISH)

# The "camera" elevation angle implied by SQUISH (a flat ring's minor/major
# axis ratio, viewed from elevation angle t above its own plane, is sin(t)).
# Used to project the Moon's inclined orbit (see below) into the same scene,
# so both rings read as viewed by one consistent camera rather than two
# independently-squished ellipses.
ORBIT_VIEW_TILT_RAD = math.asin(SQUISH)

# Real average inclination of the Moon's orbital plane to the ecliptic
# (Earth's own orbital plane, which by definition has no inclination
# relative to itself). This is what actually keeps the two rings from being
# coplanar -- see moon_orbit_point below.
MOON_ORBIT_INCLINATION_DEG = 5.145

# The inclined orbit's max vertical screen reach is MOON_ORBIT_RX *
# sin(view_tilt + inclination), a bit more than the flat-ellipse case (just
# SQUISH) would give -- needed for accurate canvas padding below so the
# Moon can't clip the window edge now that it swings slightly further up
# and down than a flat ring would.
MOON_ORBIT_RY = round(MOON_ORBIT_RX * math.sin(ORBIT_VIEW_TILT_RAD + math.radians(MOON_ORBIT_INCLINATION_DEG)))

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

# --- Earth globe geometry -------------------------------------------------
# Earth is rendered as an actual sphere, viewed from a fixed elevation angle
# above its equatorial plane (0 = edge-on, 90 = looking straight down over a
# pole). This is what gives Carleton Place a real latitude band to sit in,
# instead of the old flat-disc rim scheme where its position was really just
# encoding longitude/time-of-day and could wander up to what looked like a
# pole.
EARTH_VIEW_TILT_DEG = 28
CARLETON_PLACE_LAT_DEG = 45.13
CARLETON_PLACE_LON_DEG = -76.14

# Real axial tilt -- the sun's declination (its angle above/below Earth's
# equator) swings +-AXIAL_TILT_DEG over a year as a result, which is what
# actually causes seasons. Tied to the widget's own decorative fake "year"
# (sun_dir_deg's cycle around EARTH_ORBIT_PERIOD_S) rather than the real
# calendar, same spirit as the other made-up-but-real-feeling orbital
# motion in this file -- so the terminator visibly tilts season-to-season
# instead of always cutting straight through the poles.
AXIAL_TILT_DEG = 23.44

# South of here is rendered as solid land (Antarctica) without consulting
# CONTINENTS -- the real landmass wraps essentially all 360 degrees of
# longitude, which the (center_lon, rings) polygon scheme below isn't set up
# to represent as one shape. See continents_data.py's docstring.
POLAR_LAT_CUTOFF = -63.27

NIGHT_SHADE = (8, 10, 14, 150)  # semi-transparent -- dims whatever's under it rather than hiding it

# Bounding box per CONTINENTS entry (lat_min, lat_max, lon_min, lon_max, in
# the same center_lon-relative frame as its rings), padded slightly -- lets
# the per-pixel land test below skip the expensive ray-cast for landmasses
# nowhere near the point, which is most of them for most pixels.
_CONTINENT_BBOXES = []
for _center, _rings in CONTINENTS:
    _lats = [pt[0] for pt in _rings[0]]
    _lons = [pt[1] for pt in _rings[0]]
    _CONTINENT_BBOXES.append((min(_lats) - 0.5, max(_lats) + 0.5, min(_lons) - 0.5, max(_lons) + 0.5))


def normalize_signed_deg(x):
    """Wrap an angle in degrees to [-180, 180)."""
    return ((x + 180) % 360) - 180


def _ray_cast(x, y, ring):
    """Even-odd ray-casting test for whether (x, y) is inside a single ring
    of (lat, lon) points."""
    inside = False
    n = len(ring)
    for i in range(n):
        y1, x1 = ring[i]
        y2, x2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xin = x1 + (y - y1) / (y2 - y1) * (x2 - x1)
            if x < xin:
                inside = not inside
    return inside


def is_land(lat, real_lon):
    """Whether real-world (lat, real_lon) falls on land, per CONTINENTS plus
    the Antarctica latitude cutoff."""
    if lat <= POLAR_LAT_CUTOFF:
        return True
    for (center, rings), (lat_min, lat_max, lon_min, lon_max) in zip(CONTINENTS, _CONTINENT_BBOXES):
        if lat < lat_min or lat > lat_max:
            continue
        x = normalize_signed_deg(real_lon - center)
        if x < lon_min or x > lon_max:
            continue
        if not _ray_cast(x, lat, rings[0]):
            continue
        if any(_ray_cast(x, lat, hole) for hole in rings[1:]):
            continue
        return True
    return False


def earth_camera_basis(tilt_deg):
    """Orthonormal (right, up, camera) basis for viewing Earth from
    elevation tilt_deg above its equatorial plane, in this file's screen
    convention (up subtracts from pixel y, matching angle_to_deg elsewhere)."""
    t = math.radians(tilt_deg)
    right = (1.0, 0.0, 0.0)
    up = (0.0, math.sin(t), math.cos(t))
    cam = (0.0, -math.cos(t), math.sin(t))
    return right, up, cam


def latlon_to_unit(lat_deg, lon_deg):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat))


def dot3(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def draw_earth(canvas, d, cx, cy, r, day_frac, sun_dir_deg, scale=3):
    """Composite a lit, rotating 3D globe onto canvas (RGBA), supersampled
    the same way draw_moon_disc is."""
    right, up, cam = earth_camera_basis(EARTH_VIEW_TILT_DEG)

    # Earth's own spin: local noon (day_frac=0.5) faces the Sun's real
    # current direction, not a fixed angle -- Earth moves around its own
    # ring now, so "toward the Sun" isn't always the same way.
    rot_deg = sun_dir_deg - (day_frac - 0.5) * 360

    # Declination: the sun's angle above/below the equatorial plane, tied to
    # the same fake-year cycle as sun_dir_deg (see AXIAL_TILT_DEG above).
    decl_rad = math.radians(AXIAL_TILT_DEG) * math.sin(math.radians(sun_dir_deg))
    sun_dir_rad = math.radians(sun_dir_deg)
    sun_dir3 = (
        math.cos(sun_dir_rad) * math.cos(decl_rad),
        math.sin(sun_dir_rad) * math.cos(decl_rad),
        math.sin(decl_rad),
    )

    ss = scale
    R = r * ss
    size = (2 * R + 4, 2 * R + 4)
    Cx, Cy = size[0] / 2, size[1] / 2

    globe = Image.new("RGBA", size, (0, 0, 0, 0))
    px = globe.load()
    for j in range(size[1]):
        ny = (Cy - j) / R  # screen "up" -- matches the cy-r*sin() convention used elsewhere
        for i in range(size[0]):
            nx = (i - Cx) / R
            d2 = nx * nx + ny * ny
            if d2 > 1:
                continue
            nz = math.sqrt(1 - d2)  # always the near hemisphere by construction
            p = (
                right[0] * nx + up[0] * ny + cam[0] * nz,
                right[1] * nx + up[1] * ny + cam[1] * nz,
                right[2] * nx + up[2] * ny + cam[2] * nz,
            )
            lat = math.degrees(math.asin(max(-1.0, min(1.0, p[2]))))
            world_lon = math.degrees(math.atan2(p[1], p[0]))
            # undo Earth's spin, then re-anchor on Carleton Place's real
            # longitude to get this pixel's real-world longitude
            real_lon = world_lon - rot_deg + CARLETON_PLACE_LON_DEG

            color = LAND_COLOR if is_land(lat, real_lon) else EARTH_COLOR
            if dot3(p, sun_dir3) <= 0:
                nr, ng, nb, na = NIGHT_SHADE
                a = na / 255
                color = tuple(int(c * (1 - a) + n * a) for c, n in zip(color, (nr, ng, nb)))
            px[i, j] = color + (255,)

    rim = ImageDraw.Draw(globe)
    rim.ellipse([Cx - R, Cy - R, Cx + R, Cy + R], outline=RIM, width=max(2, ss))

    canvas.alpha_composite(
        globe.resize((size[0] // ss, size[1] // ss), Image.LANCZOS),
        (round(cx - size[0] / (2 * ss)), round(cy - size[1] / (2 * ss))),
    )

    # Rotation axis: a straight vertical line through the globe (north pole
    # is world +Z, which this camera basis always projects to pure "up",
    # since right=(1,0,0) has no Z component -- see earth_camera_basis).
    # Fixed relative to the camera regardless of spin or declination, the
    # way a real axis stays fixed in space while the sun's angle to it
    # changes through the year.
    axis_up = dot3(up, (0.0, 0.0, 1.0))
    axis_ext = r * 1.3
    d.line(
        [cx, cy - axis_ext * axis_up, cx, cy + axis_ext * axis_up],
        fill=AXIS_LINE, width=1,
    )

    # Carleton Place marker: real latitude + real local-time longitude.
    # Always drawn (a "where am I" marker that vanishes for hours at a time
    # whenever the real rotation carries it to the far side isn't useful),
    # but hollow/dim when it's actually on the far hemisphere right now, so
    # the globe still reads honestly -- solid means "facing you," faint
    # outline means "around the back."
    loc_p = latlon_to_unit(CARLETON_PLACE_LAT_DEG, rot_deg)
    lx = cx + r * dot3(loc_p, right)
    ly = cy - r * dot3(loc_p, up)
    tri = [(lx, ly - 5), (lx - 4.5, ly + 3.5), (lx + 4.5, ly + 3.5)]
    if dot3(loc_p, cam) > 0:
        d.polygon(tri, fill=MAROON, outline=RIM)
    else:
        d.polygon(tri, outline=MAROON_DIM)


def draw_ring(d, cx, cy, rx, ry, draw_body):
    """Draw an elliptical orbit ring with its far half behind and near half
    in front of the body at its center -- the depth cue that reads as a
    tilted 3D plane instead of a flat circle. Only correct for a ring with
    no inclination of its own (the Sun-Earth ring): with zero inclination,
    the near/far crossover really does fall exactly at the ellipse's
    left/right ends, which is all a bounding-box arc can draw. The Moon's
    inclined ring uses moon_orbit_point + draw_inclined_moon_ring instead,
    since its near/far crossover shifts away from those points."""
    bbox = [cx - rx, cy - ry, cx + rx, cy + ry]
    d.arc(bbox, 180, 360, fill=LINE_BACK, width=1)
    draw_body()
    d.arc(bbox, 0, 180, fill=LINE_DIM, width=1)


def moon_orbit_point(moon_ang, earth_x, earth_y):
    """Screen (x, y) and camera-relative depth for the point at angle
    moon_ang (radians) around Earth's real, inclined orbital circle.

    The orbit is built in Earth's own local frame: x_local runs along the
    line of nodes (where the Moon's plane crosses the ecliptic, taken here
    as a fixed reference direction since real nodal precession is far too
    slow to matter at this widget's decorative timescale), y_local/z_local
    are that circle rotated MOON_ORBIT_INCLINATION_DEG out of the ecliptic.
    Projecting through the same camera used for the Sun-Earth ring (see
    ORBIT_VIEW_TILT_RAD) is what keeps the two rings looking like one
    consistent 3D scene instead of two independently-squished ellipses.
    """
    incl = math.radians(MOON_ORBIT_INCLINATION_DEG)
    x_local = MOON_ORBIT_RX * math.cos(moon_ang)
    y_perp = MOON_ORBIT_RX * math.sin(moon_ang)
    y_ecl = y_perp * math.cos(incl)
    z_ecl = y_perp * math.sin(incl)

    t = ORBIT_VIEW_TILT_RAD
    sx = earth_x + x_local
    sy = earth_y - (y_ecl * math.sin(t) + z_ecl * math.cos(t))
    depth = -y_ecl * math.cos(t) + z_ecl * math.sin(t)  # >0 = nearer the viewer than Earth's center
    return sx, sy, depth


def draw_inclined_moon_ring(d, earth_x, earth_y, steps=72):
    """Trace the Moon's inclined orbit as a polyline (not a flat ellipse --
    PIL can't draw a tilted-circle projection with its arc primitive), each
    segment styled by its own actual depth rather than a fixed near/far
    split."""
    pts = [moon_orbit_point(2 * math.pi * i / steps, earth_x, earth_y) for i in range(steps + 1)]
    for (x1, y1, d1), (x2, y2, d2) in zip(pts, pts[1:]):
        color = LINE_DIM if (d1 + d2) > 0 else LINE_BACK
        d.line([x1, y1, x2, y2], fill=color, width=1)


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
        lambda: draw_sun(canvas, sun_x, sun_y, SUN_R),
    )
    d.line(
        [*edge_point(sun_x, sun_y, SUN_R, earth_x, earth_y), *edge_point(earth_x, earth_y, EARTH_R, sun_x, sun_y)],
        fill=LINE_DIM, width=2,
    )

    moon_ang = math.radians(orbit_angle_deg(now_utc, MOON_ORBIT_PERIOD_S))
    moon_x, moon_y, moon_depth = moon_orbit_point(moon_ang, earth_x, earth_y)

    draw_inclined_moon_ring(d, earth_x, earth_y)
    d.line(
        [*edge_point(earth_x, earth_y, EARTH_R, moon_x, moon_y), moon_x, moon_y],
        fill=LINE_DIM, width=2,
    )

    # Whichever body is actually nearer the viewer this moment is drawn on
    # top -- real depth now, not a fixed draw order, since the Moon's
    # inclined orbit genuinely carries it in front of and behind Earth.
    draw_earth_body = lambda: draw_earth(canvas, d, earth_x, earth_y, EARTH_R, day_frac, sun_dir_deg)
    draw_moon_body = lambda: draw_moon_disc(canvas, moon_x, moon_y, MOON_R, p)
    if moon_depth > 0:
        draw_earth_body()
        draw_moon_body()
    else:
        draw_moon_body()
        draw_earth_body()


# moon.conf displays this file at a fixed screen position with no `-p`
# centering logic of its own -- conky just anchors the image at the
# window's top-left corner. So the diagram is centered onto a canvas
# exactly matching moon.conf's own minimum_width/minimum_height here,
# rather than saved at its own natural (and orbit/size-tuning-dependent)
# CANVAS_W x CANVAS_H: that would anchor the *window* on screen but leave
# the diagram itself sitting top-left inside it, off true screen-center,
# whenever the diagram is smaller than the window's padded minimum size
# (which it deliberately is, so the diagram can't clip the window edge --
# see moon.conf's own comment on minimum_height/minimum_width).
WINDOW_W = 1150
WINDOW_H = 550


def build():
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    local = local_now(now_utc)
    p = moon_phase_fraction(now_utc)
    day_frac = local_day_fraction(local)

    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_diagram(img, d, p, day_frac, now_utc)

    out = Image.new("RGBA", (WINDOW_W, WINDOW_H), (0, 0, 0, 0))
    offset = ((WINDOW_W - CANVAS_W) // 2, (WINDOW_H - CANVAS_H) // 2)
    out.alpha_composite(img, offset)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    out.save(OUT_PATH)
    return out.size


if __name__ == "__main__":
    build()
