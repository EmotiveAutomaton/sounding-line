param(
    [Parameter(Mandatory)][string]$Source,
    [Parameter(Mandatory)][string]$Signal,
    [Parameter(Mandatory)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ReviewedDigest,
    [switch]$Once
)
$ErrorActionPreference = 'Stop'
$lock = [IO.File]::Open($Signal + '.lock', 'OpenOrCreate', 'ReadWrite', 'None')
try {
    $last = $ReviewedDigest
    if ([IO.File]::Exists($Signal)) {
        $last = (Get-Content -Raw -LiteralPath $Signal | ConvertFrom-Json).source_sha256
    }
    $errorsInARow = 0
    do {
        try {
            $digest = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash.ToLowerInvariant()
            $errorsInARow = 0
        } catch {
            $errorsInARow++
            if ($Once) { throw }
            $digest = $null
        }
        if (($digest -or $errorsInARow -ge 3) -and $digest -ne $last) {
            $reason = if ($digest) {'Review updated TP58 producer filing'} else {'Inspect unavailable TP58 producer filing'}
            $record = @{at=[DateTimeOffset]::UtcNow.ToString('o'); source_sha256=$digest; reason=$reason; research_admitted=$false}
            $temp = $Signal + '.tmp'
            [IO.File]::WriteAllText($temp,($record | ConvertTo-Json))
            [IO.File]::Move($temp,$Signal,$true)
            $last = $digest
        }
        if ($Once) { break }
        Start-Sleep -Seconds 90
    } while ([DateTimeOffset]::UtcNow -lt [DateTimeOffset]'2026-11-27T04:00:00Z')
} finally {
    $lock.Dispose()
}
