param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,
    [string]$RuntimeLabel = "default"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolvedExe = (Resolve-Path $Executable).Path
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$OutputRoot = (Resolve-Path $OutputRoot).Path
$evidence = [ordered]@{
    mode = ""
    runtime_label = $RuntimeLabel
    executable = $resolvedExe
    executable_size_bytes = (Get-Item $resolvedExe).Length
    executable_sha256 = (Get-FileHash -Algorithm SHA256 $resolvedExe).Hash.ToLowerInvariant()
    os = (Get-CimInstance Win32_OperatingSystem).Caption
    os_version = [Environment]::OSVersion.Version.ToString()
    architecture = [Environment]::Is64BitOperatingSystem
    temp = [System.IO.Path]::GetTempPath()
    path_cases = @()
}

$exeName = Split-Path $resolvedExe -Leaf
$sourceBundle = Split-Path $resolvedExe -Parent
$caseRoots = @(
    @{ Name = "space"; Root = (Join-Path $env:RUNNER_TEMP "SamoTech Forensic Acceptance") },
    @{ Name = "unicode"; Root = (Join-Path $env:RUNNER_TEMP "SamoTech Forensic Acceptance 测试") },
    @{ Name = "arbitrary-cwd"; Root = (Join-Path $env:RUNNER_TEMP "SamoTech Forensic Acceptance CWD") }
)
if (Test-Path "D:\") {
    $caseRoots += @{ Name = "d-drive"; Root = "D:\Profile\Downloads\SamoTech Forensic Acceptance" }
} else {
    $evidence.d_drive_available = $false
}
$evidence.d_drive_available = [bool](Test-Path "D:\")

function Get-ModuleSnapshot([System.Diagnostics.Process]$Process) {
    $modules = @()
    try {
        $Process.Refresh()
        $modules = @($Process.Modules | ForEach-Object { $_.FileName })
    } catch {
        $modules = @("<module-enumeration-failed:$($_.Exception.GetType().Name)>")
    }
    return $modules
}

function Get-MeiSnapshot {
    return @(
        Get-ChildItem -Path ([System.IO.Path]::GetTempPath()) -Filter "_MEI*" -Directory -ErrorAction SilentlyContinue |
            ForEach-Object { $_.FullName }
    )
}

function Invoke-ForensicCaseProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,
        [Parameter(Mandatory = $true)]
        [string]$Argument,
        [Parameter(Mandatory = $true)]
        [string]$DiagnosticPath
    )

    $env:SAMOTECH_STARTUP_DIAGNOSTIC_PATH = $DiagnosticPath
    Remove-Item $DiagnosticPath -Force -ErrorAction SilentlyContinue
    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList @($Argument, "--diagnostic") `
        -WorkingDirectory $WorkingDirectory `
        -PassThru
    if (-not $process.WaitForExit(90 * 1000)) {
        $process.Kill()
        $process.WaitForExit()
        return [pscustomobject]@{ ExitCode = -2; TimedOut = $true }
    }
    $process.Refresh()
    return [pscustomobject]@{ ExitCode = [int]$process.ExitCode; TimedOut = $false }
}

$hadFailure = $false
foreach ($case in $caseRoots) {
    $caseRoot = $case.Root
    if (Test-Path $caseRoot) {
        Remove-Item -Recurse -Force $caseRoot
    }
    New-Item -ItemType Directory -Force -Path $caseRoot | Out-Null
    $caseExe = Join-Path $caseRoot $exeName
    Copy-Item $resolvedExe $caseExe -Force
    if ((Split-Path $sourceBundle -Leaf) -eq "onedir") {
        $sourceInternal = Join-Path $sourceBundle "_internal"
        if (Test-Path $sourceInternal) {
            Copy-Item $sourceInternal (Join-Path $caseRoot "_internal") -Recurse -Force
        }
        Get-ChildItem -Path $sourceBundle -File | Where-Object { $_.Name -ne $exeName } | Copy-Item -Destination $caseRoot -Force
    }

    $caseEvidence = [ordered]@{
        name = $case.Name
        root = $caseRoot
        cwd = if ($case.Name -eq "arbitrary-cwd") { $env:SystemRoot } else { $caseRoot }
        process_probe = [ordered]@{}
        packaged_vlc = [ordered]@{}
        qt_only = [ordered]@{}
        smoke = [ordered]@{}
    }

    $probePath = Join-Path $OutputRoot "$($case.Name)-process-probe.json"
    $probeDiag = Join-Path $OutputRoot "$($case.Name)-process-diagnostic.json"
    $env:SAMOTECH_STARTUP_DIAGNOSTIC_PATH = $probeDiag
    Remove-Item $probeDiag -Force -ErrorAction SilentlyContinue
    $probe = Start-Process -FilePath $caseExe -ArgumentList @("--smoke-test", "--diagnostic") -WorkingDirectory $caseEvidence.cwd -PassThru
    $samples = @()
    $start = Get-Date
    while (-not $probe.HasExited -and ((Get-Date) - $start).TotalSeconds -lt 8) {
        $samples += [ordered]@{
            elapsed_seconds = [math]::Round(((Get-Date) - $start).TotalSeconds, 3)
            pid = $probe.Id
            modules = @(Get-ModuleSnapshot $probe)
            mei = @(Get-MeiSnapshot)
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not $probe.HasExited) {
        $probe.Kill()
        $probe.WaitForExit()
    }
    $probe.Refresh()
    $caseEvidence.process_probe.pid = $probe.Id
    $caseEvidence.process_probe.exit_code = $probe.ExitCode
    $caseEvidence.process_probe.samples = $samples
    $caseEvidence.process_probe.diagnostic_exists = Test-Path $probeDiag
    if (Test-Path $probeDiag) {
        Copy-Item $probeDiag $probePath -Force
        $caseEvidence.process_probe.diagnostic = Get-Content $probeDiag -Raw | ConvertFrom-Json
    }

    $vlcDiag = Join-Path $OutputRoot "$($case.Name)-packaged-vlc.json"
    $vlcResult = Invoke-ForensicCaseProcess `
        -FilePath $caseExe `
        -WorkingDirectory $caseEvidence.cwd `
        -Argument "--packaged-vlc-test" `
        -DiagnosticPath $vlcDiag
    $caseEvidence.packaged_vlc.exit_code = $vlcResult.ExitCode
    $caseEvidence.packaged_vlc.timed_out = $vlcResult.TimedOut
    $hadFailure = $hadFailure -or $vlcResult.TimedOut
    $caseEvidence.packaged_vlc.diagnostic_exists = Test-Path $vlcDiag
    if (Test-Path $vlcDiag) {
        $caseEvidence.packaged_vlc.diagnostic = Get-Content $vlcDiag -Raw | ConvertFrom-Json
    }

    $qtDiag = Join-Path $OutputRoot "$($case.Name)-qt-only.json"
    $qtResult = Invoke-ForensicCaseProcess `
        -FilePath $caseExe `
        -WorkingDirectory $caseEvidence.cwd `
        -Argument "--qt-only-test" `
        -DiagnosticPath $qtDiag
    $caseEvidence.qt_only.exit_code = $qtResult.ExitCode
    $caseEvidence.qt_only.timed_out = $qtResult.TimedOut
    $hadFailure = $hadFailure -or $qtResult.TimedOut
    $caseEvidence.qt_only.diagnostic_exists = Test-Path $qtDiag
    if (Test-Path $qtDiag) {
        $caseEvidence.qt_only.diagnostic = Get-Content $qtDiag -Raw | ConvertFrom-Json
    }

    $smokeDiag = Join-Path $OutputRoot "$($case.Name)-smoke.json"
    $smokeResult = Invoke-ForensicCaseProcess `
        -FilePath $caseExe `
        -WorkingDirectory $caseEvidence.cwd `
        -Argument "--smoke-test" `
        -DiagnosticPath $smokeDiag
    $caseEvidence.smoke.exit_code = $smokeResult.ExitCode
    $caseEvidence.smoke.timed_out = $smokeResult.TimedOut
    $hadFailure = $hadFailure -or $smokeResult.TimedOut
    $caseEvidence.smoke.diagnostic_exists = Test-Path $smokeDiag
    if (Test-Path $smokeDiag) {
        $caseEvidence.smoke.diagnostic = Get-Content $smokeDiag -Raw | ConvertFrom-Json
    }

    $evidence.path_cases += $caseEvidence
}

$evidence.mode = if ($resolvedExe -match "forensic-([^-\\]+(?:-[^-\\]+)*)") { $Matches[1] } else { "unknown" }
$evidence | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 (Join-Path $OutputRoot "forensic-execution-evidence.json")
$evidence | ConvertTo-Json -Depth 12
if ($hadFailure) {
    exit 2
}
