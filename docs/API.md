# mistralhack API Contract

> **Source of truth** for all sidecar endpoints.  
> Any change should be coordinated with the team before merging.

Base URL: `http://localhost:8765`

---

## GET /health

Check sidecar readiness.

**Response 200:**
```json
{
  "status": "healthy",
  "activity_service": "ready",
  "llm_service": "ready",
  "local_model": "available"
}
```

---

## GET /activity-snapshot

Returns the current user's active window and enriched behavioral context.

**Response 200:**
```json
{
  "app_name": "Chrome",
  "window_title": "YouTube - Trending",
  "timestamp": "2025-03-01T14:32:00Z",
  "context": {
    "focus_duration_sec": 45,
    "app_switches_last_5min": 7,
    "app_switches_last_30min": 15,
    "time_of_day": "14:32",
    "is_work_hours": true,
    "recent_apps": ["Chrome", "VSCode", "Slack", "Terminal", "Finder"]
  },
  "privacy_mode": false
}
```

---

## POST /nudge

Triggered by Electron when a poke is received. Fetches activity, runs classification, and generates a voice nudge.

**Request:**
```json
{ "sender_name": "Alice" }
```

**Response 200:**
```json
{
  "status": "OFF_TASK",
  "confidence": 0.87,
  "message_text": "Hey! Alice noticed you drifted—maybe save that video for later? 🎯",
  "audio_base64": "//uQx...",
  "duration_sec": 3.5,
  "classification_reasoning": "Recreational video browsing during work hours with high context switching"
}
```

**Response 200 (ON_TASK):**
```json
{
  "status": "ON_TASK",
  "confidence": 0.92,
  "message_text": "You're crushing it! Alice just checked in. 💪",
  "audio_base64": "//uQx...",
  "duration_sec": 2.8,
  "classification_reasoning": "Active coding session during work hours"
}
```

**Response 503 (sidecar error):**
```json
{
  "error": "Classification service unavailable",
  "fallback_message": "Alice sent you a poke!"
}
```

---

## POST /classify

Classify an activity snapshot. (Also called internally by `/nudge`.)

**Request:**
```json
{
  "app_name": "Chrome",
  "window_title": "YouTube - Trending",
  "context": {
    "focus_duration_sec": 45,
    "app_switches_last_5min": 7,
    "time_of_day": "14:30",
    "is_work_hours": true
  },
  "sender_name": "Alice"
}
```

**Response 200:**
```json
{
  "status": "OFF_TASK",
  "confidence": 0.87,
  "reasoning": "Recreational video browsing during work hours with high context switching"
}
```

---

## POST /classify-local

Same I/O as `/classify` but routes to local Ollama model. Returns `503` if Ollama is not running.

---

## POST /feedback

Submit user feedback on classification accuracy.

**Request:**
```json
{
  "poke_id": "uuid-from-supabase",
  "user_feedback": "CORRECT",
  "comment": "I was actually researching competitors"
}
```
`user_feedback` must be one of: `CORRECT`, `WRONG_OFF_TASK`, `WRONG_ON_TASK`

**Response 200:**
```json
{
  "success": true,
  "message": "Thanks for the feedback!"
}
```

---

## POST /config

Update sidecar runtime config (privacy mode, mute hours, preferred model).

**Request:**
```json
{
  "privacy_mode": false,
  "use_local_model": false,
  "mute_start": "22:00",
  "mute_end": "08:00"
}
```

**Response 200:**
```json
{ "success": true }
```
