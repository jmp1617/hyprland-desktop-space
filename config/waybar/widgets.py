import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from html import escape
from urllib.parse import urlencode


def weather_condition(code, is_day=True):
    if code == 0:
        return ("󰖙", "Clear") if is_day else ("󰖔", "Clear")
    if code in (1, 2):
        return ("󰖕" if is_day else "󰼱", "Partly cloudy")
    if code == 3:
        return "󰖐", "Overcast"
    if code in (45, 48):
        return "󰖑", "Fog"
    if code in (56, 57, 66, 67):
        return "󰙿", "Freezing rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "󰖘", "Snow"
    if code in (95, 96, 99):
        return "󰙾", "Thunderstorms"
    return "󰖗", "Rain"


def weather():
    try:
        location = json.loads(Path(__file__).with_name("weather-location.json").read_text())
        latitude = float(location["latitude"])
        longitude = float(location["longitude"])
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError("Coordinates out of range")
    except (OSError, ValueError, TypeError, KeyError):
        return {"text": "󰖐  —", "tooltip": "Set your location in the Waybar weather-location.json file"}

    query = urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,weather_code,is_day",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit",
        "timezone": "auto",
        "forecast_days": 3,
    })
    try:
        response = subprocess.check_output(
            ["curl", "--fail", "--silent", "--max-time", "8",
             f"https://api.open-meteo.com/v1/forecast?{query}"],
            timeout=9,
        )
        forecast = json.loads(response)
        current = forecast["current"]
        icon, condition = weather_condition(current["weather_code"], current["is_day"])
        temperature = round(current["temperature_2m"])
        lines = [escape(str(location.get("label", "Forecast"))), f"{condition} · {temperature}°F"]
        daily = forecast["daily"]
        for day, code, high, low in zip(
            daily["time"], daily["weather_code"],
            daily["temperature_2m_max"], daily["temperature_2m_min"],
        ):
            _, condition = weather_condition(code)
            weekday = date.fromisoformat(day).strftime("%a")
            lines.append(f"{weekday} · {condition} · {round(high)}° / {round(low)}°F")
        return {"text": f"{icon}  {temperature}°F", "tooltip": "\n".join(lines)}
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return {"text": "󰖐  —", "tooltip": "Forecast temporarily unavailable", "class": "unavailable"}


def notifications():
    try:
        paused = subprocess.check_output(
            ["dunstctl", "is-paused"], text=True, timeout=3
        ).strip()
    except (OSError, subprocess.SubprocessError):
        paused = ""
    if paused == "true":
        return {"text": "", "tooltip": "Do not disturb is on · Click to resume notifications", "class": "paused"}
    if paused == "false":
        return {"text": "", "tooltip": "Notifications are on · Click for do not disturb"}
    return {"text": "", "tooltip": "Dunst status unavailable", "class": "unavailable"}


def camera():
    try:
        objects = json.loads(subprocess.check_output(["pw-dump"], timeout=2, stderr=subprocess.DEVNULL))
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"text": ""}
    camera_nodes = set()
    active_sources = set()
    for item in objects:
        info = item.get("info", {})
        props = info.get("props", {})
        if props.get("media.class") == "Video/Source" and (
            props.get("device.api") in {"v4l2", "libcamera"}
            or props.get("media.role") == "Camera"
        ):
            camera_nodes.add(item["id"])
        if item["type"] == "PipeWire:Interface:Link" and info.get("state") == "active":
            active_sources.add(info.get("output-node-id"))
    if camera_nodes & active_sources:
        return {"text": "", "tooltip": "A PipeWire camera is in use"}
    return {"text": ""}


if __name__ == "__main__":
    widget = {"weather": weather, "notifications": notifications, "camera": camera}
    print(json.dumps(widget[sys.argv[1]]()))
