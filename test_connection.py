from elevenlabs import ElevenLabs

client = ElevenLabs(api_key="1232ea6af7f2a81ecba73b2a8d551c189bfd131e5d533f70a42373091383b756")

voices = client.voices.get_all()
print(f"✅ Connected. Found {len(voices.voices)} voices.")
for v in voices.voices[:5]:
    print("-", v.name)
