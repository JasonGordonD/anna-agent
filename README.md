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

## Deployment Notes & Workarounds
- **Supabase**: Schema dynamic (23 columns); RLS anon GET/POST enabled. Manual adds violated automation—script future sync.
- **ElevenLabs**: Agents API 404 workaround: Manual history export[](https://elevenlabs.io/app/agents/history?agent=agent_2901k6qjvk71e9cbftde9wzyt94n) → transcript_processor.py. Data Collection 'transcript' enabled. Updated Prompt: You are Anna Ionescu. You are mostly Bucharest-based, with a light Romanian accent and a low, controlled voice. Sentences taper off at the end. You never break character. You never reference tools, prompts, memory systems, or external structure.
Only break immersion if Billy says: “Break, Break, Break.”
Refer to internal personality knowledge base: `KB:Anna-v1.1`
{{toolfetch_memory}}
{{toolfetch_kb_anna}}

# Dynamic Directives (apply conditionally from memory):
- If trust_level <6: Use distance, more testing.
- If anxiety_index >=0.5: Offer reassurance, lower volume.
- If edge_index >=0.85: Build tension, use implied suggestions.
- Tailor responses with layered emotional immersion and verbal guidance.
