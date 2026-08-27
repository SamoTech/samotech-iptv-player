from pathlib import Path


def _read_harness() -> str:
    return (
        Path(__file__).parents[1] / "tools" / "windows_authorized_acceptance_harness.ps1"
    ).read_text(encoding="utf-8")


def test_windows_acceptance_harness_defaults_to_not_run_and_safe_output() -> None:
    source = _read_harness()

    assert "[switch]$RunAuthorized" in source
    assert "authorized_acceptance_not_requested" in source
    assert "raw_output_retained = $false" in source
    assert "raw_provider_data_retained = $false" in source
    assert "raw_provider_data_retained = $true" not in source
    assert "Invoke-WebRequest" not in source
    assert "Invoke-RestMethod" not in source
    assert "curl.exe" not in source
    assert "Write-Output $secret" not in source
    assert "Write-Output $rawResult" not in source
    assert "Write-Output $stdoutTask" not in source
    assert "Write-Output $stderrTask" not in source


def test_windows_acceptance_harness_uses_aggregate_allowlist() -> None:
    source = _read_harness()

    assert '"live_count"' in source
    assert '"vod_count"' in source
    assert '"series_count"' in source
    assert '"episode_count"' in source
    assert '"epg_entries"' in source
    assert "safe_result_accepted" in source
    assert "unsafe_result_rejected" in source
