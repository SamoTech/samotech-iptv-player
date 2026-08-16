"""Provider-free native libVLC lifecycle probe for the Windows CI runner.

This probe intentionally exercises only a temporary local silent WAV source. It does
not construct a provider URL, call the IPTV application, or log paths, credentials,
tokens, cookies, MAC addresses, or stream values.
"""

from __future__ import annotations

import sys
import tempfile
import time
import wave
from pathlib import Path
from threading import Event, Lock


def _write_silent_wav(path: Path, *, duration_s: int = 3) -> None:
    """Create a short deterministic local WAV source without external media downloads."""
    sample_rate = 8_000
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(b"\x00\x00" * sample_rate * duration_s)


def _wait_for(
    observed: set[str],
    expected: set[str],
    wake: Event,
    observed_lock: Lock,
    timeout_s: float,
) -> bool:
    """Wait for callbacks without performing any work in the callback thread."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        with observed_lock:
            complete = expected.issubset(observed)
        if complete:
            return True
        wake.wait(min(0.1, deadline - time.monotonic()))
        wake.clear()
    with observed_lock:
        return expected.issubset(observed)


def _release(target: object) -> None:
    release = getattr(target, "release", None)
    if callable(release):
        release()


def main() -> int:
    """Run a local-media lifecycle sequence against native Windows libVLC."""
    if sys.platform != "win32":
        print("native_vlc_lifecycle=SKIP reason=windows_required")
        return 0

    try:
        import vlc  # type: ignore[import-untyped]
    except Exception as exc:  # noqa: BLE001
        print(f"native_vlc_binding=FAIL error_type={type(exc).__name__}")
        return 1

    instance: object | None = None
    player: object | None = None
    active_media: object | None = None
    observed_lock = Lock()
    first_play_observed: set[str] = set()
    first_play_wake = Event()
    first_phase_manager: object | None = None
    replacement_phase_manager: object | None = None
    stop_completed = False

    try:
        instance = vlc.Instance("--aout=dummy", "--vout=dummy", "--no-video", "--quiet")
        player = instance.media_player_new()
        event_types = {
            "OPENING": vlc.EventType.MediaPlayerOpening,
            "BUFFERING": vlc.EventType.MediaPlayerBuffering,
            "PLAYING": vlc.EventType.MediaPlayerPlaying,
            "ERROR": vlc.EventType.MediaPlayerEncounteredError,
            "END": vlc.EventType.MediaPlayerEndReached,
            "STOPPED": vlc.EventType.MediaPlayerStopped,
        }

        def attach_phase_observers(observed: set[str], wake: Event) -> object:
            """Attach callbacks that can mutate only one playback generation's evidence."""
            phase_manager = vlc.libvlc_media_player_event_manager(player)
            for label, event_type in event_types.items():

                def on_event(_event: object, name: str = label) -> None:
                    """Record one aggregate label and return immediately on the native thread."""
                    with observed_lock:
                        observed.add(name)
                    wake.set()

                phase_manager.event_attach(event_type, on_event)
            return phase_manager

        def detach_phase_observers(phase_manager: object) -> None:
            """Detach the completed media generation before attaching the next one."""
            for event_type in event_types.values():
                phase_manager.event_detach(event_type)

        first_phase_manager = attach_phase_observers(first_play_observed, first_play_wake)

        print("native_vlc_binding=PASS")
        print("native_vlc_instance=PASS")
        print(f"native_vlc_event_callbacks_registered={len(event_types)}")

        with tempfile.TemporaryDirectory(prefix="samotech-vlc-probe-") as temporary_directory:
            source = Path(temporary_directory) / "silence.wav"
            _write_silent_wav(source)

            active_media = instance.media_new_path(str(source))
            player.set_media(active_media)
            if player.play() < 0:
                raise RuntimeError("native_play_failed")
            if not _wait_for(
                first_play_observed,
                {"PLAYING", "END"},
                first_play_wake,
                observed_lock,
                timeout_s=12.0,
            ):
                raise RuntimeError("native_first_playing_or_end_event_missing")
            with observed_lock:
                first_play_labels = ",".join(sorted(first_play_observed))
                buffering_observed = "BUFFERING" in first_play_observed
            required_control_methods = (
                "get_time",
                "get_length",
                "set_time",
                "get_position",
                "set_position",
                "audio_get_volume",
                "audio_set_volume",
                "audio_get_mute",
                "audio_toggle_mute",
                "audio_get_track_description",
                "audio_get_track",
                "audio_set_track",
                "video_get_spu_description",
                "video_get_spu",
                "video_set_spu",
                "video_get_aspect_ratio",
                "video_set_aspect_ratio",
            )
            missing_methods = [
                name
                for name in required_control_methods
                if not callable(getattr(player, name, None))
            ]
            if missing_methods:
                raise RuntimeError("native_control_method_missing")
            audio_description = player.audio_get_track_description()
            subtitle_description = player.video_get_spu_description()
            print("native_vlc_control_methods=PASS")
            print(f"native_vlc_audio_description_type={type(audio_description).__name__}")
            print(f"native_vlc_subtitle_description_type={type(subtitle_description).__name__}")
            print(f"native_vlc_first_play_events={first_play_labels}")
            print(
                "native_vlc_buffering_observed="
                f"{'PASS' if buffering_observed else 'NOT_OBSERVED'}"
            )
            _release(active_media)
            active_media = None
            detach_phase_observers(first_phase_manager)
            first_phase_manager = None

            replacement_play_observed: set[str] = set()
            replacement_play_wake = Event()
            replacement_phase_manager = attach_phase_observers(
                replacement_play_observed,
                replacement_play_wake,
            )
            active_media = instance.media_new_path(str(source))
            player.set_media(active_media)
            if player.play() < 0:
                raise RuntimeError("native_replacement_play_failed")
            if not _wait_for(
                replacement_play_observed,
                {"PLAYING"},
                replacement_play_wake,
                observed_lock,
                timeout_s=8.0,
            ):
                raise RuntimeError("native_replacement_playing_missing")
            player.stop()
            if not _wait_for(
                replacement_play_observed,
                {"STOPPED"},
                replacement_play_wake,
                observed_lock,
                timeout_s=8.0,
            ):
                raise RuntimeError("native_stop_event_missing")
            stop_completed = True
            with observed_lock:
                replacement_play_labels = ",".join(sorted(replacement_play_observed))
            print(f"native_vlc_replacement_play_events={replacement_play_labels}")
            detach_phase_observers(replacement_phase_manager)
            replacement_phase_manager = None

        print("native_vlc_media_replacement=PASS")
        print("native_vlc_stop_cleanup=PASS")
        print("native_vlc_lifecycle=PASS")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"native_vlc_lifecycle=FAIL error_type={type(exc).__name__}")
        return 1
    finally:
        for phase_manager in (first_phase_manager, replacement_phase_manager):
            if phase_manager is not None:
                try:
                    detach_phase_observers(phase_manager)
                except Exception as exc:  # noqa: BLE001
                    print(f"native_vlc_cleanup_detach=FAIL error_type={type(exc).__name__}")
        if active_media is not None:
            _release(active_media)
        if player is not None:
            if not stop_completed:
                try:
                    player.stop()
                except Exception as exc:  # noqa: BLE001
                    print(f"native_vlc_cleanup_stop=FAIL error_type={type(exc).__name__}")
            _release(player)
        if instance is not None:
            _release(instance)


if __name__ == "__main__":
    raise SystemExit(main())
