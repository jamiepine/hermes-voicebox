"""Test bootstrap.

The providers subclass Hermes ABCs (agent.tts_provider.TTSProvider,
agent.transcription_provider.TranscriptionProvider). When hermes-agent is
installed in the environment the real ABCs are used; otherwise minimal
stubs matching the documented contracts are installed so the suite runs
standalone (CI does not depend on hermes-agent).
"""

from __future__ import annotations

import abc
import sys
import types


def _install_stub_abcs() -> None:
    try:
        import agent.transcription_provider  # noqa: F401
        import agent.tts_provider  # noqa: F401

        return
    except ImportError:
        pass

    class TTSProvider(abc.ABC):
        @property
        @abc.abstractmethod
        def name(self) -> str: ...

        @property
        def display_name(self) -> str:
            return self.name.title()

        def is_available(self) -> bool:
            return True

        def list_voices(self):
            return []

        def list_models(self):
            return []

        def default_model(self):
            models = self.list_models()
            return models[0].get("id") if models else None

        def default_voice(self):
            voices = self.list_voices()
            return voices[0].get("id") if voices else None

        def get_setup_schema(self):
            return {"name": self.display_name, "badge": "", "tag": "", "env_vars": []}

        @abc.abstractmethod
        def synthesize(
            self,
            text,
            output_path,
            *,
            voice=None,
            model=None,
            speed=None,
            format="mp3",
            **extra,
        ) -> str: ...

        def stream(self, text, *, voice=None, model=None, format="opus", **extra):
            raise NotImplementedError

        @property
        def voice_compatible(self) -> bool:
            return False

    class TranscriptionProvider(abc.ABC):
        @property
        @abc.abstractmethod
        def name(self) -> str: ...

        @property
        def display_name(self) -> str:
            return self.name.title()

        def is_available(self) -> bool:
            return True

        def list_models(self):
            return []

        def default_model(self):
            models = self.list_models()
            return models[0].get("id") if models else None

        def get_setup_schema(self):
            return {"name": self.display_name, "badge": "", "tag": "", "env_vars": []}

        @abc.abstractmethod
        def transcribe(self, file_path, *, model=None, language=None, **extra): ...

    agent_pkg = types.ModuleType("agent")
    agent_pkg.__path__ = []  # mark as package
    tts_mod = types.ModuleType("agent.tts_provider")
    tts_mod.TTSProvider = TTSProvider
    stt_mod = types.ModuleType("agent.transcription_provider")
    stt_mod.TranscriptionProvider = TranscriptionProvider

    sys.modules["agent"] = agent_pkg
    sys.modules["agent.tts_provider"] = tts_mod
    sys.modules["agent.transcription_provider"] = stt_mod


_install_stub_abcs()
