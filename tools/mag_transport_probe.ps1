[CmdletBinding()]
param(
    [string]$PortalUrl = $env:MAG_PORTAL_URL,
    [string]$MacAddress = $env:MAG_MAC,
    [int]$TimeoutSeconds = 5
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($PortalUrl) -or [string]::IsNullOrWhiteSpace($MacAddress)) {
    throw 'Set MAG_PORTAL_URL and MAG_MAC in the environment or pass both parameters.'
}

$uri = [Uri]$PortalUrl
$port = if ($uri.IsDefaultPort) { if ($uri.Scheme -eq 'https') { 443 } else { 80 } } else { $uri.Port }
$addresses = [System.Net.Dns]::GetHostAddresses($uri.DnsSafeHost)
$ipv4 = $addresses | Where-Object { $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork } | Select-Object -First 1
if ($null -eq $ipv4) { throw 'No IPv4 address resolved.' }

$target = [ordered]@{
    hostname = $uri.DnsSafeHost
    resolved_ip = $ipv4.IPAddressToString
    port = $port
    protocol = $uri.Scheme
}

$query = 'type=stb&action=handshake&token=&JsHttpRequest=1-xml'
$endpoint = "$($uri.Scheme)://$($uri.DnsSafeHost):$port/portal.php?$query"
$referer = "$($uri.Scheme)://$($uri.DnsSafeHost)/c/"
$headers = @{
    Authorization = "MAC $MacAddress"
    Cookie = "mac=$MacAddress"
    'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    Referer = $referer
    Accept = 'application/json, text/javascript, */*; q=0.01'
    'X-Requested-With' = 'XMLHttpRequest'
}

function New-Result([string]$Transport) {
    return [ordered]@{
        transport = $Transport
        hostname = $target.hostname
        resolved_ip = $target.resolved_ip
        port = $target.port
        protocol = $target.protocol
        connection = 'failure'
        status = $null
        content_type = $null
        response_size = $null
        elapsed_seconds = $null
        redirect_count = $null
        server = $null
        allow = $null
        www_authenticate = $null
        exception_class = $null
        exception_message = $null
        tls = if ($target.protocol -eq 'https') { 'unknown' } else { 'not_applicable' }
    }
}

function Set-ResponseMetadata($Result, $Response, [double]$Started) {
    $Result.connection = 'success'
    $Result.status = [int]$Response.StatusCode
    $Result.content_type = if ($Response.Headers['Content-Type']) { ($Response.Headers['Content-Type'] -split ';')[0] } else { $null }
    $Result.response_size = if ($null -ne $Response.Content) { [Text.Encoding]::UTF8.GetByteCount([string]$Response.Content) } else { 0 }
    $Result.elapsed_seconds = [Math]::Round(((Get-Date) - $Started).TotalSeconds, 3)
    $Result.redirect_count = 0
    $Result.server = $Response.Headers['Server']
    $Result.allow = $Response.Headers['Allow']
    $Result.www_authenticate = $null -ne $Response.Headers['WWW-Authenticate']
}

function Invoke-PowerShellProbe {
    $result = New-Result 'powershell_invoke_webrequest'
    $started = Get-Date
    try {
        $response = Invoke-WebRequest -Uri $endpoint -Headers $headers -Method Get -TimeoutSec $TimeoutSeconds -MaximumRedirection 0 -UseBasicParsing
        Set-ResponseMetadata $result $response $started
    } catch {
        $result.elapsed_seconds = [Math]::Round(((Get-Date) - $started).TotalSeconds, 3)
        $result.exception_class = $_.Exception.GetType().Name
        $result.exception_message = $_.Exception.Message.Substring(0, [Math]::Min(240, $_.Exception.Message.Length))
        if ($_.Exception.Response) {
            $response = $_.Exception.Response
            $result.status = [int]$response.StatusCode
            $result.connection = 'success'
            $result.server = $response.Headers['Server']
            $result.allow = $response.Headers['Allow']
            $result.www_authenticate = $null -ne $response.Headers['WWW-Authenticate']
        }
    }
    return $result
}

function Invoke-WinHttpProbe {
    $result = New-Result 'winhttp'
    $started = Get-Date
    try {
        $request = New-Object -ComObject WinHttp.WinHttpRequest.5.1
        $request.Open('GET', $endpoint, $false)
        $request.SetTimeouts($TimeoutSeconds * 1000, $TimeoutSeconds * 1000, $TimeoutSeconds * 1000, $TimeoutSeconds * 1000)
        foreach ($key in $headers.Keys) { $request.SetRequestHeader($key, $headers[$key]) }
        $request.Send()
        $result.connection = 'success'
        $result.status = [int]$request.Status
        $result.content_type = if ($request.GetResponseHeader('Content-Type')) { ($request.GetResponseHeader('Content-Type') -split ';')[0] } else { $null }
        $result.response_size = [Text.Encoding]::UTF8.GetByteCount([string]$request.ResponseText)
        $result.elapsed_seconds = [Math]::Round(((Get-Date) - $started).TotalSeconds, 3)
        $result.server = $request.GetResponseHeader('Server')
        $result.allow = $request.GetResponseHeader('Allow')
        $result.www_authenticate = [bool]$request.GetResponseHeader('WWW-Authenticate')
    } catch {
        $result.elapsed_seconds = [Math]::Round(((Get-Date) - $started).TotalSeconds, 3)
        $result.exception_class = $_.Exception.GetType().Name
        $result.exception_message = $_.Exception.Message.Substring(0, [Math]::Min(240, $_.Exception.Message.Length))
    }
    return $result
}

function Invoke-RawTcpProbe {
    $result = New-Result 'raw_tcp'
    $started = Get-Date
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $connectTask = $client.ConnectAsync($target.hostname, $target.port)
        if (-not $connectTask.Wait($TimeoutSeconds * 1000)) { throw [TimeoutException]::new('TCP connect timeout') }
        $stream = $client.GetStream()
        $stream.ReadTimeout = $TimeoutSeconds * 1000
        $stream.WriteTimeout = $TimeoutSeconds * 1000
        $rawRequest = "GET /portal.php?$query HTTP/1.1`r`nHost: $($target.hostname)`r`nAuthorization: MAC $MacAddress`r`nCookie: mac=$MacAddress`r`nUser-Agent: $($headers['User-Agent'])`r`nReferer: $referer`r`nAccept: $($headers['Accept'])`r`nX-Requested-With: XMLHttpRequest`r`nConnection: close`r`n`r`n"
        $bytes = [Text.Encoding]::ASCII.GetBytes($rawRequest)
        $stream.Write($bytes, 0, $bytes.Length)
        $buffer = New-Object byte[] 65536
        $count = $stream.Read($buffer, 0, $buffer.Length)
        $text = [Text.Encoding]::ASCII.GetString($buffer, 0, $count)
        $headerEnd = $text.IndexOf("`r`n`r`n")
        $headerText = if ($headerEnd -ge 0) { $text.Substring(0, $headerEnd) } else { $text }
        $lines = $headerText -split "`r`n"
        if ($lines.Count -gt 0 -and $lines[0] -match '^HTTP/\d(?:\.\d)?\s+(\d+)') { $result.status = [int]$Matches[1]; $result.connection = 'success' }
        foreach ($line in $lines | Select-Object -Skip 1) {
            if ($line -match '^([^:]+):\s*(.*)$') {
                switch ($Matches[1].ToLowerInvariant()) {
                    'content-type' { $result.content_type = ($Matches[2] -split ';')[0] }
                    'server' { $result.server = $Matches[2] }
                    'allow' { $result.allow = $Matches[2] }
                    'www-authenticate' { $result.www_authenticate = $true }
                }
            }
        }
        $result.response_size = [Math]::Max(0, $count - [Math]::Max(0, $headerEnd + 4))
        $result.elapsed_seconds = [Math]::Round(((Get-Date) - $started).TotalSeconds, 3)
    } catch {
        $result.elapsed_seconds = [Math]::Round(((Get-Date) - $started).TotalSeconds, 3)
        $result.exception_class = $_.Exception.GetType().Name
        $result.exception_message = $_.Exception.Message.Substring(0, [Math]::Min(240, $_.Exception.Message.Length))
    } finally {
        $client.Dispose()
    }
    return $result
}

$results = @(
    (Invoke-PowerShellProbe),
    (Invoke-WinHttpProbe),
    (Invoke-RawTcpProbe)
)

$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if ($curl) {
    $results += [ordered]@{ transport = 'curl.exe'; hostname = $target.hostname; resolved_ip = $target.resolved_ip; port = $target.port; protocol = $target.protocol; connection = 'run-separately'; status = $null; content_type = $null; response_size = $null; elapsed_seconds = $null; redirect_count = $null; server = $null; allow = $null; www_authenticate = $null; exception_class = $null; exception_message = 'Run curl.exe with the same endpoint and headers; do not print body or command line'; tls = 'not_applicable' }
} else {
    $results += [ordered]@{ transport = 'curl.exe'; hostname = $target.hostname; resolved_ip = $target.resolved_ip; port = $target.port; protocol = $target.protocol; connection = 'unavailable'; status = $null; content_type = $null; response_size = $null; elapsed_seconds = $null; redirect_count = $null; server = $null; allow = $null; www_authenticate = $null; exception_class = 'Unavailable'; exception_message = 'curl.exe not found'; tls = 'not_applicable' }
}

[ordered]@{ target = $target; results = $results } | ConvertTo-Json -Depth 5 -Compress
