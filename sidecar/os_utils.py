import subprocess
import json
import shutil

import platform

def get_active_window_hyprland():
    """Returns a dictionary with active window information for Hyprland."""
    try:
        result = subprocess.run(['hyprctl', 'activewindow', '-j'], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return None

def get_active_window_macos():
    """Returns active window info for macOS using AppleScript."""
    script = 'tell application "System Events" to get {name, title} of first window of 0th item of (processes whose frontmost is true)'
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, check=True)
        parts = result.stdout.strip().split(', ', 1)
        if len(parts) == 2:
            return {"app": parts[0], "title": parts[1]}
        return {"app": parts[0], "title": "unknown"}
    except Exception:
        try:
            script_app = 'tell application "System Events" to get name of first item of (processes whose frontmost is true)'
            result = subprocess.run(['osascript', '-e', script_app], capture_output=True, text=True, check=True)
            return {"app": result.stdout.strip(), "title": "unknown"}
        except Exception:
            return None

def get_active_window_info():
    """Generic wrapper to get active window info, supports Hyprland and macOS."""
    os_name = platform.system()
    
    if os_name == "Darwin":
        win = get_active_window_macos()
        if win:
            return win
    elif os_name == "Linux" and shutil.which('hyprctl'):
        win = get_active_window_hyprland()
        if win:
            return {
                "app": win.get("class", "unknown"),
                "title": win.get("title", "unknown")
            }
            
    return {"app": "unknown", "title": "unknown"}
