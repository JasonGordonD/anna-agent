# Anna-Agent System Summary

## 🎯 Core Purpose
A memory-evolving, psychologically layered AI voice agent designed for character-driven storytelling and NSFW scene authorship. Hosted via Render, served via ElevenLabs TTS, and backed by Supabase.

## 🧱 System Architecture Overview

### 🔧 main.py – Flask API App
- `/speak`: Accepts user input, builds TTS prompt using memory, calls ElevenLabs API, logs session to Supabase.
- `/snapshot`: Returns current memory variables (trust_level, anxiety_index, etc.).
- `/log_memory`: Accepts structured POST data to store memory state and summary in Supabase.
- `/live_kb`: Returns dynamic KB built from recent session history.
- 🔐 Uses real Supabase + ElevenLabs keys (as dummy/tested config).
- 💥 Fixed: Broken imports, f-strings, Markdown syntax, and /snapshot logic.
- ❌ Removed dependency on load_long_term_profile() (now superseded by live_brain.txt).

### 🧠 profile_builder.py – Long-Term Memory Composer
- Pulls all session logs from Supabase.
- Derives:
  - Narrative replay (Anna’s POV)
  - Behavior tags (e.g., “humiliation”, “longing”)
  - Trend shifts (trust/anxiety/edge)
  - Behavior modulation triggers
- Writes live_brain.txt (consumed via /live_kb)
- 🔁 Daily backup files: brain_YYYY-MM-DD.txt
- 💥 Replaced old static profile logic with full AI-enhanced tracking.

### 📄 memory_schema.json
- Stores and drives all dynamic memory keys:
  - trust_level, anxiety_index, edge_index, coke_status, session_count
- Easily expandable to add new metrics like mirror_bonding, degradation_trigger, etc.

### 📂 Supabase Backend
- ✅ Live table session_logs
- ✅ Public SELECT policy enabled
- ✅ Stores full emotional state + user input + AI summary for each session
- 🧠 Powers both real-time memory and behavioral trend analysis

### 🧩 Custom ElevenLabs Tools
- fetch_memory → Calls /snapshot at session start
- store_memory → Calls /log_memory at session end
- Optional: fetch_kb_anna → Reads from /live_kb to inject long-term personality

All tools use proper JSON schemas and dynamic variables tied to LLM prompt context.

### 🔍 Observability Tools
- emotion_grapher.py (optional): Charts trends over time (not yet deployed)
- Supabase logs live memory over time (structured and queryable)
- KB output (live_brain.txt) can be inspected manually or in ElevenLabs debugging

## 🧠 Behavior + Personality Layer
- Anna’s voice adapts based on memory state:
  - Trust ↑ → Intimate, possessive language
  - Anxiety ↑ → Softer, safer tone
  - Edge ↑ → Direct, degraded, NSFW escalation
- Dark Psychology tactics woven into both prompt logic and behavior tags.
- Narrative POV lets Anna “remember” and narrate past interactions via KB.
