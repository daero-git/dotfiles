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
  showing a nested orbit diagram: Earth's ring around the Sun, the Moon's
  ring around Earth, and Earth itself with a night-side shadow and a gold
  marker for Carleton Place. Sun and Moon are drawn the same size as each
  other and much closer together than reality (see the sizing/distance
  comments at the top of `moon.py`) — none of it is to scale.
  What's real vs. decorative, since it's a mix: the Moon's *phase* (the
  shaded disc — synodic-month approximation from a known new-moon epoch,
  no network call), Earth's spin (the night shadow and Carleton Place's
  position both track real local time via `America/Toronto`), and Earth's
  own day/night direction all come from the real date/time. The Moon's and
  Earth's *positions on their rings*, though, are NOT their real orbital
  position (that barely moves in 30 minutes and reads as static) — they're
  a continuous made-up rotation, Moon once per real day and Earth once per
  real month, so the picture visibly changes each time you glance at it.
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

The script installs the required packages (`conky-all`, `variety`,
`imagemagick`, `xfce4`, `python3-pil`, fonts), symlinks the Conky/Variety config into
`~/.config` (so future edits there stay tracked in this repo automatically),
and copies the XFCE settings into place. It backs up anything already at
those paths first.

## Things that won't just transfer

This was built and tuned on one specific machine, so a few values are
hardcoded and need a look on different hardware:

- **Network interface** — `conky.conf` reads `wlp1s0` for IP/signal/up-down
  speed. Check `ip -br link` on the new machine and update those
  `${addr ...}` / `${wireless_link_qual_perc ...}` / `${upspeedf ...}` /
  `${downspeedf ...}` calls if it differs.
- **Battery device** — `clock.lua` reads `${battery_percent BAT0}`. Check
  `/sys/class/power_supply/` — a desktop with no battery will just show 0%
  on that ring (harmless, just pointless).
- **Weather location** — `weather.py` calls
  `wttr.in/Carleton+Place,ON?format=j1`, hardcoded. No API key involved,
  just change the location string.
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
  glyphs to measure), so `moon.conf` sets `minimum_width`/`minimum_height`
  explicitly to match `moon.py`'s `CANVAS_W`/`CANVAS_H` (printed by running
  the script directly, or read off its `build()` return value) and the
  `${image ... -s WxH}` size in the same file. Conky's actual window also
  runs noticeably larger than the image (padding that scales with size,
  not a fixed amount) — if you're relying on a specific clearance from the
  other widgets, check the live window with `xwininfo -root -tree | grep
  conky`, don't just compare against the raw image dimensions.
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
