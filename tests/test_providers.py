"""Provider tests — contract behavior against a mocked VoiceboxClient."""

from unittest import mock

import pytest

from hermes_voicebox.client import (
    VoiceboxError,
    VoiceboxUnreachable,
    WhisperModelDownloading,
)
from hermes_voicebox.stt import VoiceboxTranscriptionProvider
from hermes_voicebox.tts import VoiceboxTTSProvider


def _client(**overrides):
    client = mock.Mock()
    client.is_healthy.return_value = True
    client.profiles.return_value = [{"id": "p1", "name": "Morgan", "language": "en"}]
    client.resolve_profile_id.return_value = "p1"
    client.synthesize.return_value = b"RIFFwav"
    client.transcribe.return_value = "hello world"
    for key, value in overrides.items():
        setattr(client, key, value)
    return client


class TestTTSProvider:
    def test_name_is_not_a_builtin(self):
        # Built-in names are rejected by the Hermes registry.
        builtins = {
            "edge", "elevenlabs", "openai", "minimax", "xai",
            "mistral", "gemini", "neutts", "kittentts", "piper",
        }
        assert VoiceboxTTSProvider(_client()).name not in builtins

    def test_synthesize_writes_wav_and_fixes_extension(self, tmp_path):
        provider = VoiceboxTTSProvider(_client())
        requested = tmp_path / "reply.mp3"
        out = provider.synthesize("hi", str(requested), voice="Morgan")
        assert out == str(tmp_path / "reply.wav")
        assert (tmp_path / "reply.wav").read_bytes() == b"RIFFwav"

    def test_synthesize_keeps_wav_extension(self, tmp_path):
        provider = VoiceboxTTSProvider(_client())
        requested = tmp_path / "reply.wav"
        assert provider.synthesize("hi", str(requested), format="wav") == str(requested)

    def test_model_maps_to_engine_and_language_forwarded(self, tmp_path):
        client = _client()
        provider = VoiceboxTTSProvider(client)
        provider.synthesize(
            "hi", str(tmp_path / "o.wav"), model="kokoro", language="ja"
        )
        client.synthesize.assert_called_once_with(
            "hi", "p1", engine="kokoro", language="ja"
        )

    def test_synthesize_raises_on_failure(self, tmp_path):
        # TTS contract: raise, the dispatcher wraps.
        client = _client()
        client.resolve_profile_id.side_effect = VoiceboxError("no profiles")
        with pytest.raises(VoiceboxError):
            VoiceboxTTSProvider(client).synthesize("hi", str(tmp_path / "o.wav"))

    def test_availability_tracks_health(self):
        assert VoiceboxTTSProvider(_client()).is_available() is True
        down = _client()
        down.is_healthy.return_value = False
        assert VoiceboxTTSProvider(down).is_available() is False

    def test_list_voices_shape(self):
        voices = VoiceboxTTSProvider(_client()).list_voices()
        assert voices == [{"id": "p1", "display": "Morgan", "language": "en"}]

    def test_voice_compatible(self):
        assert VoiceboxTTSProvider(_client()).voice_compatible is True


class TestTranscriptionProvider:
    def test_name_is_not_a_builtin(self):
        builtins = {"local", "local_command", "groq", "openai", "mistral", "xai"}
        assert VoiceboxTranscriptionProvider(_client()).name not in builtins

    def test_success_envelope(self, tmp_path):
        provider = VoiceboxTranscriptionProvider(_client())
        result = provider.transcribe(str(tmp_path / "a.ogg"), model="turbo")
        assert result == {
            "success": True,
            "transcript": "hello world",
            "provider": "voicebox",
        }

    def test_downloading_maps_to_error_envelope(self, tmp_path):
        client = _client()
        client.transcribe.side_effect = WhisperModelDownloading("whisper-turbo")
        result = VoiceboxTranscriptionProvider(client).transcribe(str(tmp_path / "a.ogg"))
        assert result["success"] is False
        assert "whisper-turbo" in result["error"]
        assert result["transcript"] == ""

    def test_unreachable_maps_to_friendly_error(self, tmp_path):
        client = _client()
        client.transcribe.side_effect = VoiceboxUnreachable("http://127.0.0.1:17493")
        result = VoiceboxTranscriptionProvider(client).transcribe(str(tmp_path / "a.ogg"))
        assert result["success"] is False
        assert "is the app running" in result["error"]

    def test_never_raises(self, tmp_path):
        # STT contract: always return the envelope, even on unexpected errors.
        client = _client()
        client.transcribe.side_effect = RuntimeError("boom")
        result = VoiceboxTranscriptionProvider(client).transcribe(str(tmp_path / "a.ogg"))
        assert result["success"] is False
        assert result["provider"] == "voicebox"


class TestRegister:
    def test_register_wires_both_providers_and_skill(self):
        import hermes_voicebox

        ctx = mock.Mock()
        hermes_voicebox.register(ctx)

        (tts_provider,) = ctx.register_tts_provider.call_args.args
        (stt_provider,) = ctx.register_transcription_provider.call_args.args
        assert tts_provider.name == "voicebox"
        assert stt_provider.name == "voicebox"

        skill_names = [c.args[0] for c in ctx.register_skill.call_args_list]
        assert "voicebox" in skill_names

    def test_register_tolerates_old_hermes_without_register_skill(self):
        import hermes_voicebox

        ctx = mock.Mock(spec=["register_tts_provider", "register_transcription_provider"])
        hermes_voicebox.register(ctx)  # must not raise
        ctx.register_tts_provider.assert_called_once()
