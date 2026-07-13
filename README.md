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

## What this actually does

Hermes already has voice features out of the box — it can speak replies
aloud, send voice bubbles, and transcribe voice memos people send it. Those
features need an engine to do the audio work, and Hermes ships with cloud
defaults: Microsoft Edge TTS for speaking, Groq/OpenAI Whisper for
transcribing.

**This plugin adds no new features. It swaps the engine behind the existing
ones** — like changing your default printer. Two before/after examples:

- *Someone sends your Hermes bot a voice memo on Telegram.* Hermes must
  transcribe it before the model can read it. Without this plugin, the
  audio is uploaded to Groq's or OpenAI's servers. With it, Hermes posts
  the file to your running Voicebox app and local Whisper transcribes it —
  the audio never leaves your machine.
- *Hermes speaks a reply* (voice mode, or a voice bubble in chat). Without
  this plugin: a stock Microsoft voice. With it: your cloned Voicebox
  profile.

Note what's absent from both: the agent deciding anything. Transcription
happens before the model runs; synthesis happens after it's done. This is
pipeline plumbing, not a tool the model calls — which is why MCP can't do
this job.

The complement is Voicebox's built-in
[MCP server](https://docs.voicebox.sh/overview/mcp-server), which covers
the *deliberate* voice actions ("read that back in Morgan's voice",
"what did I dictate this morning?") as tools the agent chooses to call.
Connect both for the full experience:

| | MCP server | This plugin |
|---|---|---|
| What it adds | New tools the agent can *choose* to call | Nothing visible — reroutes existing plumbing |
| Speak / transcribe when | The model decides to | Hermes's pipeline needs it (always) |
| Setup | `hermes mcp install voicebox` | `pip install hermes-voicebox` + two config lines |

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
- Provider contracts: `agent/tts_provider.py` and `agent/transcription_provider.py` in
  [hermes-agent](https://github.com/NousResearch/hermes-agent) (this plugin implements both ABCs)

## License

MIT
