# dotfiles

Desktop config for this machine: Debian 13 (trixie) + XFCE, with a custom
Conky clock/system widget and a Variety-managed wallpaper that's tinted to
match the widget so the two blend together.

## What's here

- `conky/` — `conky.conf`, the Lua-drawn clock/rings (`clock.lua`), the
  helper scripts it shells out to (`month_calendar.py`, `weather.py`), and
  `principles.conf` — a second, plain-text Conky instance anchored
  `top_left` that displays the Maxims and Core Principles pulled from the
  family reference library's `Stats.html` (on the NAS, see
  `/mnt/nas/files/Family Adminstration/Family Reference Library (HTML)/Stats.html`).
  It's static reference content (not live data), so if the source page's
  Maxims/Principles wording changes, this needs a manual re-copy — there's
  no automatic sync. `moon.conf` is a third instance, anchored
  `middle_middle` and allowed to dominate the screen's middle third, that
  just displays a PNG (`scripts/moon.py` generates it to
  `~/.config/conky/moon_snapshot.png`, re-run every 30 min via `${execpi}`)
  showing an orbit diagram: Earth's ring around the Sun, and the Moon's
  ring around Earth — genuinely non-coplanar, since the Moon's orbit is
  tilted its real ~5.14 degrees off the Earth-Sun plane
  (`MOON_ORBIT_INCLINATION_DEG`) as an actual third (depth) axis, with
  whichever body is nearer the viewer at the moment drawn on top of the
  other. Earth itself is a real lit 3D globe with actual (simplified)
  coastline data from `scripts/continents_data.py` — see that file's own
  docstring for provenance — a night-side shadow whose terminator tilts
  seasonally via a real axial-tilt declination (`AXIAL_TILT_DEG`), a faint
  vertical line through it marking its rotation axis, and a maroon
  triangle marking a home location: solid when it's on the hemisphere
  facing the viewer, a dim hollow outline when real rotation has carried
  it around the back. Body sizes are a deliberate hierarchy (Sun > Earth >
  Moon, see `SUN_R`/`EARTH_R`/`MOON_R`) and orbit distances are pushed in
  close for the widget's scale (see the comments at the top of `moon.py`)
  — none of it is to scale.
  What's real vs. decorative, since it's a mix: the Moon's *phase* (the
  shaded disc — synodic-month approximation from a known new-moon epoch,
  no network call), Earth's spin, night shadow, axial-tilt declination,
  and the home location's real lat/lon position all come from the real
  date/time and real geometry. The Moon's and Earth's *positions on their
  rings*, though, are NOT their real orbital position (that barely moves
  in 30 minutes and reads as static) — they're a continuous made-up
  rotation, Moon once per real day and Earth once per real month, so the
  picture visibly changes each time you glance at it.
- `variety/` — `variety.conf` and `scripts/set_wallpaper`, the hook Variety
  runs on every wallpaper change to tint it to `#1c1c1c` so it matches the
  widget.
- `autostart/conky.desktop` — launches the clock/system Conky widget ~8s
  after login. `autostart/conky-principles.desktop` and
  `autostart/conky-moon.desktop` do the same for the other two widgets.
- `xfce4/` — panel layout, desktop, window manager (xfwm4), keyboard
  shortcuts, and other xfconf settings, plus the panel's launcher
  `.desktop` files.

## Installing on a new machine

```
git clone <this repo> ~/dotfiles
~/dotfiles/install.sh
```

`install.sh` installs the required packages (`conky-all`, `variety`,
`imagemagick`, `xfce4`, `python3-pil`, fonts) -- this step needs network --
then hands off to `link-configs.sh`, which symlinks the Conky/Variety config
into `~/.config` (so future edits there stay tracked in this repo
automatically) and copies the XFCE settings into place. It backs up anything
already at those paths first.

If there's no network yet (or the packages above are already installed),
run `~/dotfiles/link-configs.sh` directly -- it's pure file copying/linking
and touches no network. Widgets just won't actually render until the
packages are in place.

## Things that won't just transfer

This was built and tuned on one specific machine, so a few values are
hardcoded and need a look on different hardware:

- **Network interface** — `conky.conf` reads `wlxccbabd613c26` (this
  machine's USB wifi adapter, an RTL8188EU on the `rtl8xxxu` driver — the
  MacBook Air's built-in wifi isn't used) for IP/signal/up-down speed.
  Check `ip -br link` on a different machine and update those
  `${addr ...}` / `${wireless_link_qual_perc ...}` / `${upspeedf ...}` /
  `${downspeedf ...}` calls if it differs.
- **Battery device** — `clock.lua` reads `${battery_percent BAT0}`. Check
  `/sys/class/power_supply/` — a desktop with no battery will just show 0%
  on that ring (harmless, just pointless).
- **Weather location** — `weather.py` calls `wttr.in/<lat>,<lon>?format=j1`
  with a hardcoded lat/lon. No API key involved, just change the
  coordinates.
- **Screen-resolution-tuned spacing** — `gap_y` in `conky.conf` and
  `SYSTEM_BLOCK_TOP` in `clock.lua` were hand-tuned against a 1366x768
  screen (positioning the widget below a 26px top panel with room for
  everything to fit above the screen bottom). On a different resolution
  the widget still renders, just not perfectly spaced. See "Tuning after a
  resolution change" below. `principles.conf`'s `gap_x`/`gap_y` (30/34) were
  tuned the same way, just for the top-left corner instead. `moon.conf`
  uses `alignment = 'middle_middle'` with `gap_x`/`gap_y` at 0, so it stays
  centered automatically on a different resolution — nothing to retune
  there.
- **Conky window sizing from `${image}`** — unlike plain text, Conky does
  not auto-size `own_window` to fit an `${image ...}` directive (no text
  glyphs to measure), and it only ever anchors the image at the window's
  top-left corner (`${image ... -p 0,0}`) with no centering of its own.
  So `moon.py` pads/centers the rendered diagram onto a fixed canvas
  (`WINDOW_W`/`WINDOW_H`, near the top of `build()`) before saving, and
  `moon.conf`'s `minimum_width`/`minimum_height` must match those two
  constants exactly — otherwise either the image clips inside a too-small
  window, or (if `WINDOW_W`/`WINDOW_H` don't match a bigger window) the
  diagram sits off-center instead of at the window's true middle. This
  deliberately doesn't try to track `moon.py`'s own natural
  `CANVAS_W`/`CANVAS_H` (which shifts whenever orbit/body-size constants
  are tuned) — `WINDOW_W`/`WINDOW_H` just need to stay comfortably bigger
  than the largest `CANVAS_W`/`CANVAS_H` you expect. Check both live with
  `python3 -c "import moon; print(moon.CANVAS_W, moon.CANVAS_H, moon.WINDOW_W, moon.WINDOW_H)"`
  from `conky/scripts/`, or the actual on-screen window with
  `xwininfo -root -tree | grep conky`.
- **XFCE display config** (`displays.xml`) is tied to this monitor's EDID
  and won't match different hardware — XFCE will just fall back to
  defaults, which is safe but means external-monitor/multi-head setups
  need to be redone by hand.

## Tuning after a resolution change

The widget's vertical layout is deliberately explicit rather than
auto-fitting, because Conky's text-flow and the Lua-drawn clock/rings are
two independent layers that have to be kept in sync by hand. If you change
screens:

1. Restart Conky and screenshot the window
   (`xwininfo -root -tree | grep conky` for its window id, then
   `import -window <id> out.png`).
2. Check the window's total height against the new screen height (minus
   the XFCE panel and `gap_y`) — if it's taller, something will get
   clipped at the bottom.
3. Adjust `gap_y` in `conky.conf` to reposition the whole widget, and
   `SYSTEM_BLOCK_TOP` in `clock.lua` (plus the matching `${voffset ...}`
   reservation right after the calendar in `conky.conf`) if the rings
   drift out of alignment with their labels.

## Overlay darkness

The wallpaper tint and the widget are meant to read as a single overlay —
the widget's own window background is fully transparent
(`own_window_argb_value = 0` in `conky.conf`), so all the darkening comes
from `variety/scripts/set_wallpaper`'s `-colorize` value. Bump that number
to go darker/lighter, then either wait for Variety's next rotation or
re-run `convert` by hand on the current wallpaper to see it immediately.
