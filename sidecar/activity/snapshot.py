"""
Activity Snapshot – reads the currently active window and returns
a structured ActivitySnapshot. Uses pywinctl for cross-platform support.

On Linux without a DISPLAY (headless/CI), pywinctl can block indefinitely.
All calls are wrapped in a daemon thread with a 2-second timeout so the
sidecar always responds promptly.
"""
import os
import platform
import threading
from datetime import datetime, timezone

from pydantic import BaseModel

_WINDOW_TIMEOUT = 2.0  # seconds


class ActivityContext(BaseModel):
    focus_duration_sec: int = 0
    app_switches_last_5min: int = 0
    app_switches_last_30min: int = 0
    time_of_day: str = ""
    is_work_hours: bool = False
    recent_apps: list[str] = []


class ActivitySnapshot(BaseModel):
    app_name: str
    window_title: str
    timestamp: str
    context: ActivityContext
    privacy_mode: bool = False


def get_active_window() -> tuple[str, str]:
    """
    Return (app_name, window_title) for the currently focused window.
    Returns ("Unknown", "Unknown") if DISPLAY is unavailable or on timeout.
    """
    result = [("Unknown", "Unknown")]

    def _fetch():
        try:
            system = platform.system()
            import pywinctl as pwc
            win = pwc.getActiveWindow()
            if win is None:
                return
            title = win.title or "Unknown"
            if system == "Linux":
                app = _get_app_name_linux(win)
            elif system == "Darwin":
                app = _get_app_name_macos(win)
            elif system == "Windows":
                app = _get_app_name_windows(win)
            else:
                app = (title.split(" – ")[0] if " – " in title else title.split(" - ")[0])
            result[0] = (app, title)
        except Exception:
            pass  # Leave default ("Unknown", "Unknown")

    t = threading.Thread(target=_fetch, daemon=True)
    t.start()
    t.join(timeout=_WINDOW_TIMEOUT)
    return result[0]


def _get_app_name_linux(win) -> str:
    """Extract app name on Linux via xprop heuristic."""
    try:
        import subprocess
        handle = getattr(win, "_hWnd", None)
        if handle is None:
            fn = getattr(win, "getHandle", None)
            if fn:
                handle = fn()
        if handle:
            out = subprocess.run(
                ["xprop", "-id", str(handle), "WM_CLASS"],
                capture_output=True, text=True, timeout=1,
            )
            if out.returncode == 0 and "=" in out.stdout:
                parts = out.stdout.split("=")[1].strip().strip('"').split('", "')
                if len(parts) >= 2:
                    return parts[1].strip('"')
    except Exception:
        pass
    title = win.title or "Unknown"
    return title.split(" - ")[-1].strip() if " - " in title else title.split()[0]


def _get_app_name_macos(win) -> str:
    try:
        app = getattr(win, "_app", None)
        if app:
            return str(app)
    except Exception:
        pass
    title = win.title or "Unknown"
    return title.split(" – ")[0].strip()


def _get_app_name_windows(win) -> str:
    try:
        import psutil
        proc = psutil.Process(win.getHandle())
        return proc.name().replace(".exe", "").capitalize()
    except Exception:
        pass
    title = win.title or "Unknown"
    return title.split(" - ")[-1].strip()
