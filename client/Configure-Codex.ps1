param([ValidateRange(1024,65535)][int]$LocalPort = 18765)
$ErrorActionPreference = 'Stop'
# Use Codex's own configuration writer rather than replacing a user's TOML.
$codexCommand = Get-Command codex -ErrorAction SilentlyContinue
$codexExecutable = if ($codexCommand) { $codexCommand.Source } elseif ($env:CODEX_CLI_PATH -and (Test-Path -LiteralPath $env:CODEX_CLI_PATH)) { $env:CODEX_CLI_PATH } else { $null }
if (-not $codexExecutable) {
    throw 'Codex CLI is not discoverable. Ask Codex to merge client/config.example.toml into the actual user configuration instead; do not install another runtime.'
}
$endpoint = "http://127.0.0.1:$LocalPort/mcp"
$existingJson = & $codexExecutable mcp get giis_rag --json 2>$null
if ($LASTEXITCODE -eq 0) {
    $existing = ($existingJson -join "`n") | ConvertFrom-Json
    if ($existing.transport.url -ne $endpoint) {
        throw 'An existing giis_rag entry differs. Inspect it and obtain authorization before changing it.'
    }
    Write-Output 'GIIS MCP URL is already configured. Check timeout/tool settings against config.example.toml if needed.'
    return
}
$actualCodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$configPath = Join-Path $actualCodexHome 'config.toml'
if (Test-Path -LiteralPath $configPath) {
    $backupPath = $configPath + '.before-giis-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.bak'
    Copy-Item -LiteralPath $configPath -Destination $backupPath
}
& $codexExecutable mcp add giis_rag --url $endpoint
if ($LASTEXITCODE -ne 0) { throw 'Codex MCP registration failed; inspect the local backup and configuration.' }
$verified = & $codexExecutable mcp get giis_rag --json
if ($LASTEXITCODE -ne 0) { throw 'Codex could not read the registered MCP entry.' }
$parsed = ($verified -join "`n") | ConvertFrom-Json
if ($parsed.transport.url -ne $endpoint) { throw 'Registered endpoint did not match the intended loopback URL.' }
Write-Output 'GIIS MCP URL registered. Merge timeout/tool settings from config.example.toml if needed, then restart Codex and run Test-GiisMcp.ps1.'
