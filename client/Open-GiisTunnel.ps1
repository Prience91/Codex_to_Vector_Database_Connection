param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9.:-]*$')][string]$ServerHost,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z_][A-Za-z0-9_.-]*$')][string]$SshUser,
    [ValidateRange(1024,65535)][int]$LocalPort = 18765,
    [ValidateRange(1024,65535)][int]$ServerPort = 8765
)
$ErrorActionPreference = 'Stop'
$helper = Join-Path $PSScriptRoot 'Connect-GiisRag.ps1'
if (-not (Test-Path -LiteralPath $helper)) { throw 'Connect-GiisRag.ps1 is missing beside this launcher.' }
# A visible window is required for the user's interactive password prompt.
$shellExecutable = (Get-Process -Id $PID).Path
$safeHelper = $helper.Replace("'", "''")
$command = "& '$safeHelper' -ServerHost '$ServerHost' -SshUser '$SshUser' -LocalPort $LocalPort -ServerPort $ServerPort"
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
Start-Process -FilePath $shellExecutable -ArgumentList @('-NoProfile','-NoExit','-EncodedCommand',$encoded) -WindowStyle Normal
Write-Output 'Tunnel window opened. Enter credentials there, then run Test-GiisMcp.ps1. Opening the window does not prove connectivity.'
