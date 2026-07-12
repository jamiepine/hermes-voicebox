"""Voicebox STT provider for Hermes Agent.

Services Hermes's transcription pipeline once selected via
``stt.provider: voicebox`` — incoming voice messages on gateway platforms
and push-to-talk in the CLI/TUI. Whisper runs locally inside Voicebox;
audio never leaves the machine.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent.transcription_provider import TranscriptionProvider

from .client import VoiceboxClient, VoiceboxError, WhisperModelDownloading

WHISPER_MODELS = [
    {"id": "base", "display": "Whisper Base (fastest)"},
    {"id": "small", "display": "Whisper Small"},
    {"id": "medium", "display": "Whisper Medium"},
    {"id": "large", "display": "Whisper Large"},
    {"id": "turbo", "display": "Whisper Large v3 Turbo"},
]


class VoiceboxTranscriptionProvider(TranscriptionProvider):
    def __init__(self, client: Optional[VoiceboxClient] = None):
        self._client = client or VoiceboxClient()

    @property
    def name(self) -> str:
        return "voicebox"

    @property
    def display_name(self) -> str:
        return "Voicebox"

    def is_available(self) -> bool:
        return self._client.is_healthy()

    def list_models(self) -> List[Dict[str, Any]]:
        return WHISPER_MODELS

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Voicebox",
            "badge": "local",
            "tag": "Local Whisper via the Voicebox app — audio stays on-device",
            "env_vars": [
                {
                    "key": "VOICEBOX_BASE_URL",
                    "prompt": "Voicebox API base URL (blank = http://127.0.0.1:17493)",
                    "url": "https://docs.voicebox.sh",
                },
            ],
        }

    def transcribe(
        self,
        file_path: str,
        *,
        model: Optional[str] = None,
        language: Optional[str] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        # Contract: never raise — return the error envelope instead.
        # Error messages surface to end users on chat platforms, so they
        # distinguish "app not running" from "model downloading".
        try:
            transcript = self._client.transcribe(
                file_path, model=model, language=language
            )
        except (VoiceboxError, WhisperModelDownloading) as exc:
            return self._error(str(exc))
        except Exception as exc:  # requests errors, OSError, bad JSON
            return self._error(f"Voicebox transcription failed: {exc}")
        return {
            "success": True,
            "transcript": transcript,
            "provider": self.name,
        }

    def _error(self, message: str) -> Dict[str, Any]:
        return {
            "success": False,
            "transcript": "",
            "error": message,
            "provider": self.name,
        }
