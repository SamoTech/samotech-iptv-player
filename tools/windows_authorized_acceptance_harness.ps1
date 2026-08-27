[CmdletBinding()]
param(
    [ValidateSet("Xtream", "MAG", "M3U")]
    [string]$Provider = "Xtream",
    [switch]$RunAuthorized,
    [string]$RunnerPath,
    [string]$SecretEnvName = "SAMOTECH_ACCEPTANCE_SECRET_JSON",
    [string]$OutputPath = (Join-Path (Get-Location) "acceptance-summary.json"),
    [ValidateRange(30, 3600)]
    [int]$TimeoutSeconds = 900
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# This harness never probes a provider by itself. The default path is a safe,
# explicit NOT_RUN result. An authorized runner must be supplied separately.
$gateNames = @(
    "AUTH",
    "LIVE_COUNT",
    "VOD_COUNT",
    "SERIES_COUNT",
    "EPISODE_COUNT",
    "EPG",
    "FIRST_FRAME",
    "AUDIO",
    "SUBTITLES",
    "PLAYBACK",
    "RESUME",
    "BUFFERING",
    "RECOVERY",
    "DISPOSAL"
)
$aggregateNames = @(
    "live_count",
    "vod_count",
    "series_count",
    "episode_count",
    "epg_entries"
)
$allowedStatuses = @("PASS", "FAIL", "NOT_RUN", "NOT_APPLICABLE", "BLOCKED")

function New-NotRunGates {
    $gates = [ordered]@{}
    foreach ($name in $gateNames) {
        $gates[$name] = "NOT_RUN"
    }
    return $gates
}

function New-Summary {
    param([string]$Reason)

    return [ordered]@{
        schema_version = 1
        provider = $Provider
        status = "NOT_RUN"
        reason = $Reason
        gates = (New-NotRunGates)
        aggregate = [ordered]@{}
        diagnostics = [ordered]@{
            redacted = $true
            raw_output_retained = $false
            raw_provider_data_retained = $false
        }
    }
}

function Write-SafeSummary {
    param([System.Collections.IDictionary]$Summary)

    $json = $Summary | ConvertTo-Json -Depth 6
    $parent = Split-Path -Parent $OutputPath
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Set-Content -LiteralPath $OutputPath -Value $json -Encoding UTF8
    # Print only the safe result path and status; never print secrets or runner output.
    Write-Output ("status={0} provider={1} result_written=true" -f $Summary.status, $Summary.provider)
}

function Set-NotRunReason {
    param(
        [System.Collections.IDictionary]$Summary,
        [string]$Reason
    )
    $Summary.status = "NOT_RUN"
    $Summary.reason = $Reason
    $Summary.gates = New-NotRunGates
    $Summary.aggregate = [ordered]@{}
}

$summary = New-Summary -Reason "authorized_acceptance_not_requested"

if (-not $RunAuthorized) {
    Write-SafeSummary -Summary $summary
    exit 0
}

if ([string]::IsNullOrWhiteSpace($RunnerPath) -or -not (Test-Path -LiteralPath $RunnerPath -PathType Leaf)) {
    Set-NotRunReason -Summary $summary -Reason "authorized_runner_not_configured"
    Write-SafeSummary -Summary $summary
    exit 0
}

$secret = [Environment]::GetEnvironmentVariable($SecretEnvName, "Process")
if ([string]::IsNullOrEmpty($secret)) {
    Set-NotRunReason -Summary $summary -Reason "approved_secret_not_injected"
    Write-SafeSummary -Summary $summary
    exit 0
}

$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ("samotech-acceptance-" + [Guid]::NewGuid().ToString("N"))
$resultPath = Join-Path $tempRoot "safe-result.json"
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
$previousSecret = [Environment]::GetEnvironmentVariable($SecretEnvName, "Process")
$process = $null
try {
    # The future runner contract receives the approved secret through the process
    # environment and must write only the safe-result schema to resultPath.
    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $RunnerPath
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    [void]$startInfo.ArgumentList.Add("--provider")
    [void]$startInfo.ArgumentList.Add($Provider)
    [void]$startInfo.ArgumentList.Add("--result-path")
    [void]$startInfo.ArgumentList.Add($resultPath)
    [Environment]::SetEnvironmentVariable($SecretEnvName, $secret, "Process")

    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    [void]$process.Start()
    # Drain but never persist or print runner stdout/stderr. Raw provider output
    # must not become a log, artifact, diagnostic, or report.
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        $process.Kill($true)
        Set-NotRunReason -Summary $summary -Reason "authorized_runner_timeout"
    } else {
        [void]$stdoutTask.Result
        [void]$stderrTask.Result
        if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
            Set-NotRunReason -Summary $summary -Reason "safe_result_missing"
        } else {
            $rawResult = Get-Content -LiteralPath $resultPath -Raw
            # Reject any result that contains secret-shaped fields or raw provider
            # material before parsing or copying any value into the safe summary.
            $unsafePattern = "(?i)(password|passwd|token|cookie|authorization|mac|secret|signed.?url|private.?url|request.?header|response.?body|https?://)"
            if ($rawResult -match $unsafePattern) {
                Set-NotRunReason -Summary $summary -Reason "unsafe_result_rejected"
            } else {
                $candidate = $rawResult | ConvertFrom-Json
                $safeGates = New-NotRunGates
                foreach ($name in $gateNames) {
                    $value = $candidate.gates.$name
                    if ($null -ne $value -and $allowedStatuses -contains [string]$value) {
                        $safeGates[$name] = [string]$value
                    }
                }
                $safeAggregate = [ordered]@{}
                foreach ($name in $aggregateNames) {
                    $value = $candidate.aggregate.$name
                    if ($null -ne $value -and $value -is [int] -and $value -ge 0) {
                        $safeAggregate[$name] = [int]$value
                    }
                }
                $summary.gates = $safeGates
                $summary.aggregate = $safeAggregate
                $summary.status = if ($safeGates.Values -contains "FAIL") { "FAIL" } elseif ($safeGates.Values -contains "PASS") { "PASS" } else { "NOT_RUN" }
                $summary.reason = if ($process.ExitCode -eq 0) { "safe_result_accepted" } else { "runner_nonzero_safe_result" }
            }
        }
    }
} catch {
    Set-NotRunReason -Summary $summary -Reason "authorized_runner_failed"
} finally {
    if ($null -ne $process) {
        $process.Dispose()
    }
    [Environment]::SetEnvironmentVariable($SecretEnvName, $previousSecret, "Process")
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-SafeSummary -Summary $summary
exit 0
