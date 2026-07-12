# hermes-voicebox

[Voicebox](https://voicebox.sh) TTS + STT providers for
[Hermes Agent](https://github.com/NousResearch/hermes-agent) — voice cloning
and Whisper transcription, fully local. Once selected, Hermes's entire voice
pipeline runs through the Voicebox app on your machine:

- **Voice out** — spoken replies in the CLI/TUI and voice bubbles on
  Telegram/Discord/WhatsApp/Slack/Signal are synthesized in one of your
  cloned or preset Voicebox voices. No ElevenLabs key, no cloud.
- **Voice in** — incoming voice messages and push-to-talk recordings are
  transcribed by the Whisper models bundled with Voicebox. Audio never
  leaves your machine.
- **Bundled skill** — teaches the agent when speaking aloud is appropriate,
  how to pick voices, and to recall your dictated
  [Captures](https://docs.voicebox.sh/overview/captures) through Voicebox's
  MCP server.

This plugin wires Hermes's *own* voice pipeline. Agent-invoked tools (speak
on demand, transcribe a file, list captures/profiles) live on Voicebox's
built-in [MCP server](https://docs.voicebox.sh/overview/mcp-server) —
connect both for the full experience.

## Requirements

- [Voicebox](https://voicebox.sh) running locally (desktop app, or Docker on
  `127.0.0.1:17600`)
- Hermes Agent, Python 3.11+

## Install

**Pip (recommended)** — into the same environment Hermes runs in:

```bash
pip install hermes-voicebox
```

(Or straight from git: `pip install git+https://github.com/jamiepine/hermes-voicebox`)

Hermes auto-discovers the plugin through its `hermes_agent.plugins` entry
point on next startup.

**Directory install** — no pip:

```bash
git clone https://github.com/jamiepine/hermes-voicebox /tmp/hermes-voicebox
cp -r /tmp/hermes-voicebox/hermes_voicebox ~/.hermes/plugins/voicebox
hermes plugins enable voicebox
```

## Configure

In `~/.hermes/config.yaml`:

```yaml
tts:
  provider: voicebox

stt:
  provider: voicebox
```

And optionally connect Voicebox's MCP server for agent-invoked tools:

```yaml
mcp_servers:
  voicebox:
    url: "http://127.0.0.1:17493/mcp"
    headers:
      X-Voicebox-Client-Id: "hermes"
```

Voice selection: `tts.voice` (or the tool's `voice` argument) accepts a
Voicebox profile **name or id**; with nothing set, your first profile is
used. Pass a Voicebox engine id (`qwen`, `kokoro`, `chatterbox`, …) as the
Hermes `model` to override the profile's default engine.

Running Voicebox somewhere other than the desktop app's default port:

```bash
export VOICEBOX_BASE_URL=http://127.0.0.1:17600   # e.g. Docker
```

## Behavior notes

- Voicebox must be running — the desktop app only serves the API while
  open. Both providers health-check live, so Hermes's picker reflects
  reality.
- First generation after app start is slower while the TTS engine loads;
  first transcription with a new Whisper size triggers a background
  download and returns a friendly "try again in a minute".

## Development

```bash
pip install -e ".[dev]"
pytest
```

Tests are fully offline (HTTP mocked) and run without hermes-agent
installed — minimal ABC stubs matching the Hermes provider contracts are
used when the real ones aren't importable.

## Docs

- [Voicebox × Hermes integration guide](https://docs.voicebox.sh/overview/hermes-agent)
- Hermes developer guides: [TTS providers](https://hermes-agent.nousresearch.com/docs/developer-guide/tts-provider-plugin) ·
  [Transcription providers](https://hermes-agent.nousresearch.com/docs/developer-guide/transcription-provider-plugin)

## License

MIT
