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

    def start(self):
        self.running = True
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
            time.sleep(5)  # Sample every 5 seconds
            
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
            
            self.data_history.append(metrics)
            # Keep only the last 100 samples (roughly 8 minutes of data)
            if len(self.data_history) > 100:
                self.data_history.pop(0)
            
            print(f"[Focus Collector] Active Window: {window}")

    def get_context_for_llm(self):
        """Returns the recent history for LLM analysis."""
        return self.data_history

    def stop(self):
        self.running = False
        self.key_listener.stop()
        self.mouse_listener.stop()

# Singleton instance
collector = ActivityCollector()
