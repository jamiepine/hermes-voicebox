"""VoiceboxClient tests — HTTP fully mocked."""

from unittest import mock

import pytest
import requests

from hermes_voicebox.client import (
    DEFAULT_BASE_URL,
    VoiceboxClient,
    VoiceboxError,
    VoiceboxUnreachable,
    WhisperModelDownloading,
)

PROFILES = [
    {"id": "p1", "name": "Morgan", "language": "en"},
    {"id": "p2", "name": "Jamie Clone", "language": "en"},
]


def _response(status=200, json_data=None, content=b""):
    resp = mock.Mock(spec=requests.Response)
    resp.status_code = status
    resp.ok = status < 400
    resp.content = content
    resp.json.return_value = json_data
    if status >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"HTTP {status}")
    else:
        resp.raise_for_status.return_value = None
    return resp


class TestBaseUrl:
    def test_default(self, monkeypatch):
        monkeypatch.delenv("VOICEBOX_BASE_URL", raising=False)
        assert VoiceboxClient().base_url == DEFAULT_BASE_URL

    def test_env_override_and_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("VOICEBOX_BASE_URL", "http://127.0.0.1:17600/")
        assert VoiceboxClient().base_url == "http://127.0.0.1:17600"

    def test_explicit_beats_env(self, monkeypatch):
        monkeypatch.setenv("VOICEBOX_BASE_URL", "http://127.0.0.1:17600")
        assert VoiceboxClient("http://other:1").base_url == "http://other:1"


class TestHealth:
    def test_healthy(self):
        with mock.patch("hermes_voicebox.client.requests.get") as get:
            get.return_value = _response(200)
            assert VoiceboxClient().is_healthy() is True

    def test_connection_error_is_false_not_raise(self):
        with mock.patch("hermes_voicebox.client.requests.get") as get:
            get.side_effect = requests.ConnectionError()
            assert VoiceboxClient().is_healthy() is False


class TestResolveProfileId:
    def _client_with_profiles(self, profiles):
        client = VoiceboxClient()
        client.profiles = mock.Mock(return_value=profiles)
        return client

    def test_no_voice_uses_first_profile(self):
        assert self._client_with_profiles(PROFILES).resolve_profile_id(None) == "p1"

    def test_matches_by_id(self):
        assert self._client_with_profiles(PROFILES).resolve_profile_id("p2") == "p2"

    def test_matches_by_name_case_insensitive(self):
        client = self._client_with_profiles(PROFILES)
        assert client.resolve_profile_id("jamie clone") == "p2"
        assert client.resolve_profile_id("  Morgan ") == "p1"

    def test_unknown_voice_lists_available(self):
        with pytest.raises(VoiceboxError, match="Morgan, Jamie Clone"):
            self._client_with_profiles(PROFILES).resolve_profile_id("nope")

    def test_empty_profiles(self):
        with pytest.raises(VoiceboxError, match="create one in the app"):
            self._client_with_profiles([]).resolve_profile_id(None)


class TestSynthesize:
    def test_payload_shape_and_bytes(self):
        with mock.patch("hermes_voicebox.client.requests.post") as post:
            post.return_value = _response(200, content=b"RIFFwav")
            out = VoiceboxClient().synthesize(
                "hello", "p1", engine="kokoro", language="en"
            )
        assert out == b"RIFFwav"
        payload = post.call_args.kwargs["json"]
        assert payload == {
            "profile_id": "p1",
            "text": "hello",
            "engine": "kokoro",
            "language": "en",
        }

    def test_no_engine_sends_explicit_null(self):
        # Explicit null defers to the profile's default engine; omitting the
        # key would fall back to the API-wide default instead.
        with mock.patch("hermes_voicebox.client.requests.post") as post:
            post.return_value = _response(200, content=b"x")
            VoiceboxClient().synthesize("hello", "p1")
        payload = post.call_args.kwargs["json"]
        assert "engine" in payload and payload["engine"] is None
        assert "language" not in payload

    def test_connection_error(self):
        with mock.patch("hermes_voicebox.client.requests.post") as post:
            post.side_effect = requests.ConnectionError()
            with pytest.raises(VoiceboxUnreachable, match="is the app running"):
                VoiceboxClient().synthesize("hello", "p1")


class TestTranscribe:
    def test_success(self, tmp_path):
        audio = tmp_path / "memo.ogg"
        audio.write_bytes(b"OggS")
        with mock.patch("hermes_voicebox.client.requests.post") as post:
            post.return_value = _response(200, json_data={"text": "hi", "duration": 1.2})
            text = VoiceboxClient().transcribe(str(audio), model="turbo", language="en")
        assert text == "hi"
        assert post.call_args.kwargs["data"] == {"model": "turbo", "language": "en"}

    def test_202_raises_model_downloading(self, tmp_path):
        audio = tmp_path / "memo.ogg"
        audio.write_bytes(b"OggS")
        body = {"detail": {"model_name": "whisper-turbo", "downloading": True}}
        with mock.patch("hermes_voicebox.client.requests.post") as post:
            post.return_value = _response(202, json_data=body)
            with pytest.raises(WhisperModelDownloading, match="whisper-turbo"):
                VoiceboxClient().transcribe(str(audio))

    def test_connection_error(self, tmp_path):
        audio = tmp_path / "memo.ogg"
        audio.write_bytes(b"OggS")
        with mock.patch("hermes_voicebox.client.requests.post") as post:
            post.side_effect = requests.ConnectionError()
            with pytest.raises(VoiceboxUnreachable):
                VoiceboxClient().transcribe(str(audio))
