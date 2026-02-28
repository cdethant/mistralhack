"""
Context enrichment: tracks focus duration, app switches, and recent app history.
Runs a background thread that polls the active window every second.
"""
import threading
import time
from collections import deque
from datetime import datetime

# get_active_window is thread-safe and timeout-protected (no module-level X11 init)
from activity.snapshot import get_active_window


class ActivityContextTracker:
    """
    Singleton-style tracker that runs in a background thread.
    Stores a rolling history of (timestamp, app_name) tuples.
    """

    POLL_INTERVAL = 1.0  # seconds

    def __init__(self):
        # Each entry: (epoch_float, app_name, window_title)
        self._history: deque[tuple[float, str, str]] = deque(maxlen=1800)  # 30 min @ 1s
        self._lock = threading.Lock()
        self._running = False
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        self._running = True

    def _poll_loop(self):
        while True:
            now = time.time()
            app, title = get_active_window()
            with self._lock:
                self._history.append((now, app, title))
            time.sleep(self.POLL_INTERVAL)

    def stop(self):
        self._running = False

    # ── Public helpers ──────────────────────────────────────────────────────

    def current_focus_duration(self, app_name: str, window_title: str) -> int:
        """How long (seconds) the user has been on the current window."""
        now = time.time()
        duration = 0
        with self._lock:
            for ts, a, t in reversed(self._history):
                if a == app_name and t == window_title:
                    duration = int(now - ts)
                else:
                    break
        return duration

    def app_switches(self, window_seconds: int) -> int:
        """Number of app switches in the last `window_seconds` seconds."""
        cutoff = time.time() - window_seconds
        with self._lock:
            recent = [(ts, a) for ts, a, _ in self._history if ts >= cutoff]

        if len(recent) < 2:
            return 0
        switches = sum(
            1 for i in range(1, len(recent)) if recent[i][1] != recent[i - 1][1]
        )
        return switches

    def recent_apps(self, n: int = 5) -> list[str]:
        """Last `n` distinct apps (most recent first, no duplicates)."""
        seen: list[str] = []
        with self._lock:
            for _, app, _ in reversed(self._history):
                if app not in seen:
                    seen.append(app)
                if len(seen) >= n:
                    break
        return seen

    def is_work_hours(self) -> bool:
        """Heuristic: 9am–6pm on weekdays."""
        now = datetime.now()
        return now.weekday() < 5 and 9 <= now.hour < 18
