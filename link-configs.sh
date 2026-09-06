#!/usr/bin/env bash
# Links/copies this repo's configs into place. No network access required --
# safe to run before packages are installed (though Conky/Variety/XFCE won't
# do anything with these configs until they're actually installed).
# Safe to re-run: existing targets are backed up with a .bak-<timestamp> suffix
# before being replaced.
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$HOME/.config"
STAMP="$(date +%Y%m%d%H%M%S)"

backup_and_link() {
    local src="$1" dest="$2"
    mkdir -p "$(dirname "$dest")"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
        mv "$dest" "$dest.bak-$STAMP"
        echo "    backed up existing $dest -> $dest.bak-$STAMP"
    fi
    ln -s "$src" "$dest"
    echo "    linked $dest -> $src"
}

backup_and_copy() {
    local src="$1" dest="$2"
    mkdir -p "$(dirname "$dest")"
    if [ -e "$dest" ]; then
        mv "$dest" "$dest.bak-$STAMP"
        echo "    backed up existing $dest -> $dest.bak-$STAMP"
    fi
    cp "$src" "$dest"
    echo "    copied $dest"
}

echo "==> Linking Conky (symlinked: edits in ~/.config stay in sync with this repo)"
backup_and_link "$DOTFILES/conky/conky.conf" "$CONFIG/conky/conky.conf"
backup_and_link "$DOTFILES/conky/clock.lua" "$CONFIG/conky/clock.lua"
backup_and_link "$DOTFILES/conky/principles.conf" "$CONFIG/conky/principles.conf"
backup_and_link "$DOTFILES/conky/moon.conf" "$CONFIG/conky/moon.conf"
mkdir -p "$CONFIG/conky/scripts"
backup_and_link "$DOTFILES/conky/scripts/month_calendar.py" "$CONFIG/conky/scripts/month_calendar.py"
backup_and_link "$DOTFILES/conky/scripts/weather.py" "$CONFIG/conky/scripts/weather.py"
backup_and_link "$DOTFILES/conky/scripts/moon.py" "$CONFIG/conky/scripts/moon.py"

echo "==> Linking Variety wallpaper config"
backup_and_link "$DOTFILES/variety/variety.conf" "$CONFIG/variety/variety.conf"
mkdir -p "$CONFIG/variety/scripts"
backup_and_link "$DOTFILES/variety/scripts/set_wallpaper" "$CONFIG/variety/scripts/set_wallpaper"
chmod +x "$CONFIG/variety/scripts/set_wallpaper"

echo "==> Installing autostart entries"
backup_and_copy "$DOTFILES/autostart/conky.desktop" "$CONFIG/autostart/conky.desktop"
backup_and_copy "$DOTFILES/autostart/conky-principles.desktop" "$CONFIG/autostart/conky-principles.desktop"
backup_and_copy "$DOTFILES/autostart/conky-moon.desktop" "$CONFIG/autostart/conky-moon.desktop"

echo "==> Restoring XFCE panel/desktop/window-manager settings"
echo "    (xfsettingsd should be stopped/not yet running for these to take on first login)"
mkdir -p "$CONFIG/xfce4/xfconf/xfce-perchannel-xml"
for f in "$DOTFILES/xfce4/xfconf/xfce-perchannel-xml/"*.xml; do
    backup_and_copy "$f" "$CONFIG/xfce4/xfconf/xfce-perchannel-xml/$(basename "$f")"
done
cp -r "$DOTFILES/xfce4/panel/." "$CONFIG/xfce4/panel/" 2>/dev/null || true

cat <<'EOF'

==> Done. Before this looks right, check the machine-specific bits:

  1. Network interface name in conky.conf (currently "wlp1s0") -- run
     `ip -br link` on the new machine and update the ${addr ...},
     ${wireless_link_qual_perc ...}, ${upspeedf ...}, ${downspeedf ...}
     calls if the interface is named differently.

  2. Battery device in clock.lua (currently "BAT0") -- check
     /sys/class/power_supply/ on the new machine; if it's a desktop with
     no battery, that ring will just read 0%, which is harmless but ugly.

  3. conky.conf's gap_y / voffset values and clock.lua's SYSTEM_BLOCK_TOP
     were hand-tuned for a 1366x768 screen. On a different resolution the
     widget will still render, just not perfectly spaced -- see the
     "Tuning after a resolution change" note in README.md.

  4. Weather location is hardcoded to a lat/lon in weather.py (and to the
     same coordinates in moon.py).

  5. Log out and back in (or run `xfce4-panel --restart`) to pick up the
     restored panel/desktop XFCE settings.

  6. Start Conky: `conky -c ~/.config/conky/conky.conf &`,
     `conky -c ~/.config/conky/principles.conf &`, and
     `conky -c ~/.config/conky/moon.conf &` (or just log in -- the
     autostart entries launch all three automatically after an 8s delay).

  Note: none of the above will actually run/render until the packages in
  install.sh (or install-packages.sh) are installed.

EOF
