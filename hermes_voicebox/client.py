"""Thin HTTP client for the Voicebox local API.

Voicebox's FastAPI backend listens on http://127.0.0.1:17493 while the
desktop app is running (Docker default: http://127.0.0.1:17600). The API
has no auth — it is loopback-only by default. Override the base URL with
the VOICEBOX_BASE_URL environment variable.

All Hermes-facing logic lives in tts.py / stt.py; this module knows only
HTTP shapes.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:17493"

HEALTH_TIMEOUT = 2
CATALOG_TIMEOUT = 10
# Local inference: the first generation/transcription after app start can
# include model load time.
SYNTHESIS_TIMEOUT = 600
TRANSCRIBE_TIMEOUT = 600


class VoiceboxError(RuntimeError):
    """Base error for Voicebox API failures."""


class VoiceboxUnreachable(VoiceboxError):
    """The Voicebox app is not running (connection refused)."""

    def __init__(self, base_url: str):
        super().__init__(
            f"Voicebox is not reachable at {base_url} — is the app running?"
        )


class WhisperModelDownloading(VoiceboxError):
    """Voicebox returned 202: the Whisper model is downloading in the background."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        super().__init__(
            f"Voicebox is still downloading {model_name} — try again in a minute."
        )


class VoiceboxClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (
            base_url
            or os.environ.get("VOICEBOX_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/")

    # -- health ---------------------------------------------------------

    def is_healthy(self) -> bool:
        """True when the Voicebox API answers /health. Never raises."""
        try:
            return requests.get(
                f"{self.base_url}/health", timeout=HEALTH_TIMEOUT
            ).ok
        except requests.RequestException:
            return False

    # -- voice profiles ---------------------------------------------------

    def profiles(self) -> List[Dict[str, Any]]:
        try:
            resp = requests.get(
                f"{self.base_url}/profiles", timeout=CATALOG_TIMEOUT
            )
        except requests.ConnectionError:
            raise VoiceboxUnreachable(self.base_url) from None
        resp.raise_for_status()
        return resp.json()

    def resolve_profile_id(self, voice: Optional[str]) -> str:
        """Resolve a Hermes voice value (profile name or id) to a profile id.

        With no voice given, the first profile wins.
        """
        profiles = self.profiles()
        if not profiles:
            raise VoiceboxError(
                "No voice profiles exist in Voicebox — create one in the app first."
            )
        if not voice:
            return profiles[0]["id"]
        needle = voice.strip()
        for p in profiles:
            if p["id"] == needle or p["name"].lower() == needle.lower():
                return p["id"]
        raise VoiceboxError(
            f"No Voicebox profile named {voice!r}. "
            f"Available: {', '.join(p['name'] for p in profiles)}"
        )

    # -- TTS ---------------------------------------------------------------

    def synthesize(
        self,
        text: str,
        profile_id: str,
        *,
        engine: Optional[str] = None,
        language: Optional[str] = None,
    ) -> bytes:
        """Generate speech synchronously; returns WAV bytes.

        POST /generate/stream blocks until generation completes and returns
        the audio in one response — no polling. ``engine=None`` is sent as an
        explicit JSON null, which defers to the profile's default engine
        (omitting the key would fall back to the API-wide default instead).
        """
        payload: Dict[str, Any] = {
            "profile_id": profile_id,
            "text": text,
            "engine": engine or None,
        }
        if language:
            payload["language"] = language
        try:
            resp = requests.post(
                f"{self.base_url}/generate/stream",
                json=payload,
                timeout=SYNTHESIS_TIMEOUT,
            )
        except requests.ConnectionError:
            raise VoiceboxUnreachable(self.base_url) from None
        resp.raise_for_status()
        return resp.content

    # -- STT ---------------------------------------------------------------

    def transcribe(
        self,
        file_path: str,
        *,
        model: Optional[str] = None,
        language: Optional[str] = None,
    ) -> str:
        """Transcribe an audio file; returns the transcript text.

        Raises WhisperModelDownloading on Voicebox's 202 response (the
        requested Whisper size isn't cached yet and is downloading in the
        background).
        """
        data: Dict[str, str] = {}
        if model:
            data["model"] = model
        if language:
            data["language"] = language
        try:
            with open(file_path, "rb") as f:
                resp = requests.post(
                    f"{self.base_url}/transcribe",
                    files={"file": f},
                    data=data,
                    timeout=TRANSCRIBE_TIMEOUT,
                )
        except requests.ConnectionError:
            raise VoiceboxUnreachable(self.base_url) from None
        if resp.status_code == 202:
            detail = {}
            try:
                detail = resp.json().get("detail", {})
            except ValueError:
                pass
            raise WhisperModelDownloading(
                detail.get("model_name", "the Whisper model")
            )
        resp.raise_for_status()
        return resp.json()["text"]
