#!/usr/bin/env bash
set -euo pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$repo"
usage() {
    cat <<'HELP'
Usage: ./install.sh [--dry-run | --config-only] [--manual-login]
  Default         Install Arch packages, desktop files, preferences and services.
  --dry-run       Show the package and service plan without changing anything.
  --config-only   Install files and the login hook (requires Python 3).
  --manual-login  Skip adding a tty1 autostart hook to your bash/zsh login file.
HELP
}
mode=full
login_flags=()
for arg in "$@"; do
    case "$arg" in
        --dry-run|--config-only)
            if [[ $mode != full ]]; then usage >&2; exit 2; fi
            mode=${arg#--} ;;
        --manual-login) login_flags=(--manual-login) ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done

if [[ $mode != dry-run && $EUID == 0 ]]; then
    echo 'Run as the target desktop user. The installer invokes sudo for system changes.' >&2
    exit 1
fi
if [[ $mode == config-only ]]; then
    exec python3 scripts/configure.py "${login_flags[@]}"
fi
if [[ ! -f /etc/arch-release ]] || ! command -v pacman >/dev/null; then
    echo 'Full installation requires an installed Arch Linux system with pacman.' >&2
    exit 1
fi

audio=pulseaudio
audio_units=(pulseaudio.socket)
if pacman -Qq pipewire-pulse >/dev/null 2>&1; then
    audio=pipewire-pulse
    audio_units=(pipewire-pulse.socket wireplumber.service)
fi
mapfile -t packages < <(cat packages/{desktop,apps}.txt "packages/$audio.txt")
system_units=(NetworkManager.service bluetooth.service)
user_units=(hypridle.service hyprpolkitagent.service pipewire.socket "${audio_units[@]}")

if [[ $mode == dry-run ]]; then
    printf 'Arch upgrade and packages (%s):\n' "$audio"
    printf '  %s\n' "${packages[@]}"
    printf 'Enable system units: %s\nEnable user units: %s\n' "${system_units[*]}" "${user_units[*]}"
    printf 'Install desktop files under %s and apply GTK preferences.\n' "${XDG_CONFIG_HOME:-$HOME/.config}"
    if (( ${#login_flags[@]} == 0 )); then echo 'Configure tty1 autostart for bash or zsh.'; fi
    exit 0
fi

sudo pacman -Syu --needed "${packages[@]}"
python3 scripts/configure.py "${login_flags[@]}"
sudo systemctl enable "${system_units[@]}"
systemctl --user enable "${user_units[@]}"
gsettings set org.gnome.desktop.interface color-scheme prefer-dark
gsettings set org.gnome.desktop.interface icon-theme Papirus-Dark
gsettings set org.gnome.desktop.interface cursor-size 24
gsettings set org.gnome.desktop.interface cursor-theme default
echo 'Installation complete. Reboot, then log in locally to start the desktop.'
