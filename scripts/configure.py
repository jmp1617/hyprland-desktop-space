"""Install the repository's desktop files as the logged-in user."""
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
home = Path.home()
config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
state = Path(os.environ.get("XDG_STATE_HOME") or home / ".local/state")
backup = None


def install(target, content, backup_name, mode=0o644):
    global backup
    exists = target.exists() or target.is_symlink()
    if exists:
        if target.is_file() and target.read_bytes() == content:
            return
        if target.exists() and not target.is_file():
            sys.exit(f"Expected a regular file at {target}. Move it aside before installing.")
        if backup is None:
            parent = state / "hyprland-desktop/backups"
            parent.mkdir(parents=True, exist_ok=True)
            backup = Path(tempfile.mkdtemp(prefix="install-", dir=parent))
            print(f"Saving replaced files in {backup}", flush=True)
        original = backup / backup_name
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, original, follow_symlinks=False)
        if target.is_file():
            mode = stat.S_IMODE(target.stat().st_mode) & 0o777
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as f:
        tmp = Path(f.name)
        try:
            f.write(content)
            f.flush()
            tmp.chmod(mode)
            tmp.replace(target)
        finally:
            tmp.unlink(missing_ok=True)
    print(f"Installed {target}")


def configure_login():
    shell = Path(os.environ.get("SHELL", "")).name
    if shell == "zsh":
        profile = Path(os.environ.get("ZDOTDIR") or home) / ".zprofile"
    elif shell == "bash":
        profiles = [home / name for name in (".bash_profile", ".bash_login", ".profile")]
        profile = next((p for p in profiles if p.is_file()), profiles[0])
    else:
        print("Start the desktop from a local TTY with: uwsm start hyprland.desktop")
        return
    hook = b'. "${XDG_CONFIG_HOME:-$HOME/.config}/hypr/tty-login.sh"'
    current = profile.read_bytes() if profile.is_file() else b""
    if hook in current.splitlines() or re.search(rb"(?m)^\s*exec uwsm start hyprland\.desktop\s*$", current):
        return
    install(profile, current + b"\n" + hook + b"\n", Path("login") / profile.name)


for source in sorted((repo / "config").rglob("*")):
    if source.is_file():
        relative = source.relative_to(repo / "config")
        data = source.read_bytes()
        if relative.as_posix() in {"hypr/hyprpaper.conf", "hypr/hyprlock.conf"}:
            data = data.replace(b"@WALLPAPER@", os.fsencode(config / "hypr/wallpaper.png"))
        install(config / relative, data, Path("config") / relative)

weather = repo / "local/weather-location.json"
if weather.is_file():
    install(config / "waybar/weather-location.json", weather.read_bytes(),
            Path("config/waybar/weather-location.json"), 0o600)
if "--manual-login" not in sys.argv:
    configure_login()
