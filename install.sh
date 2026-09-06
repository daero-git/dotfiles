#!/usr/bin/env bash
# Bootstraps this dotfiles repo onto a fresh Debian/XFCE install.
# Installs the required packages (needs network), then links the configs
# into place via link-configs.sh. If packages are already installed (or
# there's no network yet), run ./link-configs.sh directly instead.
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Installing packages"
sudo apt-get update
sudo apt-get install -y \
    conky-all lua5.3 \
    variety imagemagick \
    xfce4 xfce4-panel xfwm4 \
    python3 python3-pil curl \
    fonts-noto-core fonts-dejavu-mono

exec "$DOTFILES/link-configs.sh"
