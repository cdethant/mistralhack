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


# App-specific AppleScript that returns the active tab / document title.
# Key = localised app name as reported by System Events.
_APP_TITLE_SCRIPTS = {
    "Google Chrome":        'tell application "Google Chrome" to get title of active tab of front window',
    "Google Chrome Beta":   'tell application "Google Chrome Beta" to get title of active tab of front window',
    "Google Chrome Canary": 'tell application "Google Chrome Canary" to get title of active tab of front window',
    "Chromium":             'tell application "Chromium" to get title of active tab of front window',
    "Microsoft Edge":       'tell application "Microsoft Edge" to get title of active tab of front window',
    "Brave Browser":        'tell application "Brave Browser" to get title of active tab of front window',
    "Arc":                  'tell application "Arc" to get title of active tab of front window',
    "Safari":               'tell application "Safari" to get name of current tab of front window',
    "Firefox":              'tell application "Firefox" to get title of front window',
    "Code":                 'tell application "Code" to get name of front document',
    "Xcode":                'tell application "Xcode" to get name of front document',
}


def _osascript(script: str, timeout: int = 3) -> str | None:
    """Run an AppleScript one-liner; return stripped stdout or None on any error."""
    try:
        r = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=timeout,
        )
        if r.returncode == 0:
            out = r.stdout.strip()
            return out if out else None
    except Exception:
        pass
    return None


def get_active_window_macos():
    """
    Returns {'app': str, 'title': str} for the frontmost macOS window.

    Uses osascript (out-of-process) for the app name so it is always accurate
    even when called from a background thread (NSWorkspace is unreliable there).

    Title resolution order:
      1. App-specific AppleScript (browsers, VS Code/Xcode) – no special perms.
      2. CGWindowListCopyWindowInfo kCGWindowName – works for native apps when
         Screen Recording is granted.
      3. Falls back to the app name.
    """
    # --- Step 1: get frontmost app name via osascript (always accurate) ---
    app_name = _osascript(
        'tell application "System Events" to get name of first process whose frontmost is true'
    )
    if not app_name:
        return None

    # --- Step 2: browser / editor tab title ---
    script = _APP_TITLE_SCRIPTS.get(app_name)
    if script:
        title = _osascript(script)
        if title:
            return {"app": app_name, "title": title}

    # --- Step 3: CGWindowListCopyWindowInfo (requires Screen Recording perm) ---
    try:
        import Quartz
        import AppKit

        # Resolve PID for the named process so we can match windows.
        ws = AppKit.NSWorkspace.sharedWorkspace()
        pid = None
        for proc in ws.runningApplications():
            if proc.localizedName() == app_name:
                pid = proc.processIdentifier()
                break

        if pid is not None:
            win_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly
                | Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID,
            )
            for w in (win_list or []):
                if w.get("kCGWindowOwnerPID") == pid and w.get("kCGWindowLayer", 99) == 0:
                    t = w.get("kCGWindowName", "")
                    if t:
                        return {"app": app_name, "title": t}
    except Exception:
        pass

    # --- Step 4: fall back to app name as title ---
    return {"app": app_name, "title": app_name}


def get_active_window_info():
    """Generic wrapper to get active window info; supports Hyprland and macOS."""
    os_name = platform.system()

    if os_name == "Darwin":
        win = get_active_window_macos()
        if win:
            return win
    elif os_name == "Linux" and shutil.which("hyprctl"):
        win = get_active_window_hyprland()
        if win:
            return {
                "app": win.get("class", "unknown"),
                "title": win.get("title", "unknown"),
            }

    return {"app": "unknown", "title": "unknown"}
