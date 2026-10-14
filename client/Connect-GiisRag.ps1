param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9.:-]*$')][string]$ServerHost,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z_][A-Za-z0-9_.-]*$')][string]$SshUser,
    [ValidateRange(1024,65535)][int]$LocalPort = 18765,
    [ValidateRange(1024,65535)][int]$ServerPort = 8765
)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    throw 'OpenSSH client is unavailable. Ask your administrator to supply it.'
}
Write-Host 'Enter the company password only at the SSH prompt. Leave this window open.'
Write-Host "Local MCP URL: http://127.0.0.1:$LocalPort/mcp"
& ssh -N -L "127.0.0.1:${LocalPort}:127.0.0.1:${ServerPort}" `
    -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
    -o StrictHostKeyChecking=ask "${SshUser}@${ServerHost}"
if ($LASTEXITCODE -ne 0) { throw "SSH tunnel exited with code $LASTEXITCODE" }
