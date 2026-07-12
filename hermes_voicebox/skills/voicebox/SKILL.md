---
name: voicebox
description: "Voicebox voice I/O: when to speak aloud, pick voices, recall dictated Captures via MCP."
version: 0.1.0
platforms: [macos, windows, linux]
metadata:
  hermes:
    tags: [voicebox, voice, tts, stt, whisper, speak, transcribe, captures, dictation]
    related_skills: []
---

# Voicebox: Local Voice I/O

The user runs [Voicebox](https://voicebox.sh), a local-first voice studio.
It is wired into this Hermes install in up to two ways:

1. **Pipeline providers** (this plugin): when `tts.provider: voicebox` /
   `stt.provider: voicebox` are set, your spoken replies and all incoming
   voice-message transcription already flow through Voicebox automatically.
   You don't need to do anything for these.
2. **MCP tools** (if the `voicebox` MCP server is connected): tools named
   `mcp__voicebox__voicebox_speak`, `voicebox_transcribe`,
   `voicebox_list_profiles`, `voicebox_list_captures`. These are for
   *deliberate* voice actions and recall.

## When to speak aloud (MCP `speak`)

- The user explicitly asks ("read this to me", "say it in Morgan's voice").
- The user is away from the screen (they told you they're cooking, driving,
  etc.) and the reply is short and useful to hear.
- Do NOT speak unprompted in group chats, for long content (summarize
  first, then offer), or repeatedly after the user ignored/stopped audio.
- The `profile` argument accepts a profile **name or id** — list them with
  `voicebox_list_profiles` if unsure. Respect an explicitly requested voice;
  otherwise omit `profile` and Voicebox uses the binding the user set for
  this client.

## Captures = the user's dictation memory

Voicebox's Captures tab stores everything the user has dictated, with the
original audio preserved alongside each transcript. When the user refers to
something they *said* or *dictated* earlier ("that idea I recorded this
morning", "my voice note about the launch"), search Captures via
`voicebox_list_captures` **before** asking them to repeat it.

## Transcription behavior you should expect

- Whisper runs locally inside Voicebox. First use of a new model size
  triggers a background download — Voicebox answers with a "still
  downloading" error. Wait a minute and retry; tell the user what's
  happening rather than reporting a generic failure.
- If Voicebox is unreachable, the app isn't running. Say exactly that —
  "your Voicebox app doesn't seem to be open" — instead of a vague error.

## Voice selection quick reference

- Voices = Voicebox **profiles** (cloned or preset). Engines (`qwen`,
  `kokoro`, `chatterbox`, …) are per-profile defaults; only override the
  engine when the user asks for a specific one.
- Long text: fine to send — Voicebox chunks and crossfades automatically.
