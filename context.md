```markdown
# Project Kickoff: Social Accountability App - Parallel Development Structure

## Project Overview
Build a social accountability app where friends can "poke" each other to stay on-task. A local AI agent assesses the recipient's current activity and delivers voice nudges when users drift off-task.

## Architecture Decision: Python-Centric System Integration
**All system introspection (activity detection, context enrichment) lives in the Python sidecar.** Electron is a thin UI client that handles rendering, Supabase sync, and audio playback only.

```
┌────────────────────────────────────────────┐
│  Electron App (UI Client)                  │
│                                            │
│  - Friend list + presence UI               │
│  - Poke button (send to Supabase)          │
│  - Supabase Realtime listener              │
│  - On poke received: POST /nudge           │
│  - Play audio response                     │
└────────────────┬───────────────────────────┘
                 │ HTTP (localhost:8765)
                 ▼
┌────────────────────────────────────────────┐
│  Python Sidecar (FastAPI)                  │
│                                            │
│  GET /activity-snapshot                    │ ← Coder 3
│   → Capture current window/app             │
│   → Enrich with behavioral context         │
│                                            │
│  POST /nudge { sender_name }               │
│   → Fetch own activity snapshot            │
│   → Mistral classification (Coder 1)       │ ← Coder 1
│   → ElevenLabs TTS generation              │
│   → Return audio + classification          │
│                                            │
│  POST /classify-local (optional)           │ ← Coder 3
│   → Ollama/local Mistral inference         │
└────────────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │   Supabase    │
         │ users/pokes/  │
         │ presence/     │
         │ feedback      │
         └───────────────┘
```

---

## Development Structure: 3 Parallel Workstreams

### **Coder 1: LLM Pipeline Engineer (Python)**
**Focus:** API orchestration, prompt engineering, model evaluation, voice generation

#### **Deliverables:**

**1. Task Classification Service**
- **Endpoint:** `POST /classify`
  ```json
  Input: {
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
  
  Output: {
    "status": "OFF_TASK",
    "confidence": 0.87,
    "reasoning": "Recreational video browsing during work hours with high context switching"
  }
  ```

- **Implementation:**
  - Design prompt templates with few-shot examples (10+ task/off-task scenarios)
  - Mistral API integration with retry logic + fallback models
  - Confidence thresholding: only trigger nudge if >0.75 confidence
  - Context-aware classification (work hours vs. evening, focus patterns)

**2. Voice Nudge Generation Pipeline**
- **Endpoint:** `POST /generate-nudge`
  ```json
  Input: {
    "sender_name": "Alice",
    "classification": "OFF_TASK",
    "activity_summary": "browsing YouTube"
  }
  
  Output: {
    "audio_base64": "//uQx...",
    "message_text": "Hey! Alice noticed you drifted—maybe save that video for later? 🎯",
    "duration_sec": 3.5
  }
  ```

- **Implementation:**
  - ElevenLabs API with voice ID selection (cheerful, professional, playful)
  - Generate personalized messages using sender name + activity context
  - Cache 15-20 common phrase variations (reduce API calls by 60%+)
  - Fallback: pre-recorded MP3s if API fails

**3. Observability & Fine-Tuning Loop**
- **Weave Integration:**
  - Trace every LLM call: log prompts, completions, latency, tokens used
  - Dashboard: classification distribution, confidence histogram, API error rates

- **Feedback Collection:**
  - Endpoint: `POST /feedback`
    ```json
    {
      "poke_id": "uuid",
      "user_feedback": "CORRECT" | "WRONG_OFF_TASK" | "WRONG_ON_TASK",
      "actual_activity": "researching competitors" // optional user comment
    }
    ```
  - Export to JSONL for fine-tuning dataset (target: 500+ labeled examples)

- **Metrics to track:**
  - Classification accuracy (validated against feedback)
  - TTS generation latency (p50, p95, p99)
  - API cost per poke (Mistral + ElevenLabs tokens)

#### **Mock Data Provided:**
- 100 sample activity snapshots with ground truth labels (CSV)
- 50 example poke scenarios (on-task: coding, reading docs; off-task: social media, shopping)
- Supabase read access to `feedback` table

#### **Dependencies:**
- **From Coder 3:** Activity snapshot schema with enriched context
- **From Coder 2:** Feedback data flowing from UI

#### **Tech Stack:**
Python 3.11+, FastAPI, Mistral API SDK, ElevenLabs API, Weave (W&B), pytest, pydantic

---

### **Coder 2: Electron UI/UX Developer**
**Focus:** Desktop app interface, real-time sync, user experience, audio playback

#### **Deliverables:**

**1. Electron Main Process**
- **Sidecar Lifecycle Management:**
  ```javascript
  // On app startup:
  1. Spawn Python sidecar: `python sidecar/main.py`
  2. Poll GET /health every 500ms (timeout: 30s)
  3. If health check fails: show error UI + retry button
  4. On app quit: gracefully terminate sidecar
  ```

- **Poke Flow Orchestration:**
  ```javascript
  // When poke received from Supabase:
  1. POST http://localhost:8765/nudge { sender_name: "Alice" }
  2. Receive { audio_base64, message_text, status }
  3. If audio_base64 exists: decode + play via Audio() API
  4. If audio fails: show visual toast with message_text
  5. Show feedback UI: "Was this accurate?" (thumbs up/down)
  ```

- **Audio Playback:**
  - Decode base64 → Blob → play via Web Audio API
  - Volume control (user preference: 0-100%)
  - Mute hours check (e.g., no audio 10pm-8am)
  - Fallback: if playback errors, show notification banner

**2. Renderer Process (React + Tailwind)**
- **Friend List View:**
  ```
  ┌─────────────────────────────┐
  │  Friends Online (3)         │
  ├─────────────────────────────┤
  │  ● Alice        [Poke] 👋   │  ← green dot = online
  │  ● Bob          [Poke] 👋   │
  │  ○ Charlie                  │  ← gray dot = offline
  └─────────────────────────────┘
  ```
  - Real-time presence dots (Supabase Realtime)
  - Individual poke buttons (disabled for offline users)
  - "Poke All Online" bulk action button

- **Incoming Poke Experience:**
  ```
  ┌─────────────────────────────────────┐
  │  🔔 Alice sent you a poke!          │
  │                                     │
  │  [Audio plays automatically]        │
  │  "Hey! Alice is checking in—maybe   │
  │   save that video for later? 🎯"    │
  │                                     │
  │  Was this accurate?                 │
  │  [👍 Yes]  [👎 No, I was on task]   │
  └─────────────────────────────────────┘
  ```
  - Toast notification with auto-dismiss (15s)
  - Feedback buttons → POST to Coder 1's `/feedback` endpoint
  - Show classification reasoning on hover (for debugging)

- **Settings Panel:**
  - Toggle: "Enable voice nudges" (fallback to visual only)
  - Slider: Audio volume (0-100%)
  - Time picker: Mute hours (e.g., 10pm-8am)
  - Toggle: "Privacy mode" (use local model, disable cloud API)

**3. Supabase Integration**
- **Authentication:**
  - Email/password login (Supabase Auth)
  - Persist session in Electron store

- **Tables:**
  ```sql
  users (id, email, display_name, avatar_url, created_at)
  
  pokes (
    id, 
    sender_id → users.id, 
    receiver_id → users.id, 
    timestamp, 
    classification, -- OFF_TASK | ON_TASK
    confidence
  )
  
  feedback (
    id,
    poke_id → pokes.id,
    user_feedback, -- CORRECT | WRONG_OFF_TASK | WRONG_ON_TASK
    comment,
    created_at
  )
  ```

- **Real-time Listeners:**
  - Subscribe to `pokes` where `receiver_id = current_user`
  - Subscribe to `users:presence` for friend online/offline updates

**4. Error Handling UI**
- Sidecar down: "AI service unavailable—retrying..." banner
- Audio playback fail: Show message text in toast
- Network error: "Couldn't send poke—check connection"

#### **Mock Data Provided:**
- Figma mockups for all screens
- 5 test Supabase accounts with seeded friend relationships
- Sample poke payloads for testing

#### **Dependencies:**
- **From Coder 3:** None directly (Python sidecar is a black box)
- **From Coder 1:** `/nudge` and `/feedback` endpoint contracts

#### **Tech Stack:**
Electron 28+, React 18, Tailwind CSS, Supabase JS SDK, Zustand (state), Electron Store (settings)

---

### **Coder 3: System Integration & Local ML Engineer**
**Focus:** Activity detection, context enrichment, local model optimization, privacy

#### **Deliverables:**

**1. Activity Snapshot Service**
- **Endpoint:** `GET /activity-snapshot`
  ```json
  Output: {
    "app_name": "Chrome",
    "window_title": "Machine Learning Papers - arXiv",
    "timestamp": "2025-03-01T14:32:00Z",
    "context": {
      "focus_duration_sec": 1200,      // 20min on current window
      "app_switches_last_5min": 2,
      "app_switches_last_30min": 8,
      "time_of_day": "14:32",
      "is_work_hours": true,            // heuristic: 9am-6pm weekdays
      "recent_apps": ["Chrome", "VSCode", "Slack"]
    },
    "privacy_mode": false
  }
  ```

- **Implementation:**
  - Use `pywinctl` library (cross-platform window detection)
  - **macOS:** Request Accessibility permissions on first run
  - **Windows:** Use Win32 API via `pywin32`
  - **Linux:** Support both X11 and Wayland (with graceful degradation)
  
- **Context Enrichment:**
  - Track focus duration: how long user has been on current window
  - Count app switches using rolling window (5min, 30min buckets)
  - Time-based heuristics: classify work hours vs. personal time
  - Recent apps list: last 5 apps switched to (for pattern detection)

- **Privacy Anonymization (optional mode):**
  ```python
  # If privacy_mode=True:
  - Hash window titles: "Machine Learning Papers" → "Doc-a3f8b2"
  - Redact sensitive keywords: bank names, medical terms, dating apps
  - User can whitelist apps to never report (e.g., "Messages", "WhatsApp")
  ```

**2. Local NVIDIA Model Integration**
- **Endpoint:** `POST /classify-local` (same I/O as `/classify`)
  ```json
  Input: { activity snapshot + sender_name }
  Output: { status, confidence, reasoning }
  ```

- **Setup:**
  - Install Ollama + pull `mistral:7b-instruct`
  - Benchmark vs. cloud API:
    - Latency: local (300-500ms) vs. cloud (800-1200ms)
    - Accuracy: validate on 100 held-out examples
    - VRAM usage: monitor with `nvidia-smi`

- **Optimization:**
  - Use 4-bit quantization (GGUF format) for inference
  - Tune context window: 2048 tokens sufficient for classification
  - Implement prompt caching for repeated activity patterns

- **Configuration:**
  - User toggle in Electron settings: "Use local AI (privacy mode)"
  - Fallback: if local model fails, route to cloud API
  - Document GPU requirements: RTX 3060+ (8GB VRAM minimum)

**3. Browser Context Extension (Stretch Goal)**
- **Problem:** `pywinctl` only sees "Chrome", not tab titles
- **Solution:** Optional browser extension
  - Chrome/Firefox extension that reports current tab via localhost WebSocket
  - Privacy-first: user must explicitly enable + grant permissions
  - Send active tab title to sidecar every 2 seconds when extension is active

**4. Fine-Tuning Dataset Pipeline**
- **Script:** `export_training_data.py`
  ```python
  # Fetch from Supabase:
  1. All pokes with feedback (feedback.user_feedback != NULL)
  2. Join with activity snapshots
  3. Export to JSONL:
     {
       "prompt": "Classify: {activity snapshot}",
       "completion": "OFF_TASK", 
       "reasoning": "YouTube during work hours"
     }
  ```
- Deliver to Coder 1 weekly (target: 100+ new labeled examples per week)
- Include edge cases: ambiguous activities, false positives, context-dependent tasks

#### **Mock Data Provided:**
- 200 sample `pywinctl` outputs across macOS/Windows/Linux
- NVIDIA RTX 3080 access (12GB VRAM)
- Sample browser extension scaffold (React + Chrome Manifest v3)

#### **Dependencies:**
- **From Coder 1:** Classification prompt templates (to align local model)
- **From Coder 2:** Privacy mode toggle state (via `/config` endpoint)

#### **Tech Stack:**
Python 3.11+, pywinctl, psutil, Ollama, CUDA Toolkit 12.x, FastAPI, SQLite (local cache)

---

## Shared Interfaces (Contract-First Development)

### **1. Activity Snapshot Schema**
**Owner:** Coder 3  
**Consumers:** Coder 1 (for classification)

```typescript
interface ActivitySnapshot {
  app_name: string;              // e.g., "Chrome", "VSCode"
  window_title: string;          // e.g., "YouTube - Trending"
  timestamp: string;             // ISO 8601
  context: {
    focus_duration_sec: number;  // time on current window
    app_switches_last_5min: number;
    app_switches_last_30min: number;
    time_of_day: string;         // "HH:MM"
    is_work_hours: boolean;
    recent_apps: string[];       // last 5 apps
  };
  privacy_mode: boolean;         // anonymization enabled?
}
```

### **2. Nudge Endpoint** (Electron → Python)
**Owner:** Coder 1  
**Consumer:** Coder 2

```bash
POST http://localhost:8765/nudge
Content-Type: application/json

{
  "sender_name": "Alice"
}

Response 200:
{
  "status": "OFF_TASK" | "ON_TASK",
  "confidence": 0.87,
  "message_text": "Hey! Alice is checking in—maybe save that video for later? 🎯",
  "audio_base64": "//uQx...",  // optional: null if TTS fails
  "duration_sec": 3.5,
  "classification_reasoning": "Recreational browsing during work hours"
}

Response 503 (Sidecar Error):
{
  "error": "Classification service unavailable",
  "fallback_message": "Alice sent you a poke!"
}
```

### **3. Feedback Endpoint** (Electron → Python)
**Owner:** Coder 1  
**Consumer:** Coder 2

```bash
POST http://localhost:8765/feedback
Content-Type: application/json

{
  "poke_id": "uuid-from-supabase",
  "user_feedback": "CORRECT" | "WRONG_OFF_TASK" | "WRONG_ON_TASK",
  "comment": "I was researching competitors, not slacking"  // optional
}

Response 200:
{
  "success": true,
  "message": "Thanks for the feedback!"
}
```

### **4. Health Check** (Electron → Python)
**Owner:** Coder 3  
**Consumer:** Coder 2

```bash
GET http://localhost:8765/health

Response 200:
{
  "status": "healthy",
  "activity_service": "ready",
  "llm_service": "ready",
  "local_model": "available" | "unavailable"
}
```

---

## Development Timeline

### **Week 1: Foundation & Contracts**
- **All:** Agree on API contracts (review this doc, lock in schemas)
- **Coder 1:** FastAPI skeleton + mock `/nudge` endpoint (returns dummy audio)
- **Coder 2:** Electron shell + Supabase auth + friend list UI (with mock data)
- **Coder 3:** `/activity-snapshot` working on macOS (permission flow complete)

**Milestone:** Electron can send poke → Python returns mock nudge → audio plays

### **Week 2: Core Features**
- **Coder 1:** Live Mistral classification + ElevenLabs TTS integration
- **Coder 2:** Real-time poke flow (Supabase → sidecar → audio playback)
- **Coder 3:** Cross-platform activity detection (Windows + Linux support)

**Milestone:** End-to-end poke works with real classification

### **Week 3: Intelligence & Polish**
- **Coder 1:** Context-aware prompts + confidence thresholding + Weave tracing
- **Coder 2:** Feedback UI + settings panel (mute hours, volume, privacy toggle)
- **Coder 3:** Context enrichment (focus duration, app switching metrics)

**Milestone:** Classification improves with context, user can tune preferences

### **Week 4: Local Models & Optimization**
- **Coder 1:** Phrase caching (reduce TTS API calls 60%) + feedback export pipeline
- **Coder 2:** Error handling UI (sidecar down, network failures)
- **Coder 3:** Ollama local model integration + privacy mode anonymization

**Milestone:** Privacy mode works, local inference functional

### **Week 5: Dogfooding & Iteration**
- **All:** Internal testing with team as users (target: 500+ pokes)
- **Coder 1:** Analyze classification accuracy from feedback data
- **Coder 2:** UI refinements based on team feedback
- **Coder 3:** Performance tuning (reduce activity snapshot latency)

**Milestone:** Ready for limited beta (10-20 external users)

---

## Success Metrics

### **Coder 1 (LLM Pipeline):**
- ✅ 80%+ classification accuracy (validated on held-out set with feedback)
- ✅ <1.5s TTS generation latency (p95)
- ✅ 100% of LLM calls traced in Weave dashboard
- ✅ 500+ labeled examples exported for fine-tuning

### **Coder 2 (Electron UX):**
- ✅ <3s end-to-end poke-to-nudge latency (p95)
- ✅ 0 crashes in 1000 poke cycles (sidecar spawn/health check resilient)
- ✅ Audio playback success rate >95% (fallback to visual toast works)
- ✅ Settings persist across app restarts

### **Coder 3 (System Integration):**
- ✅ Activity detection works on macOS/Windows/Linux (manual QA: 20 apps each)
- ✅ Local model inference <500ms (RTX 3080, 4-bit quantized)
- ✅ Privacy mode: 0 sensitive keywords leak to logs/API
- ✅ Context enrichment adds <50ms overhead to snapshot generation

---

## Communication Protocols

### **Daily Standups (15 min, async-friendly):**
- **Format:** Slack thread with 3 questions:
  1. What I shipped yesterday
  2. What I'm shipping today
  3. Blockers (tag relevant coder if dependency blocked)

### **API Contract Changes:**
- **Rule:** Any change to shared schemas should be coordinated with the team.
- **Process:** Post proposed change in `#contracts` channel → wait for 👍 from others → merge

### **Shared Repository Structure:**
```
/
├── electron/          # Coder 2
│   ├── main/          # Main process
│   ├── renderer/      # React UI
│   └── preload/       # IPC bridge
├── sidecar/           # Coders 1 + 3
│   ├── main.py        # FastAPI app
│   ├── classification/  # Coder 1: LLM logic
│   ├── activity/      # Coder 3: system introspection
│   └── tests/
└── docs/
    └── API.md         # Source of truth for contracts
```

### **Mock/Stub Mode:**
- **Coder 1:** Provides `MOCK_MODE=true` env var → returns dummy classifications
- **Coder 2:** Can test UI with mock sidecar responses (bypass network calls)
- **Coder 3:** Provides sample activity snapshots as JSON fixtures

---

## Open Questions for Team

1. **Privacy Default:**
   - Ship with cloud LLM (faster) or local model (private)?
   - Recommendation: Cloud by default, prominent "Enable Privacy Mode" in settings

2. **Voice Personality:**
   - Single voice (consistency) or user-selectable (personalization)?
   - Options: Cheerful, Professional, Playful, Sarcastic

3. **Poke Limits:**
   - Should we rate-limit pokes? (e.g., max 10 per hour to prevent spam)
   - Or trust social dynamics to self-regulate?

4. **Browser Extension:**
   - Must-have for MVP or post-launch feature?
   - Trade-off: Better accuracy vs. extra installation friction

5. **Fine-Tuning Strategy:**
   - Auto-retrain model weekly with new feedback data?
   - Or manual curation to avoid poisoning dataset?## Getting Started

```