import os
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
                # In a real desktop app, we'd play this audio immediately.
                # For the sidecar, we'll save it to a temp file or just acknowledge success.
                audio_path = "/tmp/roast_audio.mp3"
                with open(audio_path, "wb") as f:
                    f.write(response.content)
                
                # Command to play audio (platform specific)
                # os.system(f"afplay {audio_path}") # macOS
                # os.system(f"mpg123 {audio_path}") # Linux
                
                print(f"[ElevenLabs] Successfully generated audio to {audio_path}")
                return {"status": "success", "audio_path": audio_path}
            else:
                print(f"[ElevenLabs Error] {response.status_code}: {response.text}")
                return {"status": "error", "message": response.text}
        except Exception as e:
            print(f"[ElevenLabs Exception] {str(e)}")
            return {"status": "error", "message": str(e)}
