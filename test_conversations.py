from elevenlabs import ElevenLabs

api_key = "sk_0434e282b02f333781fb7568cb4f9cbbf4449442a1537d36"  # New Agents key
client = ElevenLabs(api_key=api_key)

try:
  conversations = client.conversations.list()
  print("Conversations list:", conversations)
except Exception as e:
  print("ERROR:", str(e))
