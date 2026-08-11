# Infrastructure / Player

## Supported backend

**libVLC through `python-vlc` is the only supported playback backend.** The `VlcPlayerAdapter` implements the application `PlayerPort` for play, pause, resume, stop, and active-playback state.

Provider adapters remain responsible for advertising and exercising their own discovery, catalogue, EPG, category, and stream-resolution capabilities. A provider must resolve an authorized canonical URL before it is passed to `VlcPlayerAdapter`; the player layer does not contain provider credentials, sessions, or protocol-specific authentication state.

The first libVLC increment uses fake-backed adapter contracts so tests do not require an installed system VLC runtime. Production packaging must include a compatible libVLC installation alongside the Python binding.
