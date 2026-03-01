import os
import base64
import httpx
import weave

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default 'Rachel' voice

@weave.op()
async def generate_roast_audio(text: str):
    """
    Converts text to speech using ElevenLabs API.
    If no API key is provided, it logs the text and returns a 'dry-run' status.
    """
    if not ELEVENLABS_API_KEY:
        print(f"[ElevenLabs Mock] Generated roast audio for: \"{text}\"")
        return {"status": "dry-run", "message": "No API key found, audio skipped."}

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, headers=headers)
            if response.status_code == 200:
                audio_b64 = base64.b64encode(response.content).decode("utf-8")
                print(f"[ElevenLabs] Successfully generated audio ({len(response.content)} bytes)")
                return {"status": "success", "audio_b64": audio_b64}
            else:
                print(f"[ElevenLabs Error] {response.status_code}: {response.text}")
                return {"status": "error", "message": response.text}
        except Exception as e:
            print(f"[ElevenLabs Exception] {str(e)}")
            return {"status": "error", "message": str(e)}
