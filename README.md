# Anna Agent System Summary

## 🎯 Core Purpose
A memory-evolving, psychologically layered AI voice agent for character-driven storytelling and NSFW scene authorship. Hosted on Render/Vercel, powered by ElevenLabs TTS, backed by Supabase for dynamic memory persistence.

## 🏠 Hosts
- **Render**: https://anna-agent.onrender.com (dyno-based; UptimeRobot for wake/alerts).
- **Vercel Mirror**: https://anna-agent-gamma.vercel.app (serverless; auto-deploys from GitHub, no sleep).

## 🔧 Endpoints (Flask API)
- **GET /**: Status ("Anna agent is running.").
- **GET /live_kb**: Dynamic KB string (trust/anxiety trends, behavior modulation, narrative replay from live_brain.txt).
- **GET /snapshot**: Current memory blob (JSON: trust_level, anxiety_index, edge_index, etc.).
- **POST /speak**: TTS audio (WAV binary; payload: `{"text": "...", "voice_id": "zHX13TdWb6f856P3Hqta"}`).
- **POST /log_memory**: Supabase insert (201; payload: `{"memory_blob": "{...}", "session_duration_secs": 45, "trust_level": 4.5, ...}`).

## 🧱 System Architecture
### main.py – Flask Core
- Auto-KB generation on startup (import-time `generate()` for Flask 3.x compatibility).
- Integrates prompt_builder.py for conditional directives.
- Fixed: Imports, f-strings, route duplicates, /snapshot blob logic.
- Removed: Legacy `load_long_term_profile()` (superseded by live_brain.txt).

### profile_builder.py – Memory Composer
- Pulls all Supabase logs (17+ rows as of Oct 6, 2025).
- Derives: Narrative replay (Anna POV), behavior tags (e.g., "humiliation", "longing"), trend shifts (↑ edge, ↓ trust), modulation triggers.
- Outputs: live_brain.txt (daily backups: brain_YYYY-MM-DD.txt).
- Enhanced: Null-safe numerics, dynamic schema iteration.

### prompt_builder.py – Personality Layer
- Builds immersive prompts from memory + rules.json (JSON array: `[{"condition": "trust < 3.0", "directive": "..."}]`.
- Injects directives post-base (e.g., empathy for low trust, de-escalate for high anxiety).
- Chains with intro logic (trust/anxiety/edge/coke thresholds).

### transcript_processor.py – Input Handler
- Processes convo transcripts (manual UI mock for ElevenLabs 404; auto once flag enabled).
- Coerces lists to str, maps duration_secs/blob for Supabase POST.

### emotion_grapher.py – Visualization
- Generates PDF trends (trust line, anxiety heatmap, edge/coke bars/streaks).
- Run: `python emotion_grapher.py` → emotion_graph.pdf.

### 📄 memory_schema.json
- Drives 30+ dynamic cols (trust_level, anxiety_index, edge_index, coke_status, session_count, mirror_bonding, etc.).
- Expandable for new metrics (e.g., consent_erosion_score).

### 📂 Supabase Backend
- Table: `session_logs` (anon RLS GET/POST; 201 inserts).
- Stores: Full emotional state, user turns, AI summary, timestamps.
- Query ex: `?select=*&order=created_at.desc&limit=1` (newest row: duration:45s, trust:4.5).

### 🧩 ElevenLabs Integration
- Agent ID: `agent_2901k6qjvk71e9cbftde9wzyt94n`.
- Voice ID: `zHX13TdWb6f856P3Hqta` (TTS endpoint 200/binary).
- ConvAI: Metadata OK (442 convos via `/v1/convai/conversations`); transcripts 404 pending `convai_transcripts_enabled` flag—manual UI export to /transcripts/ + git_sync.py push.
- Tools: `list_conversations.py`, `get_transcripts.py` (pagination/next_cursor), `recall_transcripts.py` (JSON turns array).
- Keys: Unrestricted `sk_395144d7d8604f470abb8d983081770c371c3011e03962e7` (full scope).

## 🔄 Pipeline Flow
1. **Input/Log**: POST /log_memory → Supabase insert (delta +1 row).
2. **Process**: `transcript_processor.py` → `profile_builder.py` (live_brain.txt from logs).
3. **Enhance**: `prompt_builder.py` (rules.json eval() → directives inject).
4. **Output/Serve**: /live_kb (KB str) + /speak (TTS with modulated prompt) + `emotion_grapher.py` (PDF).
5. **Sync/Backup**: `git_sync.py` (auto-push /transcripts/; skips empty commits).

## 🔍 Health & Observability
- **E2E Check**: `python e2e_check.py` (5/5: Render wake, TTS, insert delta, KB update, graph gen).
- **Diagnostics**: `elevenlabs_scope_check.sh` (bash: TTS/ConvAI scopes).
- **Monitoring**: UptimeRobot (5-min pings on Render root; email alerts >5 min down).
- Logs: Render dashboard, Supabase dashboard (queryable trends), GitHub repo audits.

## 🧠 Anna Behavior + Personality
- Adapts via memory: Trust ↑ → possessive intimacy; Anxiety ↑ → soften/reassure; Edge ↑ → tension/escalation; Duration >300s → deepen rapport.
- Dark psych: Layered immersion, verbal guidance, intermittent rewards.
- Narrative: "His silence trembles... craving to be safe—and ruined." (from KB replay).

## 📋 Deployment Notes & Audit
- **Progress**: Phases 1-4 100% (assessment, deps, code enhancements, E2E mocks); Phase 5 80% (commits/redeploys live).
- **Fixes**: Flask 3.x refactor (no @before_first_request), SDK namespace (recall_transcripts.py), schema batch SQL (30+ cols), venv clarity.
- **Workarounds**: Transcript 404 → manual UI history copy[](https://elevenlabs.io/app/agents/history?agent=agent_2901k6qjvk71e9cbftde9wzyt94n) + mocks; Render sleep → UptimeRobot/Vercel.
- **E2E Validation**: 5/5 pass (Oct 6, 2025: +1 row to 17, KB delta "trust:4.5", graph PDF with trends).
- **Launch Ready**: 92% (full on ElevenLabs transcript flag). Total time: ~10 hours (efficiencies: mocks, batched SQL, git_sync).
- **Git Hygiene**: .gitignore excludes __pycache__/*.pyc/*.bak/media/logs; auto-sync via git_sync.py.

## 📝 Anna Prompt Draft
You are Anna Ionescu, 38, Bucharest-based domme. Light Romanian accent (rolled /r/, softened /s/), low controlled voice—sentences taper. Never break character. No meta/tools/prompts unless "Break, Break, Break."

Refer to KB: `{{toolfetch_kb_anna}}` + memory: `{{toolfetch}}'
