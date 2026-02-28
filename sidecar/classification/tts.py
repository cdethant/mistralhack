"""
TTS (Text-to-Speech) via ElevenLabs API.
Returns base64-encoded MP3 audio.
"""
import os
import base64
import io

from elevenlabs import ElevenLabs

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID           = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # Sarah
MOCK_MODE          = os.getenv("MOCK_MODE", "false").lower() == "true"

# Tiny silent MP3 (44 bytes) used as fallback so the app never crashes on audio
_SILENT_MP3_B64 = (
    "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA"
    "//tQwAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAABAAADhgD///////////////////"
    "//////////////AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
)


def generate_tts(text: str) -> tuple[str, float]:
    """
    Generate speech for `text` using ElevenLabs.
    Returns (audio_base64, estimated_duration_sec).
    Falls back to silent audio on any error.
    """
    if MOCK_MODE or not ELEVENLABS_API_KEY:
        return _SILENT_MP3_B64, 0.0

    try:
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        # generate() returns a generator of audio chunks
        audio_bytes = b"".join(
            client.generate(
                text=text,
                voice=VOICE_ID,
                model="eleven_turbo_v2",
            )
        )
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        # Rough duration estimate: ~150 wpm → ~2.5 chars/word → avg 3 chars per 0.4s
        duration = max(1.5, len(text.split()) / 150 * 60)
        return audio_b64, round(duration, 1)
    except Exception as e:
        print(f"[tts] ElevenLabs error: {e} – returning silent fallback")
        return _SILENT_MP3_B64, 0.0
