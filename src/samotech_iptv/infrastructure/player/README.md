# Player infrastructure

## Supported backend

**libVLC through `python-vlc` is the only supported playback and recording backend.** `VlcPlayerAdapter` implements the application `PlayerPort` for play, pause, resume, stop, active-playback state, and active-stream recording.

Recording is implemented with libVLC stream output: the adapter rebuilds the current media with a duplicate output that preserves display while writing an MPEG transport-stream (`.ts`) file. Starting or stopping recording restarts the active libVLC media on the same player instance; no MPV, WinRT, FFmpeg, or secondary media pipeline is introduced. The adapter accepts only local `.ts` destinations, rejects control characters and existing targets, and does not log stream URLs, provider credentials, or local output paths.

Provider adapters remain responsible for advertising and exercising their own discovery, catalogue, EPG, category, and stream-resolution capabilities. A provider must resolve an authorized canonical URL before it is passed to `VlcPlayerAdapter`; the player layer does not contain provider credentials, sessions, or protocol-specific authentication state.

The libVLC adapter uses fake-backed contracts so tests do not require an installed system VLC runtime. Production packaging must include a compatible libVLC installation alongside the Python binding.
