Param(
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$Args
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$env:PYTHONPATH = "src" + [System.IO.Path]::PathSeparator + ($env:PYTHONPATH ?? '')
pytest -q @Args

