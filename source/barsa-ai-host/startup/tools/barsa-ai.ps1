param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("health", "systems", "pull", "pull-systems", "snapshot", "snapshot-systems", "snapshot-diff", "plan", "apply", "apply-status")]
    [string]$Command,

    [Parameter(Position = 1)]
    [string]$Value,

    [Parameter(Position = 2)]
    [string]$Value2,

    [string]$BaseUrl = "http://127.0.0.1:17840",
    [string]$ApiKey
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = $utf8NoBom

if ($Host.Name -eq "ConsoleHost") {
    try {
        [Console]::OutputEncoding = $utf8NoBom
    }
    catch {
        # Some redirected/non-standard console hosts do not expose a valid console handle.
    }
}

function Get-Headers {
    $headers = @{}
    if (-not [string]::IsNullOrWhiteSpace($ApiKey)) {
        $headers["X-Barsa-Ai-Key"] = $ApiKey
    }
    return $headers
}

function Invoke-BarsaGet([string]$Path) {
    return Invoke-RestMethod -Method Get -Uri ($BaseUrl.TrimEnd('/') + $Path) -Headers (Get-Headers)
}

function Invoke-BarsaPost([string]$Path, [string]$Json) {
    # Keep byte[] construction inside this scope. Returning byte[] from a PowerShell
    # function enumerates it through the pipeline and can turn it into Object[].
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Json)
    return Invoke-RestMethod -Method Post -Uri ($BaseUrl.TrimEnd('/') + $Path) `
        -Headers (Get-Headers) `
        -ContentType "application/json; charset=utf-8" `
        -Body $bytes
}

try {
    switch ($Command) {
        "health" {
            $result = Invoke-BarsaGet "/health"
        }
        "systems" {
            $result = Invoke-BarsaGet "/systems"
        }
        "pull" {
            if ([string]::IsNullOrWhiteSpace($Value)) {
                $json = "{}"
            }
            else {
                $json = @{ selectionFile = $Value } | ConvertTo-Json -Compress
            }
            $result = Invoke-BarsaPost "/pull" $json
        }
        "pull-systems" {
            if ([string]::IsNullOrWhiteSpace($Value)) {
                throw "pull-systems requires comma-separated system ids."
            }
            $ids = @()
            foreach ($part in $Value.Split(',')) {
                $id = [Int64]0
                if (-not [Int64]::TryParse($part.Trim(), [ref]$id) -or $id -le 0) {
                    throw "Invalid system id: $part"
                }
                if ($ids -notcontains $id) { $ids += $id }
            }
            $json = @{ systemIds = $ids } | ConvertTo-Json -Compress
            $result = Invoke-BarsaPost "/pull" $json
        }
        "snapshot" {
            if ([string]::IsNullOrWhiteSpace($Value)) {
                $json = "{}"
            }
            else {
                $json = @{ selectionFile = $Value } | ConvertTo-Json -Compress
            }
            $result = Invoke-BarsaPost "/snapshot" $json
        }
        "snapshot-systems" {
            if ([string]::IsNullOrWhiteSpace($Value)) {
                throw "snapshot-systems requires comma-separated system ids."
            }
            $ids = @()
            foreach ($part in $Value.Split(',')) {
                $id = [Int64]0
                if (-not [Int64]::TryParse($part.Trim(), [ref]$id) -or $id -le 0) {
                    throw "Invalid system id: $part"
                }
                if ($ids -notcontains $id) { $ids += $id }
            }
            $json = @{ systemIds = $ids } | ConvertTo-Json -Compress
            $result = Invoke-BarsaPost "/snapshot" $json
        }
        "snapshot-diff" {
            if ([string]::IsNullOrWhiteSpace($Value) -or [string]::IsNullOrWhiteSpace($Value2)) {
                throw "snapshot-diff requires before snapshot path and after snapshot path."
            }
            $json = @{ beforeFile = $Value; afterFile = $Value2 } | ConvertTo-Json -Compress
            $result = Invoke-BarsaPost "/snapshot-diff" $json
        }
        "plan" {
            if ([string]::IsNullOrWhiteSpace($Value)) {
                throw "plan requires the path to an AiChangeBatch JSON file."
            }
            $changeFile = [System.IO.Path]::GetFullPath($Value)
            if (-not (Test-Path -LiteralPath $changeFile -PathType Leaf)) {
                throw "Change file not found: $changeFile"
            }
            # Read exact JSON as UTF-8; the Host owns validation and planning.
            $json = [System.IO.File]::ReadAllText($changeFile, [System.Text.Encoding]::UTF8)
            $result = Invoke-BarsaPost "/plan" $json
        }
        "apply" {
            if ([string]::IsNullOrWhiteSpace($Value)) {
                throw "apply requires a planId produced by the currently running Barsa.Ai.Host process."
            }
            $json = @{ planId = $Value } | ConvertTo-Json -Compress
            $result = Invoke-BarsaPost "/apply" $json
        }
        "apply-status" {
            if ([string]::IsNullOrWhiteSpace($Value)) {
                throw "apply-status requires a planId."
            }
            $escaped = [System.Uri]::EscapeDataString($Value)
            $result = Invoke-BarsaGet ("/apply-status?planId=" + $escaped)
        }
    }

    # stdout is always structured JSON for Codex/automation consumption.
    $result | ConvertTo-Json -Depth 100
}
catch {
    $errorObject = [ordered]@{
        status = "clientFailed"
        command = $Command
        error = $_.Exception.Message
    }

    # Windows PowerShell exposes the HTTP response on WebException.Response.
    $response = $null
    if ($_.Exception.PSObject.Properties.Name -contains "Response") {
        $response = $_.Exception.Response
    }
    if ($null -ne $response) {
        try {
            $stream = $response.GetResponseStream()
            if ($null -ne $stream) {
                $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
                try {
                    $body = $reader.ReadToEnd()
                    if (-not [string]::IsNullOrWhiteSpace($body)) {
                        try {
                            $errorObject["hostResponse"] = $body | ConvertFrom-Json
                        }
                        catch {
                            $errorObject["hostResponse"] = $body
                        }
                    }
                }
                finally {
                    $reader.Dispose()
                    $stream.Dispose()
                }
            }
        }
        catch { }
    }

    $errorObject | ConvertTo-Json -Depth 100
    exit 1
}
