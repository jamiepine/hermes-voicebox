"""Voicebox TTS provider for Hermes Agent.

Services Hermes's entire voice-output pipeline once selected via
``tts.provider: voicebox`` — spoken replies in the CLI/TUI, and voice
bubbles on gateway platforms. Mapping:

    Hermes ``voice``  ->  Voicebox profile (name or id)
    Hermes ``model``  ->  Voicebox engine (qwen, kokoro, chatterbox, ...)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.tts_provider import TTSProvider

from .client import VoiceboxClient

ENGINES = [
    {"id": "qwen", "display": "Qwen3-TTS (voice cloning)"},
    {"id": "qwen_custom_voice", "display": "Qwen CustomVoice (presets)"},
    {"id": "kokoro", "display": "Kokoro (fast presets)"},
    {"id": "chatterbox", "display": "Chatterbox Multilingual"},
    {"id": "chatterbox_turbo", "display": "Chatterbox Turbo"},
    {"id": "luxtts", "display": "LuxTTS"},
    {"id": "tada", "display": "HumeAI TADA"},
]


class VoiceboxTTSProvider(TTSProvider):
    def __init__(self, client: Optional[VoiceboxClient] = None):
        self._client = client or VoiceboxClient()

    @property
    def name(self) -> str:
        return "voicebox"

    @property
    def display_name(self) -> str:
        return "Voicebox"

    def is_available(self) -> bool:
        # Voicebox only listens while the app is running, so availability
        # is a live health check. Never raises.
        return self._client.is_healthy()

    def list_voices(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": p["id"],
                "display": p["name"],
                "language": p.get("language"),
            }
            for p in self._client.profiles()
        ]

    def list_models(self) -> List[Dict[str, Any]]:
        return ENGINES

    def default_model(self) -> Optional[str]:
        # None = defer to the Voicebox profile's own default engine.
        return None

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Voicebox",
            "badge": "local",
            "tag": "Local-first voice cloning TTS — Voicebox app must be running",
            "env_vars": [
                {
                    "key": "VOICEBOX_BASE_URL",
                    "prompt": "Voicebox API base URL (blank = http://127.0.0.1:17493)",
                    "url": "https://docs.voicebox.sh",
                },
            ],
        }

    def synthesize(
        self,
        text: str,
        output_path: str,
        *,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        speed: Optional[float] = None,
        format: str = "mp3",
        **extra: Any,
    ) -> str:
        # Contract: raise on failure — the Hermes dispatcher converts
        # exceptions to the standard error envelope.
        profile_id = self._client.resolve_profile_id(voice)
        audio = self._client.synthesize(
            text,
            profile_id,
            engine=model,
            language=extra.get("language"),
        )
        # Voicebox emits WAV; the ABC allows substituting the closest
        # format as long as the extension matches the bytes.
        if format != "wav":
            output_path = str(Path(output_path).with_suffix(".wav"))
        with open(output_path, "wb") as f:
            f.write(audio)
        return output_path

    @property
    def voice_compatible(self) -> bool:
        # WAV output — the gateway ffmpeg-converts to Opus for voice
        # bubbles on Telegram et al.
        return True
