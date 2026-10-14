param(
    [ValidateRange(1024,65535)][int]$LocalPort = 18765,
    [string]$Query
)
$ErrorActionPreference = 'Stop'
$endpoint = "http://127.0.0.1:$LocalPort/mcp"
$headers = @{Accept='application/json, text/event-stream'}
function Invoke-McpRequest($payload) {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $endpoint -Method Post `
        -Headers $headers -ContentType 'application/json' `
        -Body ($payload | ConvertTo-Json -Depth 12 -Compress) -TimeoutSec 180
    if ($response.Headers['Mcp-Session-Id']) {
        $headers['Mcp-Session-Id'] = [string]$response.Headers['Mcp-Session-Id']
    }
    if (-not $response.Content) { return $null }
    $message = $response.Content | ConvertFrom-Json
    if ($message.error) { throw ($message.error | ConvertTo-Json -Compress) }
    return $message
}
$init = Invoke-McpRequest @{jsonrpc='2.0';id=1;method='initialize';params=@{
    protocolVersion='2025-06-18';capabilities=@{};
    clientInfo=@{name='giis-onboarding-check';version='1.0.0'}
}}
if (-not $init.result.protocolVersion) { throw 'MCP initialization did not return a protocol version' }
$headers['MCP-Protocol-Version'] = $init.result.protocolVersion
$null = Invoke-McpRequest @{jsonrpc='2.0';method='notifications/initialized'}
$listed = Invoke-McpRequest @{jsonrpc='2.0';id=2;method='tools/list';params=@{}}
$names = @($listed.result.tools | ForEach-Object { $_.name })
foreach ($name in @('search_evidence','retrieve_obligations','fetch_passage')) {
    if ($names -notcontains $name) { throw "Required tool missing: $name" }
}
$summary = [ordered]@{state='mcp_handshake_and_tools_passed';endpoint=$endpoint;tools=$names;semantic_coverage_certified=$false}
if ($Query) {
    $called = Invoke-McpRequest @{jsonrpc='2.0';id=3;method='tools/call';params=@{
        name='search_evidence';arguments=@{question=$Query}
    }}
    if ($called.result.isError) { throw 'Search tool returned an error' }
    $packet = ($called.result.content | Where-Object {$_.type -eq 'text'} | Select-Object -First 1).text | ConvertFrom-Json
    if (-not $packet.packet_id) { throw 'Search response is not a GIIS evidence packet' }
    $summary['state'] = 'basic_retrieval_passed'
    $summary['passage_count'] = @($packet.evidence).Count
    $summary['packet_id'] = $packet.packet_id
    foreach ($passage in $packet.evidence) {
        if (-not $passage.chunk_id -or -not $passage.document_id -or -not $passage.text) {
            throw 'Malformed passage in search response'
        }
    }
    if (@($packet.evidence).Count -eq 0) { $summary['state'] = 'connected_but_no_qualifying_evidence' }
}
$summary | ConvertTo-Json -Depth 5
