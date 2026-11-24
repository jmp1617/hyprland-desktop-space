import json
import subprocess

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk


def pulse(*args):
    result = subprocess.run(
        ["pactl", *args], capture_output=True, text=True, check=True, timeout=2
    )
    return result.stdout.strip()


class DeviceControls:
    def __init__(self, panel, row, kind, label):
        self.panel = panel
        self.kind = kind
        self.devices = {}
        self.selected = None
        self.updating = False
        title = Gtk.Label(label=label, xalign=0)
        panel.grid.attach(title, 0, row, 2, 1)

        self.choices = Gtk.ComboBoxText(hexpand=True)
        self.choices.connect("changed", self.select_device)
        panel.grid.attach(self.choices, 0, row + 1, 2, 1)

        self.level = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.level.set_hexpand(True)
        self.level.connect("format-value", lambda _, value: f"{value:.0f}%")
        self.level.connect("value-changed", self.set_volume)
        panel.grid.attach(self.level, 0, row + 2, 1, 1)

        self.mute = Gtk.CheckButton(label="Mute")
        self.mute.connect("toggled", self.set_mute)
        panel.grid.attach(self.mute, 1, row + 2, 1, 1)

    def refresh(self, default, devices):
        self.updating = True
        choices = {item["name"]: item["description"] for item in devices}
        if choices != self.devices:
            self.choices.remove_all()
            for name, description in choices.items():
                self.choices.append(name, description)
            self.devices = choices
        self.selected = next((item for item in devices if item["name"] == default), None)
        self.choices.set_active_id(default)
        self.choices.set_sensitive(bool(choices))
        self.level.set_sensitive(self.selected is not None)
        self.mute.set_sensitive(self.selected is not None)
        if self.selected:
            channels = self.selected["volume"].values()
            level = max((int(channel["value_percent"].rstrip("%")) for channel in channels), default=0)
            self.level.set_value(level)
            self.mute.set_active(self.selected["mute"])
        else:
            self.level.set_value(0)
            self.mute.set_active(False)
        self.updating = False

    def select_device(self, combo):
        name = combo.get_active_id()
        if not self.updating and name:
            self.panel.change(f"set-default-{self.kind}", name, refresh=True)

    def set_volume(self, scale):
        if not self.updating and self.selected:
            self.panel.change(
                f"set-{self.kind}-volume", self.selected["name"], f"{scale.get_value():.0f}%"
            )

    def set_mute(self, button):
        if not self.updating and self.selected:
            self.panel.change(
                f"set-{self.kind}-mute", self.selected["name"], str(int(button.get_active()))
            )


class Mixer(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Audio Controls", default_width=420)
        self.grid = Gtk.Grid(column_spacing=12, row_spacing=8, margin=16)
        self.add(self.grid)
        self.output = DeviceControls(self, 0, "sink", "Playback output")
        self.input = DeviceControls(self, 4, "source", "Microphone")
        self.status = Gtk.Label(xalign=0, wrap=True)
        self.grid.attach(self.status, 0, 7, 1, 1)
        refresh = Gtk.Button(label="Refresh devices")
        refresh.connect("clicked", lambda _: self.refresh())
        self.grid.attach(refresh, 1, 7, 1, 1)
        self.connect("focus-in-event", lambda *_: self.refresh())
        self.refresh()
        self.show_all()

    def refresh(self):
        try:
            info = json.loads(pulse("-f", "json", "info"))
            outputs = json.loads(pulse("-f", "json", "list", "sinks"))
            sources = json.loads(pulse("-f", "json", "list", "sources"))
            microphones = [item for item in sources if not item["name"].endswith(".monitor")]
            self.output.refresh(info["default_sink_name"], outputs)
            self.input.refresh(info["default_source_name"], microphones)
            self.status.set_text("" if microphones else "No microphone available")
        except (OSError, subprocess.SubprocessError, ValueError, KeyError):
            self.status.set_text("Could not read PulseAudio devices.")

    def change(self, *args, refresh=False):
        try:
            pulse(*args)
            if refresh:
                self.refresh()
        except (OSError, subprocess.SubprocessError):
            self.refresh()
            self.status.set_text("PulseAudio could not apply the change.")


def activate(app):
    window = app.get_active_window() or Mixer(app)
    window.refresh()
    window.present()


if __name__ == "__main__":
    app = Gtk.Application(
        application_id="local.waybar.AudioControls", flags=Gio.ApplicationFlags.FLAGS_NONE
    )
    app.connect("activate", activate)
    app.run()
