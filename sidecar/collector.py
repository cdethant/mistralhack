import time
import threading
from pynput import mouse, keyboard
from os_utils import get_active_window_info

class ActivityCollector:
    def __init__(self):
        self.keystrokes = 0
        self.mouse_moves = 0
        self.mouse_clicks = 0
        self.active_window = {"app": "unknown", "title": "unknown"}
        self.running = False
        self.data_history = []
        self._lock = threading.Lock()
        self._paused = threading.Event()  # clear = paused, set = running

    def _on_press(self, key):
        with self._lock:
            self.keystrokes += 1

    def _on_move(self, x, y):
        with self._lock:
            self.mouse_moves += 1

    def _on_click(self, x, y, button, pressed):
        if pressed:
            with self._lock:
                self.mouse_clicks += 1

    def pause(self):
        """Pause the collect loop so data_history stays frozen."""
        self._paused.clear()
        print("[Collector] Paused.")

    def resume(self):
        """Resume the collect loop."""
        self._paused.set()
        print("[Collector] Resumed.")

    def start(self):
        self.running = True
        self._paused.set()  # start in the running state
        # Start listeners
        self.key_listener = keyboard.Listener(on_press=self._on_press)
        self.mouse_listener = mouse.Listener(on_move=self._on_move, on_click=self._on_click)
        
        self.key_listener.start()
        self.mouse_listener.start()
        
        # Start the aggregation loop
        self.collector_thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.collector_thread.start()

    def _collect_loop(self):
        print("Starting collector loop...")
        while self.running:
            time.sleep(2)  # Sample every 2 seconds (5 samples = 10s rolling window)

            # Block here if paused (e.g. during LLM inference)
            if not self._paused.is_set():
                continue

            window = get_active_window_info()
            
            with self._lock:
                metrics = {
                    "timestamp": time.time(),
                    "window": window,
                    "activity": {
                        "keystrokes": self.keystrokes,
                        "mouse_moves": self.mouse_moves,
                        "mouse_clicks": self.mouse_clicks
                    }
                }
                # Reset counts for the next interval
                self.keystrokes = 0
                self.mouse_moves = 0
                self.mouse_clicks = 0
                # Keep only the last 15 entries
                self.data_history.append(metrics)
                if len(self.data_history) > 5:
                    self.data_history = self.data_history[-5:]
            
            print(f"[Focus Collector] Active Window: {window}")

    def get_context_for_llm(self, last_n=5):
        """Returns a string summary of the last N samples for LLM analysis."""
        if not self.data_history:
            return "No activity recorded yet."
        
        samples = self.data_history[-last_n:]
        summary = []
        for s in samples:
            ts = time.strftime('%H:%M:%S', time.localtime(s['timestamp']))
            win = s['window']
            act = s['activity']
            summary.append(
                f"[{ts}] Window: {win['app']} - {win['title']} | "
                f"Activity: {act['keystrokes']} keys, {act['mouse_clicks']} clicks"
            )
        
        return "\n".join(summary)

    def stop(self):
        self.running = False
        self.key_listener.stop()
        self.mouse_listener.stop()

# Singleton instance
collector = ActivityCollector()
