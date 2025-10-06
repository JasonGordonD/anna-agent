#!/bin/bash
echo "Checking ElevenLabs API scope..."
curl -s -H "xi-api-key: $XI_API_KEY" https://api.elevenlabs.io/v1/user |
jq -r '
  if has("subscription") then
    "✔️  TTS access: ENABLED"
  else
    "❌  TTS access: DISABLED"
  end,
  (if .convai_enabled then "✔️  ConvAI access: ENABLED" else "❌  ConvAI access: DISABLED" end),
  (if .recordings_access then "✔️  Recordings access: ENABLED" else "❌  Recordings access: DISABLED" end)
'
