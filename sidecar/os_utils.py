import subprocess
import json
import shutil

def get_active_window_hyprland():
    """Returns a dictionary with active window information for Hyprland."""
    try:
        result = subprocess.run(['hyprctl', 'activewindow', '-j'], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return None

def get_active_window_info():
    """Generic wrapper to get active window info, currently supports Hyprland."""
    # Add more OS/DE detection logic here if needed
    if shutil.which('hyprctl'):
        win = get_active_window_hyprland()
        if win:
            return {
                "app": win.get("class", "unknown"),
                "title": win.get("title", "unknown")
            }
    return {"app": "unknown", "title": "unknown"}
