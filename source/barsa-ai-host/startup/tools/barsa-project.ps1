param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("systems", "init", "status", "pull", "plan", "apply", "apply-status", "handoff", "pack", "run-package")]
    [string]$Command,

    [string]$Project,
    [string]$Name,
    [string]$SystemIds,
    [string]$Query,
    [string]$ChangeFile,
    [string]$PackageFile,
    [string]$OutputFile,
    [string]$PlanId,
    [string]$ProjectsRoot,
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

function Read-HttpErrorBody($Exception) {
    $response = $null
    if ($Exception.PSObject.Properties.Name -contains "Response") {
        $response = $Exception.Response
    }
    if ($null -eq $response) { return $null }

    try {
        $stream = $response.GetResponseStream()
        if ($null -eq $stream) { return $null }
        $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
        try { return $reader.ReadToEnd() }
        finally { $reader.Dispose(); $stream.Dispose() }
    }
    catch { return $null }
}

function Invoke-BarsaPost([string]$Path, [string]$Json, [bool]$AllowStructuredError = $false) {
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Json)
        return Invoke-RestMethod -Method Post -Uri ($BaseUrl.TrimEnd('/') + $Path) `
            -Headers (Get-Headers) -ContentType "application/json; charset=utf-8" -Body $bytes
    }
    catch {
        $body = Read-HttpErrorBody $_.Exception
        if ($AllowStructuredError -and -not [string]::IsNullOrWhiteSpace($body)) {
            try { return $body | ConvertFrom-Json }
            catch { }
        }
        throw
    }
}


function ConvertTo-SafePathSegment([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "Path segment cannot be empty." }
    $invalid = [System.IO.Path]::GetInvalidFileNameChars()
    $chars = $Value.Trim().ToCharArray() | ForEach-Object {
        if ($invalid -contains $_) { '_' } else { $_ }
    }
    $safe = (-join $chars).Trim([char[]]@(' ', '.'))
    if ([string]::IsNullOrWhiteSpace($safe)) { throw "Path segment became empty after sanitization: $Value" }
    return $safe
}

function Get-HostIdentity {
    $health = Invoke-BarsaGet "/health"
    if ($health.status -ne "ready") { throw "Host is not ready." }
    if ([string]::IsNullOrWhiteSpace([string]$health.connectionKey)) {
        throw "Host /health did not return connectionKey."
    }
    return $health
}


function Get-ProjectsRoot {
    if (-not [string]::IsNullOrWhiteSpace($ProjectsRoot)) {
        return [System.IO.Path]::GetFullPath($ProjectsRoot)
    }
    $health = Get-HostIdentity
    if (-not [string]::IsNullOrWhiteSpace([string]$health.projectsRoot)) {
        return [System.IO.Path]::GetFullPath([string]$health.projectsRoot)
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$health.workspaceRoot)) {
        return [System.IO.Path]::GetFullPath((Join-Path ([string]$health.workspaceRoot) "projects"))
    }
    throw "Host /health did not return projectsRoot/workspaceRoot."
}

function Write-Utf8Json([string]$Path, $Object) {
    $json = $Object | ConvertTo-Json -Depth 100
    [System.IO.File]::WriteAllText($Path, $json, (New-Object System.Text.UTF8Encoding($true)))
}

function Resolve-ProjectPath {
    if (-not [string]::IsNullOrWhiteSpace($Project)) {
        return [System.IO.Path]::GetFullPath($Project)
    }

    # One persistent workspace per Runtime database. -Name is accepted only for
    # backward compatibility and never creates another directory level.
    $health = Get-HostIdentity
    $connectionKey = ConvertTo-SafePathSegment ([string]$health.connectionKey)
    return [System.IO.Path]::GetFullPath((Join-Path (Get-ProjectsRoot) $connectionKey))
}

function Read-Project([string]$ProjectPath) {
    $file = Join-Path $ProjectPath "project.json"
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "project.json not found: $file" }
    return [System.IO.File]::ReadAllText($file, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
}

function Save-Project([string]$ProjectPath, $ProjectObject) {
    Write-Utf8Json (Join-Path $ProjectPath "project.json") $ProjectObject
}

function Ensure-ProjectFolders([string]$ProjectPath) {
    @("systems", "changes", "plans", "results", ".barsa") | ForEach-Object {
        [System.IO.Directory]::CreateDirectory((Join-Path $ProjectPath $_)) | Out-Null
    }
}


function Normalize-BarsaLookupText([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return $Value }
    $normalized = $Value.Replace([char]0x064A, [char]0x06CC).Replace([char]0x0649, [char]0x06CC).Replace([char]0x0643, [char]0x06A9)
    $normalized = [System.Text.RegularExpressions.Regex]::Replace($normalized.Trim(), "\s+", " ")
    return $normalized
}

function Test-ContainsIgnoreCase([string]$Value, [string]$Needle) {
    if ([string]::IsNullOrWhiteSpace($Value) -or [string]::IsNullOrWhiteSpace($Needle)) { return $false }
    $normalizedValue = Normalize-BarsaLookupText $Value
    $normalizedNeedle = Normalize-BarsaLookupText $Needle
    return $normalizedValue.IndexOf($normalizedNeedle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
}

function Get-SystemMap {
    $response = Invoke-BarsaGet "/systems"
    $map = @{}
    foreach ($system in @($response.systems)) {
        $map[[string]$system.id] = $system
    }
    return $map
}

function Parse-SystemIds([string]$Text) {
    if ([string]::IsNullOrWhiteSpace($Text)) { throw "-SystemIds is required (comma-separated runtime ids)." }
    $result = @()
    foreach ($part in $Text.Split(',')) {
        $value = [Int64]0
        if (-not [Int64]::TryParse($part.Trim(), [ref]$value) -or $value -le 0) {
            throw "Invalid system id: $part"
        }
        if ($result -notcontains $value) { $result += $value }
    }
    return $result
}

function Pull-SystemIntoProject([string]$ProjectPath, [Int64]$SystemId, $SystemMap, $ProjectObject) {
    $systemIdKey = [string]$SystemId
    if (-not $SystemMap.ContainsKey($systemIdKey)) { throw "System not found in Host discovery: $SystemId" }
    $system = $SystemMap[$systemIdKey]
    if ([string]::IsNullOrWhiteSpace([string]$system.name)) { throw "System has no unique name: $SystemId" }
    $systemKey = ConvertTo-SafePathSegment ([string]$system.name)

    $request = @{ systemIds = @($SystemId) } | ConvertTo-Json -Compress
    $pull = Invoke-BarsaPost "/pull" $request
    if ($pull.status -ne "succeeded") { throw "Host pull failed for system $SystemId." }
    if (-not (Test-Path -LiteralPath $pull.exportFile -PathType Leaf)) {
        throw "Host export file not found: $($pull.exportFile)"
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $systemsRoot = Join-Path $ProjectPath "systems"
    $target = Join-Path $systemsRoot $systemKey
    $temp = Join-Path $systemsRoot (".pull-" + $systemKey + "-" + [Guid]::NewGuid().ToString("N"))
    [System.IO.Directory]::CreateDirectory($temp) | Out-Null
    try {
        [System.IO.Compression.ZipFile]::ExtractToDirectory([string]$pull.exportFile, $temp)

        # A selected-system Export v13 contains export-level files (for example manifest.json)
        # plus the actual System root directory. The project workspace stores the System root
        # directly as systems/<System.Name>; export-level wrappers are not copied into it.
        $allowedRootNames = @($systemKey)
        if (-not [string]::IsNullOrWhiteSpace([string]$system.caption)) {
            $captionKey = ConvertTo-SafePathSegment ([string]$system.caption)
            if ($allowedRootNames -notcontains $captionKey) { $allowedRootNames += $captionKey }
        }

        $rootDirectories = @(Get-ChildItem -LiteralPath $temp -Directory -Force)
        $matchingRoots = @($rootDirectories | Where-Object { $allowedRootNames -contains $_.Name })
        if ($matchingRoots.Count -eq 1) {
            $contentRoot = $matchingRoots[0].FullName
        }
        elseif ($rootDirectories.Count -eq 1) {
            $contentRoot = $rootDirectories[0].FullName
        }
        else {
            throw "Could not identify the System root inside export: $($pull.exportFile)"
        }

        # Remove any additional repeated System wrapper directories, but do not flatten
        # meaningful folders such as [موجوديت].
        while ($true) {
            $files = @(Get-ChildItem -LiteralPath $contentRoot -File -Force)
            $dirs = @(Get-ChildItem -LiteralPath $contentRoot -Directory -Force)
            if ($files.Count -ne 0 -or $dirs.Count -ne 1 -or $allowedRootNames -notcontains $dirs[0].Name) { break }
            $contentRoot = $dirs[0].FullName
        }

        if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
        [System.IO.Directory]::Move($contentRoot, $target)
    }
    finally {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
    }

    $entries = @()
    foreach ($entry in @($ProjectObject.systems)) {
        if ([Int64]$entry.id -ne $SystemId) { $entries += $entry }
    }
    $entries += [pscustomobject][ordered]@{
        id = $SystemId
        name = [string]$system.name
        caption = [string]$system.caption
        pulledAt = [DateTime]::UtcNow.ToString("o")
        exportVersion = 10
        path = "systems/$systemKey"
    }
    $ProjectObject.systems = $entries
    Save-Project $ProjectPath $ProjectObject

    return [pscustomobject][ordered]@{
        systemId = $SystemId
        name = [string]$system.name
        caption = [string]$system.caption
        workspacePath = $target
        exportFile = [string]$pull.exportFile
        status = "succeeded"
    }
}


function Get-FileSha256([string]$Path) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $stream = [System.IO.File]::OpenRead($Path)
        try {
            $hash = $sha.ComputeHash($stream)
            return ([BitConverter]::ToString($hash)).Replace("-", "").ToLowerInvariant()
        }
        finally { $stream.Dispose() }
    }
    finally { $sha.Dispose() }
}

function Get-BytesSha256([byte[]]$Bytes) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hash = $sha.ComputeHash($Bytes)
        return ([BitConverter]::ToString($hash)).Replace("-", "").ToLowerInvariant()
    }
    finally { $sha.Dispose() }
}

function Open-ZipRead([string]$Path) {
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        $zip = New-Object System.IO.Compression.ZipArchive($stream, [System.IO.Compression.ZipArchiveMode]::Read, $false)
        return [pscustomobject]@{ Stream = $stream; Zip = $zip }
    }
    catch {
        $stream.Dispose()
        throw
    }
}

function Read-ZipEntryBytes($Zip, [string]$Name) {
    $entry = $Zip.GetEntry($Name)
    if ($null -eq $entry) { throw "Package entry not found: $Name" }
    $stream = $entry.Open()
    try {
        $memory = New-Object System.IO.MemoryStream
        try {
            $stream.CopyTo($memory)
            return $memory.ToArray()
        }
        finally { $memory.Dispose() }
    }
    finally { $stream.Dispose() }
}

function New-ZipFromDirectory([string]$SourceDirectory, [string]$DestinationFile) {
    Add-Type -AssemblyName System.IO.Compression
    if (Test-Path -LiteralPath $DestinationFile) { Remove-Item -LiteralPath $DestinationFile -Force }

    $root = [System.IO.Path]::GetFullPath($SourceDirectory)
    if (-not $root.EndsWith([System.IO.Path]::DirectorySeparatorChar.ToString(), [System.StringComparison]::Ordinal)) {
        $root += [System.IO.Path]::DirectorySeparatorChar
    }

    $stream = New-Object System.IO.FileStream($DestinationFile, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    try {
        $zip = New-Object System.IO.Compression.ZipArchive($stream, [System.IO.Compression.ZipArchiveMode]::Create, $false)
        try {
            foreach ($file in ([System.IO.Directory]::GetFiles($SourceDirectory, "*", [System.IO.SearchOption]::AllDirectories) | Sort-Object)) {
                $full = [System.IO.Path]::GetFullPath($file)
                if (-not $full.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) { throw "ZIP source escaped root: $full" }
                $entryName = $full.Substring($root.Length).Replace('\', '/')
                if ([string]::IsNullOrWhiteSpace($entryName) -or $entryName.Contains('\')) { throw "Invalid portable ZIP entry name: $entryName" }
                $entry = $zip.CreateEntry($entryName, [System.IO.Compression.CompressionLevel]::Optimal)
                $input = New-Object System.IO.FileStream($full, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
                try {
                    $output = $entry.Open()
                    try { $input.CopyTo($output) } finally { $output.Dispose() }
                }
                finally { $input.Dispose() }
            }
        }
        finally { $zip.Dispose() }
    }
    finally { $stream.Dispose() }
}

function Test-ChangeContainsDelete($ChangeObject) {
    foreach ($change in @($ChangeObject.changes)) {
        if ([string]$change.operation -eq "delete") { return $true }
    }
    return $false
}

function Read-BarsaChangePackage([string]$Path) {
    $full = [System.IO.Path]::GetFullPath($Path)
    $fileName = [System.IO.Path]::GetFileName($full)
    if (-not $fileName.EndsWith(".zip", [System.StringComparison]::OrdinalIgnoreCase) -or
        $fileName.IndexOf(".barsa-change", [System.StringComparison]::OrdinalIgnoreCase) -lt 0) {
        throw "User metadata package filename must contain .barsa-change and end with .zip."
    }
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw "Package file not found: $full" }

    $opened = Open-ZipRead $full
    try {
        $manifestBytes = Read-ZipEntryBytes $opened.Zip "barsa-change-manifest.json"
        $manifestJson = [System.Text.Encoding]::UTF8.GetString($manifestBytes)
        $manifest = $manifestJson | ConvertFrom-Json
        if ([string]$manifest.packageType -ne "barsa-system-change") { throw "Invalid metadata package type." }
        if ([int]$manifest.formatVersion -ne 1) { throw "Unsupported metadata package formatVersion." }
        if ([string]::IsNullOrWhiteSpace([string]$manifest.changeFile)) { throw "Package changeFile is required." }

        $changeBytes = Read-ZipEntryBytes $opened.Zip ([string]$manifest.changeFile)
        $actualHash = Get-BytesSha256 $changeBytes
        if ([string]::IsNullOrWhiteSpace([string]$manifest.changeSha256) -or
            -not $actualHash.Equals([string]$manifest.changeSha256, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Metadata package change SHA256 mismatch."
        }

        $changeJson = [System.Text.Encoding]::UTF8.GetString($changeBytes)
        $change = $changeJson | ConvertFrom-Json
        if ($null -eq $change -or $null -eq $change.changes) { throw "change.json must contain changes[]." }

        $health = Get-HostIdentity
        if ([string]::IsNullOrWhiteSpace([string]$manifest.connectionKey)) {
            throw "Metadata package connectionKey is required."
        }
        if (-not ([string]$manifest.connectionKey).Equals([string]$health.connectionKey, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Package belongs to a different Runtime database (connectionKey mismatch)."
        }

        return [pscustomobject]@{
            Path = $full
            Manifest = $manifest
            ChangeJson = $changeJson
            Change = $change
        }
    }
    finally {
        $opened.Zip.Dispose()
        $opened.Stream.Dispose()
    }
}

function Invoke-MetadataChangePackage([string]$Path) {
    $package = Read-BarsaChangePackage $Path
    if (Test-ChangeContainsDelete $package.Change) {
        throw "Automatic package execution does not apply delete operations. Run an explicitly reviewed Plan/Apply workflow for destructive metadata changes."
    }

    $projectPath = Resolve-ProjectPath
    Ensure-ProjectFolders $projectPath
    $projectObject = Read-Project $projectPath

    $packageStem = [System.IO.Path]::GetFileNameWithoutExtension($package.Path)
    $markerIndex = $packageStem.IndexOf(".barsa-change", [System.StringComparison]::OrdinalIgnoreCase)
    if ($markerIndex -ge 0) { $packageStem = $packageStem.Remove($markerIndex, ".barsa-change".Length) }
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss-fff")
    $runRoot = Join-Path (Join-Path $projectPath "results") ($packageStem + "-" + $stamp)
    [System.IO.Directory]::CreateDirectory($runRoot) | Out-Null

    $effectiveChange = $package.Change
    Expand-ReferencedPackageAssets $package.Path $effectiveChange $runRoot
    if ((Get-ReferencedAssets $effectiveChange).Count -gt 0) {
        $effectiveChange | Add-Member -NotePropertyName assetRoot -NotePropertyValue $runRoot -Force
    }
    $effectiveChangeJson = $effectiveChange | ConvertTo-Json -Depth 100
    $changeFile = Join-Path $runRoot "change.json"
    [System.IO.File]::WriteAllText($changeFile, $effectiveChangeJson, (New-Object System.Text.UTF8Encoding($true)))

    $plan = Invoke-BarsaPost "/plan" $effectiveChangeJson $true
    Write-Utf8Json (Join-Path $runRoot "plan.json") $plan

    if (-not [bool]$plan.isValid -or -not [bool]$plan.summary.canApplyAny) {
        $summary = [pscustomobject][ordered]@{
            status = "invalid"
            package = $package.Path
            planId = $plan.planId
            applied = $false
            resultPackage = $null
        }
        Write-Utf8Json (Join-Path $runRoot "summary.json") $summary
        return $summary
    }

    if ($package.Manifest.PSObject.Properties.Name -contains "autoApply" -and -not [bool]$package.Manifest.autoApply) {
        $summary = [pscustomobject][ordered]@{
            status = "planned"
            package = $package.Path
            planId = $plan.planId
            applied = $false
            resultPackage = $null
        }
        Write-Utf8Json (Join-Path $runRoot "summary.json") $summary
        return $summary
    }

    $applyJson = @{ planId = [string]$plan.planId } | ConvertTo-Json -Compress
    $applyResult = Invoke-BarsaPost "/apply" $applyJson $true
    Write-Utf8Json (Join-Path $runRoot "apply-result.json") $applyResult

    $refresh = @()
    if ($applyResult.status -eq "succeeded" -or $applyResult.status -eq "partiallySucceeded") {
        $systemMap = Get-SystemMap
        $affectedIds = @($applyResult.affectedSystemIds | Where-Object { [Int64]$_ -gt 0 } | Select-Object -Unique)
        $finalRoot = Join-Path $runRoot "systems"
        [System.IO.Directory]::CreateDirectory($finalRoot) | Out-Null
        foreach ($systemId in $affectedIds) {
            try {
                $pulled = Pull-SystemIntoProject $projectPath ([Int64]$systemId) $systemMap $projectObject
                $refresh += $pulled
                if (Test-Path -LiteralPath $pulled.workspacePath) {
                    $target = Join-Path $finalRoot (Split-Path -Leaf $pulled.workspacePath)
                    Copy-Item -LiteralPath $pulled.workspacePath -Destination $target -Recurse -Force
                }
            }
            catch {
                $refresh += [pscustomobject][ordered]@{ systemId = [Int64]$systemId; status = "failed"; error = $_.Exception.Message }
            }
        }
    }

    $resultPackage = Join-Path (Split-Path -Parent $package.Path) ($packageStem + ".barsa-result.zip")
    $summary = [pscustomobject][ordered]@{
        status = [string]$applyResult.status
        package = $package.Path
        planId = [string]$plan.planId
        applied = $true
        mutationApplied = $applyResult.mutationApplied
        verificationSucceeded = $applyResult.verificationSucceeded
        affectedSystemIds = @($applyResult.affectedSystemIds)
        refresh = $refresh
        resultPackage = $resultPackage
    }
    Write-Utf8Json (Join-Path $runRoot "summary.json") $summary
    New-ZipFromDirectory $runRoot $resultPackage
    return $summary
}

function Assert-SemanticV15PackageNode($Node, [string]$Path, [hashtable]$DeclaredTempIds, [bool]$IsChangeRoot) {
    if ($null -eq $Node -or $Node -is [string] -or $Node -is [ValueType]) { return }
    if ($Node -is [System.Collections.IEnumerable] -and -not ($Node -is [System.Management.Automation.PSCustomObject])) {
        $i = 0
        foreach ($child in $Node) { Assert-SemanticV15PackageNode $child ($Path + '[' + $i + ']') $DeclaredTempIds $false; $i++ }
        return
    }
    foreach ($property in $Node.PSObject.Properties) {
        if (@('id','rowId','sourceId','runtimeId','dependencyKey') -contains [string]$property.Name) {
            throw "Semantic v15 package contains forbidden Runtime authority at $Path.$($property.Name)."
        }
        if (-not $IsChangeRoot -and [string]$property.Name -ieq 'tempId' -and -not [string]::IsNullOrWhiteSpace([string]$property.Value)) {
            $tempId = [string]$property.Value
            if (-not $DeclaredTempIds.ContainsKey($tempId)) { throw "Semantic v15 package references undeclared/cross-wave tempId at $Path.tempId: $tempId" }
        }
        Assert-SemanticV15PackageNode $property.Value ($Path + '.' + [string]$property.Name) $DeclaredTempIds $false
    }
}

function Assert-SemanticV15ChangeForPackage($ChangeObject) {
    if ($null -eq $ChangeObject) { throw 'Change JSON is null.' }
    if ([int]$ChangeObject.profileVersion -ne 15) { throw 'pack accepts only explicit profileVersion=15.' }
    if ($null -eq $ChangeObject.changes) { throw 'Change file must contain changes[].' }
    $declared = @{}
    foreach ($change in @($ChangeObject.changes)) {
        if ($null -eq $change) { throw 'changes[] cannot contain null.' }
        $tempId = [string]$change.tempId
        if (-not [string]::IsNullOrWhiteSpace($tempId)) {
            if (-not ([string]$change.operation).Equals('create', [System.StringComparison]::OrdinalIgnoreCase)) { throw "tempId can only be declared by create commands: $tempId" }
            if ($declared.ContainsKey($tempId)) { throw "Duplicate tempId declaration: $tempId" }
            $declared[$tempId] = $true
        }
    }
    $index = 0
    foreach ($change in @($ChangeObject.changes)) { Assert-SemanticV15PackageNode $change ("changes[$index]") $declared $true; $index++ }
}

function Test-SafeReferencedAssetPath([string]$LogicalPath) {
    if ([string]::IsNullOrWhiteSpace($LogicalPath)) { return $false }
    $normalized = $LogicalPath.Replace('\', '/')
    if (-not $normalized.StartsWith('assets/', [System.StringComparison]::OrdinalIgnoreCase)) { return $false }
    if ([System.IO.Path]::IsPathRooted($LogicalPath) -or $normalized.StartsWith('/')) { return $false }
    foreach ($segment in $normalized.Split('/')) {
        if ([string]::IsNullOrWhiteSpace($segment) -or $segment -eq '.' -or $segment -eq '..') { return $false }
        if ($segment.Length -ge 2 -and [char]::IsLetter($segment[0]) -and $segment[1] -eq ':') { return $false }
    }
    return $true
}

function Add-ReferencedAssetsFromNode($Node, [hashtable]$Found) {
    if ($null -eq $Node -or $Node -is [string] -or $Node -is [ValueType]) { return }
    if ($Node -is [System.Collections.IEnumerable] -and -not ($Node -is [System.Management.Automation.PSCustomObject])) {
        foreach ($child in $Node) { Add-ReferencedAssetsFromNode $child $Found }
        return
    }
    $names = @($Node.PSObject.Properties.Name)
    if (($names -contains 'asset') -or ($names -contains 'sha256')) {
        if (-not (($names -contains 'asset') -and ($names -contains 'sha256'))) { throw 'Portable asset reference requires asset and sha256.' }
        $logical = ([string]$Node.asset).Replace('\', '/')
        $expected = ([string]$Node.sha256).Trim().ToLowerInvariant()
        if (-not (Test-SafeReferencedAssetPath $logical)) { throw "Unsafe portable asset path: $logical" }
        if ($expected -notmatch '^[0-9a-f]{64}$') { throw "Invalid portable asset sha256: $logical" }
        if ($Found.ContainsKey($logical)) {
            if (-not ([string]$Found[$logical]).Equals($expected, [System.StringComparison]::OrdinalIgnoreCase)) {
                throw "Conflicting sha256 values for referenced asset: $logical"
            }
        } else { $Found[$logical] = $expected }
        return
    }
    foreach ($property in $Node.PSObject.Properties) { Add-ReferencedAssetsFromNode $property.Value $Found }
}

function Get-ReferencedAssets($ChangeObject) {
    $found = @{}
    Add-ReferencedAssetsFromNode $ChangeObject $found
    return $found
}

function Copy-ReferencedAssetsForPackage($ChangeObject, [string]$ChangePath, [string]$PackageRoot) {
    $references = Get-ReferencedAssets $ChangeObject
    $sourceRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $ChangePath)).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    foreach ($logical in @($references.Keys | Sort-Object)) {
        $source = [System.IO.Path]::GetFullPath((Join-Path $sourceRoot ($logical.Replace('/', [System.IO.Path]::DirectorySeparatorChar))))
        if (-not $source.StartsWith($sourceRoot, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Asset path escaped change directory: $logical" }
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Referenced asset not found: $logical" }
        $actual = Get-FileSha256 $source
        if (-not $actual.Equals([string]$references[$logical], [System.StringComparison]::OrdinalIgnoreCase)) { throw "Referenced asset SHA256 mismatch: $logical" }
        $target = Join-Path $PackageRoot ($logical.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
        [System.IO.Directory]::CreateDirectory((Split-Path -Parent $target)) | Out-Null
        Copy-Item -LiteralPath $source -Destination $target -Force
    }
    return $references
}

function Expand-ReferencedPackageAssets([string]$PackagePath, $ChangeObject, [string]$ExecutionRoot) {
    $references = Get-ReferencedAssets $ChangeObject
    if ($references.Count -eq 0) { return }
    $opened = Open-ZipRead $PackagePath
    try {
        foreach ($logical in @($references.Keys | Sort-Object)) {
            $bytes = Read-ZipEntryBytes $opened.Zip $logical
            $actual = Get-BytesSha256 $bytes
            if (-not $actual.Equals([string]$references[$logical], [System.StringComparison]::OrdinalIgnoreCase)) { throw "Packaged asset SHA256 mismatch: $logical" }
            $target = Join-Path $ExecutionRoot ($logical.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
            [System.IO.Directory]::CreateDirectory((Split-Path -Parent $target)) | Out-Null
            [System.IO.File]::WriteAllBytes($target, $bytes)
        }
    }
    finally { $opened.Zip.Dispose(); $opened.Stream.Dispose() }
}

function New-MetadataChangePackage([string]$ChangePath, [string]$Destination) {
    $source = [System.IO.Path]::GetFullPath($ChangePath)
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Change file not found: $source" }
    $changeJson = [System.IO.File]::ReadAllText($source, [System.Text.Encoding]::UTF8)
    # Pre-ZIP semantic/package lint is centralized in the Runtime so selector grammar is validated
    # by the same SemanticSelectorCodec used by Plan/Apply/Verify. No parallel PowerShell parser.
    Invoke-BarsaPost "/lint" $changeJson | Out-Null
    $changeObject = $changeJson | ConvertFrom-Json
    Assert-SemanticV15ChangeForPackage $changeObject
    if (Test-ChangeContainsDelete $changeObject) { throw "pack does not create auto-apply packages containing delete." }
    if ($changeObject.PSObject.Properties.Name -contains 'assetRoot') { throw 'assetRoot is an execution detail and must not be authored in a Semantic v15 change package.' }

    $health = Get-HostIdentity
    $temp = Join-Path ([System.IO.Path]::GetTempPath()) ("barsa-change-" + [Guid]::NewGuid().ToString("N"))
    [System.IO.Directory]::CreateDirectory($temp) | Out-Null
    try {
        $changeTarget = Join-Path $temp "change.json"
        Write-Utf8Json $changeTarget $changeObject
        Copy-ReferencedAssetsForPackage $changeObject $source $temp | Out-Null
        $manifest = [pscustomobject][ordered]@{
            packageType = "barsa-system-change"
            formatVersion = 1
            connectionKey = [string]$health.connectionKey
            createdAt = [DateTime]::UtcNow.ToString("o")
            changeFile = "change.json"
            changeSha256 = Get-FileSha256 $changeTarget
            autoApply = $true
        }
        Write-Utf8Json (Join-Path $temp "barsa-change-manifest.json") $manifest
        New-ZipFromDirectory $temp $Destination
    }
    finally {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
    }
}


try {
    switch ($Command) {
        "handoff" {
            $result = [pscustomobject][ordered]@{
                status = "deprecated"
                packageType = "barsa-handoff"
                replacement = "Use the Host-generated <EID>-START-HERE.en.md + <EID>-upload-ai-gen.zip pair in Package Mode."
                generatedArtifact = $null
            }
        }
        "pack" {
            if ([string]::IsNullOrWhiteSpace($ChangeFile)) { throw "pack requires -ChangeFile." }
            $destination = $OutputFile
            if ([string]::IsNullOrWhiteSpace($destination)) {
                $stem = [System.IO.Path]::GetFileNameWithoutExtension($ChangeFile)
                $destination = Join-Path (Split-Path -Parent ([System.IO.Path]::GetFullPath($ChangeFile))) ($stem + ".barsa-change.zip")
            }
            if (-not $destination.EndsWith(".barsa-change.zip", [System.StringComparison]::OrdinalIgnoreCase)) {
                $destination += ".barsa-change.zip"
            }
            New-MetadataChangePackage $ChangeFile ([System.IO.Path]::GetFullPath($destination))
            $result = [pscustomobject][ordered]@{ status = "succeeded"; packageType = "barsa-system-change"; file = [System.IO.Path]::GetFullPath($destination) }
        }
        "run-package" {
            if ([string]::IsNullOrWhiteSpace($PackageFile)) { throw "run-package requires -PackageFile." }
            $result = Invoke-MetadataChangePackage $PackageFile
        }
        "systems" {
            $response = Invoke-BarsaGet "/systems"
            if ([string]::IsNullOrWhiteSpace($Query)) {
                $result = $response
            }
            else {
                $items = @($response.systems | Where-Object {
                    (Test-ContainsIgnoreCase ([string]$_.name) $Query) -or
                    (Test-ContainsIgnoreCase ([string]$_.caption) $Query)
                })
                $result = [pscustomobject][ordered]@{
                    status = "succeeded"
                    query = $Query
                    count = $items.Count
                    systems = $items
                }
            }
        }
        "init" {
            $health = Get-HostIdentity
            $projectsRoot = Get-ProjectsRoot
            [System.IO.Directory]::CreateDirectory($projectsRoot) | Out-Null
            $connectionKey = ConvertTo-SafePathSegment ([string]$health.connectionKey)
            $projectPath = [System.IO.Path]::GetFullPath((Join-Path $projectsRoot $connectionKey))
            [System.IO.Directory]::CreateDirectory($projectPath) | Out-Null
            Ensure-ProjectFolders $projectPath

            if (Test-Path -LiteralPath (Join-Path $projectPath "project.json")) {
                $projectObject = Read-Project $projectPath
                $result = [pscustomobject][ordered]@{ status = "succeeded"; reused = $true; projectPath = $projectPath; project = $projectObject }
                break
            }

            $projectObject = [pscustomobject][ordered]@{
                projectVersion = 1
                name = $connectionKey
                host = $BaseUrl.TrimEnd('/')
                connectionKey = $connectionKey
                runtime = [pscustomobject][ordered]@{
                    server = [string]$health.database.server
                    instance = [string]$health.database.instance
                    database = [string]$health.database.name
                }
                createdAt = [DateTime]::UtcNow.ToString("o")
                systems = @()
            }
            Save-Project $projectPath $projectObject
            $result = [pscustomobject][ordered]@{ status = "succeeded"; reused = $false; projectPath = $projectPath; project = $projectObject }
        }
        "status" {
            $projectPath = Resolve-ProjectPath
            $projectObject = Read-Project $projectPath
            $result = [pscustomobject][ordered]@{ status = "succeeded"; projectPath = $projectPath; project = $projectObject }
        }
        "pull" {
            $projectPath = Resolve-ProjectPath
            Ensure-ProjectFolders $projectPath
            $projectObject = Read-Project $projectPath
            $ids = Parse-SystemIds $SystemIds
            $systemMap = Get-SystemMap
            $items = @()
            foreach ($id in $ids) {
                $items += Pull-SystemIntoProject $projectPath $id $systemMap $projectObject
            }
            $result = [pscustomobject][ordered]@{ status = "succeeded"; projectPath = $projectPath; systems = $items }
        }
        "plan" {
            $projectPath = Resolve-ProjectPath
            Ensure-ProjectFolders $projectPath
            $projectObject = Read-Project $projectPath | Out-Null
            if ([string]::IsNullOrWhiteSpace($ChangeFile)) { throw "plan requires -ChangeFile." }
            $source = [System.IO.Path]::GetFullPath($ChangeFile)
            if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Change file not found: $source" }
            $changeJson = [System.IO.File]::ReadAllText($source, [System.Text.Encoding]::UTF8)
            $stem = [System.IO.Path]::GetFileNameWithoutExtension($source)
            $changeTarget = Join-Path (Join-Path $projectPath "changes") ($stem + ".json")
            [System.IO.File]::WriteAllText($changeTarget, $changeJson, (New-Object System.Text.UTF8Encoding($true)))

            $plan = Invoke-BarsaPost "/plan" $changeJson $true
            $planTarget = Join-Path (Join-Path $projectPath "plans") ($stem + ".json")
            Write-Utf8Json $planTarget $plan
            $result = [pscustomobject][ordered]@{
                status = $(if ($plan.isValid) { "succeeded" } else { "invalid" })
                projectPath = $projectPath
                changeFile = $changeTarget
                planFile = $planTarget
                summary = $plan.summary
                canApplyCleanly = [bool]$plan.summary.canApplyCleanly
                canApplyAny = [bool]$plan.summary.canApplyAny
                canApplyAll = [bool]$plan.summary.canApplyAll
                plan = $plan
            }
        }
        "apply-status" {
            $projectPath = Resolve-ProjectPath
            Ensure-ProjectFolders $projectPath
            $projectObject = Read-Project $projectPath
            if ([string]::IsNullOrWhiteSpace($PlanId)) { throw "apply-status requires -PlanId." }
            $escaped = [System.Uri]::EscapeDataString($PlanId)
            $statusResult = Invoke-BarsaGet ("/apply-status?planId=" + $escaped)

            $recoveredResultFile = $null
            $refresh = @()
            $hasResult = $statusResult.PSObject.Properties.Name -contains "result"
            if ([string]$statusResult.state -eq "applied" -and $hasResult -and $null -ne $statusResult.result) {
                $runtimeResult = $statusResult.result
                $recoveredResultFile = Join-Path (Join-Path $projectPath "results") ($PlanId + ".json")
                Write-Utf8Json $recoveredResultFile $runtimeResult

                if ($runtimeResult.status -eq "succeeded" -or $runtimeResult.status -eq "partiallySucceeded") {
                    $systemMap = Get-SystemMap
                    $affectedIds = @($runtimeResult.affectedSystemIds | Where-Object { [Int64]$_ -gt 0 } | Select-Object -Unique)
                    foreach ($systemId in $affectedIds) {
                        try {
                            $refresh += Pull-SystemIntoProject $projectPath ([Int64]$systemId) $systemMap $projectObject
                        }
                        catch {
                            $refresh += [pscustomobject][ordered]@{ systemId = [Int64]$systemId; status = "failed"; error = $_.Exception.Message }
                        }
                    }
                }
            }

            $result = [pscustomobject][ordered]@{
                status = "succeeded"
                projectPath = $projectPath
                applyStatus = $statusResult
                recoveredResultFile = $recoveredResultFile
                refresh = $refresh
            }
        }
        "apply" {
            $projectPath = Resolve-ProjectPath
            Ensure-ProjectFolders $projectPath
            $projectObject = Read-Project $projectPath
            if ([string]::IsNullOrWhiteSpace($PlanId)) { throw "apply requires -PlanId from an explicitly approved plan." }
            $applyJson = @{ planId = $PlanId } | ConvertTo-Json -Compress
            $applyResult = Invoke-BarsaPost "/apply" $applyJson $true
            $resultTarget = Join-Path (Join-Path $projectPath "results") ($PlanId + ".json")
            Write-Utf8Json $resultTarget $applyResult

            $refresh = @()
            if ($applyResult.status -eq "succeeded" -or $applyResult.status -eq "partiallySucceeded") {
                $systemMap = Get-SystemMap
                $affectedIds = @($applyResult.affectedSystemIds | Where-Object { [Int64]$_ -gt 0 } | Select-Object -Unique)
                foreach ($systemId in $affectedIds) {
                    try {
                        $refresh += Pull-SystemIntoProject $projectPath ([Int64]$systemId) $systemMap $projectObject
                    }
                    catch {
                        $refresh += [pscustomobject][ordered]@{ systemId = [Int64]$systemId; status = "failed"; error = $_.Exception.Message }
                    }
                }
            }

            $result = [pscustomobject][ordered]@{
                status = [string]$applyResult.status
                projectPath = $projectPath
                resultFile = $resultTarget
                runtimeResult = $applyResult
                refresh = $refresh
            }
        }
    }

    $result | ConvertTo-Json -Depth 100
}
catch {
    [pscustomobject][ordered]@{
        status = "clientFailed"
        command = $Command
        error = $_.Exception.Message
    } | ConvertTo-Json -Depth 100
    exit 1
}
