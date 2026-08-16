"""Probe native python-vlc track-description shapes using only a local silent WAV."""

from __future__ import annotations

import sys
import tempfile
import time
import wave
from pathlib import Path


def write_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(8_000)
        output.writeframes(b"\x00\x00" * 8_000)


def main() -> int:
    if sys.platform == "win32":
        pass
    try:
        import vlc  # type: ignore[import-untyped]
    except Exception as exc:  # noqa: BLE001
        print(f"binding=FAIL type={type(exc).__name__}")
        return 1

    instance = None
    player = None
    media = None
    try:
        instance = vlc.Instance("--aout=dummy", "--vout=dummy", "--no-video", "--quiet")
        player = instance.media_player_new()
        with tempfile.TemporaryDirectory(prefix="samotech-track-probe-") as temporary_directory:
            source = Path(temporary_directory) / "silence.wav"
            write_wav(source)
            media = instance.media_new_path(str(source))
            player.set_media(media)
            if player.play() < 0:
                print("play=FAIL")
                return 1
            time.sleep(0.4)
            for label, value in (
                ("audio_description", player.audio_get_track_description()),
                ("audio_active", player.audio_get_track()),
                ("subtitle_description", player.video_get_spu_description()),
                ("subtitle_active", player.video_get_spu()),
            ):
                print(f"{label}_type={type(value).__name__}")
                print(f"{label}_repr={value!r}")
            return 0
    finally:
        if player is not None:
            player.stop()
            player.release()
        if media is not None:
            media.release()
        if instance is not None:
            instance.release()


if __name__ == "__main__":
    raise SystemExit(main())
