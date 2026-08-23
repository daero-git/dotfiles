# dotfiles

Desktop config for this machine: Debian 13 (trixie) + XFCE, with a custom
Conky clock/system widget and a Variety-managed wallpaper that's tinted to
match the widget so the two blend together.

## What's here

- `conky/` — `conky.conf`, the Lua-drawn clock/rings (`clock.lua`), and the
  helper scripts it shells out to (`month_calendar.py`, `weather.py`).
- `variety/` — `variety.conf` and `scripts/set_wallpaper`, the hook Variety
  runs on every wallpaper change to tint it to `#1c1c1c` so it matches the
  widget.
- `autostart/conky.desktop` — launches Conky ~8s after login.
- `xfce4/` — panel layout, desktop, window manager (xfwm4), keyboard
  shortcuts, and other xfconf settings, plus the panel's launcher
  `.desktop` files.

## Installing on a new machine

```
git clone <this repo> ~/dotfiles
~/dotfiles/install.sh
```

The script installs the required packages (`conky-all`, `variety`,
`imagemagick`, `xfce4`, fonts), symlinks the Conky/Variety config into
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
  resolution change" below.
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
