# Hyprland desktop for Arch Linux

This repo restores a Hyprland desktop with Waybar, Hyprpaper, Hyprlock, Hypridle, Hyprlauncher, Dunst, the polkit agent and the current wallpaper. It also carries the Kitty theme, GTK appearance, Dolphin preferences, Cava settings and the Waybar audio, camera, weather and notification widgets.

## Install on a fresh machine

Start with a bootable Arch Linux installation, working networking, graphics drivers for the target GPU, and a normal user with sudo access. The source machine uses Hyprland 0.57.2 with Lua configuration, Hyprpaper 0.8.5 and Waybar 0.16.0. Pacman installs the versions in the configured Arch repositories. Kernel, firmware, GPU driver, bootloader and disk encryption choices belong to the base installation.

Log into a local TTY as the user who will run the desktop. Install Git if needed, then replace YOUR-REPOSITORY-URL with the clone URL from GitHub.

```sh
sudo pacman -Syu --needed git
git clone YOUR-REPOSITORY-URL hyprland-desktop
cd hyprland-desktop
./install.sh
```

The installer runs a full Arch package upgrade, installs the packages in [packages/](packages/), copies the desktop files, applies the GTK preferences, and enables NetworkManager and Bluetooth for the next boot. It enables Hypridle, the polkit agent and audio sockets for the user. UWSM starts the graphical session, Hyprland launches Waybar and Hyprpaper, and Dunst and the portals support D-Bus activation. The default sound server is PulseAudio, matching the source machine. A target already running the pipewire-pulse package keeps that backend and uses WirePlumber.

Reboot and log in on **tty1**. Bash and Zsh logins start Hyprland automatically. With another shell, or after installing with `--manual-login`, start it from a local TTY with `uwsm start hyprland.desktop`. A display manager can use the **Hyprland (uwsm-managed)** session.

| Installer option | Effect |
| --- | --- |
| `--dry-run` | Print the package and service plan. |
| `--config-only` | Copy the desktop files and configure the login hook using Python 3. Skip package installation, service enablement and GSettings. |
| `--manual-login` | Skip adding the tty1 hook to the active Bash or Zsh login profile. Combine with either option above. |

## Using the desktop

| Shortcut | Action |
| --- | --- |
| Super + Space | Open the launcher |
| Super + Q / E / F | Open Kitty / Dolphin / Firefox |
| Super + L | Lock the screen |
| Super + C / M | Close a window / end the session |
| Volume keys or knob | Adjust the default output by one percentage point |

Hypridle locks after 30 minutes of inactivity and turns off the display five minutes later. The monitor rule uses each display’s preferred mode and automatic scaling. Waybar follows the default network route so Ethernet and Wi-Fi work across machines. Use `nmtui` for a new network and `blueman-manager` to pair Bluetooth devices.

## Weather and wallpaper

The weather widget reads coordinates from `$XDG_CONFIG_HOME/waybar/weather-location.json` (normally `~/.config/waybar/weather-location.json`). For a fresh clone, create `local/weather-location.json` before installation, or create the installed file later. The `local/` directory is ignored by Git. Keep a private copy if you want the same location after a reinstall. This example uses London.

```json
{"label": "London", "latitude": 51.5072, "longitude": -0.1276}
```

The widget sends those coordinates to Open-Meteo and displays the forecast in Fahrenheit. Until configured, it displays a dash. The installer resolves the wallpaper path for the target user in both Hyprlock and Hyprpaper. To change the image on every machine, replace `config/hypr/wallpaper.png` in the repo and reinstall the files.

## Updates and recovery

Edit the files under `config/` in this repo, commit them, and run `./install.sh --config-only` on each machine after pulling. The installer copies files so the checkout can move afterwards. Log out and back in to load all changes.

Before replacing a differing file, the installer saves the original under `${XDG_STATE_HOME:-$HOME/.local/state}/hyprland-desktop/backups/install-*/` and prints the exact directory. The backup mirrors configuration paths under `config/` and login profiles under `login/`. Copy the relevant original back to its installed location to restore it. Identical files are skipped. The full installer also sets the GNOME interface color scheme, icon theme, cursor theme and cursor size.

To check a new installation from within Hyprland:

```sh
hyprctl configerrors
systemctl --user status hypridle hyprpolkitagent
pactl info
nmcli device status
```

The repo contains desktop settings and assets. Wi-Fi credentials, Bluetooth pairings, browser profiles, keyrings and personal app accounts are per-machine data.
