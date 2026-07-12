"""Voicebox plugin for Hermes Agent.

Registers Voicebox (https://voicebox.sh) as a TTS and STT backend, and
bundles a skill teaching the agent when and how to use Voicebox's wider
feature set (MCP tools, Captures recall, voice selection).

Select the providers in ~/.hermes/config.yaml:

    tts:
      provider: voicebox
    stt:
      provider: voicebox

Agent-facing tools (speak on demand, transcribe a file, list captures and
profiles) intentionally live on Voicebox's own MCP server rather than
here — connect it with `hermes mcp configure voicebox` or a
`mcp_servers.voicebox` config block. This plugin only wires Hermes's own
voice pipeline.
"""

from pathlib import Path

__version__ = "0.1.0"


def register(ctx) -> None:
    """Plugin entry point — called once at Hermes startup."""
    from .stt import VoiceboxTranscriptionProvider
    from .tts import VoiceboxTTSProvider

    ctx.register_tts_provider(VoiceboxTTSProvider())
    ctx.register_transcription_provider(VoiceboxTranscriptionProvider())

    # ctx.register_skill landed after the provider hooks; stay compatible
    # with Hermes versions that predate it.
    if hasattr(ctx, "register_skill"):
        skills_dir = Path(__file__).parent / "skills"
        if skills_dir.is_dir():
            for child in sorted(skills_dir.iterdir()):
                skill_md = child / "SKILL.md"
                if child.is_dir() and skill_md.exists():
                    ctx.register_skill(child.name, skill_md)
