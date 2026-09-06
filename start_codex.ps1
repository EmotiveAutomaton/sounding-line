# Enter the Git repository so instructions and the canonical grind skill are discovered.
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$CodexArguments)
$ErrorActionPreference = 'Stop'
$workspacePath = (Resolve-Path -LiteralPath $PSScriptRoot).Path
& codex -C $workspacePath @CodexArguments
exit $LASTEXITCODE
