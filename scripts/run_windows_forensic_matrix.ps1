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
    $vlcOutput = Join-Path $OutputRoot "$($case.Name)-packaged-vlc.output.txt"
    $env:SAMOTECH_STARTUP_DIAGNOSTIC_PATH = $vlcDiag
    Remove-Item $vlcDiag -Force -ErrorAction SilentlyContinue
    & $caseExe --packaged-vlc-test --diagnostic *> $vlcOutput
    $caseEvidence.packaged_vlc.exit_code = $LASTEXITCODE
    $caseEvidence.packaged_vlc.diagnostic_exists = Test-Path $vlcDiag
    if (Test-Path $vlcDiag) {
        $caseEvidence.packaged_vlc.diagnostic = Get-Content $vlcDiag -Raw | ConvertFrom-Json
    }

    $smokeDiag = Join-Path $OutputRoot "$($case.Name)-smoke.json"
    $smokeOutput = Join-Path $OutputRoot "$($case.Name)-smoke.output.txt"
    $env:SAMOTECH_STARTUP_DIAGNOSTIC_PATH = $smokeDiag
    Remove-Item $smokeDiag -Force -ErrorAction SilentlyContinue
    & $caseExe --smoke-test --diagnostic *> $smokeOutput
    $caseEvidence.smoke.exit_code = $LASTEXITCODE
    $caseEvidence.smoke.diagnostic_exists = Test-Path $smokeDiag
    if (Test-Path $smokeDiag) {
        $caseEvidence.smoke.diagnostic = Get-Content $smokeDiag -Raw | ConvertFrom-Json
    }

    $evidence.path_cases += $caseEvidence
}

$evidence.mode = if ($resolvedExe -match "forensic-([^-\\]+(?:-[^-\\]+)*)") { $Matches[1] } else { "unknown" }
$evidence | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 (Join-Path $OutputRoot "forensic-execution-evidence.json")
$evidence | ConvertTo-Json -Depth 12
