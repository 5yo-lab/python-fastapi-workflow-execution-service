#!/usr/bin/env pwsh
# Full docker-compose smoke test for the workflow execution service.
# Usage: .\scripts\smoke-test.ps1
#        .\scripts\smoke-test.ps1 -ApiBaseUrl http://localhost:8000

param(
    [string]$ApiBaseUrl = $(if ($env:API_BASE_URL) { $env:API_BASE_URL } else { "http://localhost:8000" }),
    [string]$FrontendUrl = $(if ($env:FRONTEND_URL) { $env:FRONTEND_URL } else { "http://localhost:3000" }),
    [string]$PgAdminUrl = $(if ($env:PGADMIN_URL) { $env:PGADMIN_URL } else { "http://localhost:5050" }),
    [int]$ValidationPollSeconds = 40,
    [int]$ProcessingPollSeconds = 60,
    [int]$PollIntervalSeconds = 2,
    [switch]$SkipFrontend,
    [switch]$SkipPgAdmin,
    [switch]$ShowWorkerLogs
)

$ErrorActionPreference = "Stop"
$failures = @()

function Write-Pass([string]$Message) {
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Write-Fail([string]$Message) {
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    $script:failures += $Message
}

function Get-Workflow([string]$WorkflowId) {
    return Invoke-RestMethod -Uri "$ApiBaseUrl/workflows/$WorkflowId" -Method Get
}

function Invoke-Transition([object]$Workflow, [string]$Action) {
    $body = @{
        action          = $Action
        expectedVersion = $Workflow.version
    } | ConvertTo-Json

    return Invoke-RestMethod `
        -Uri "$ApiBaseUrl/workflows/$($Workflow.id)/transitions" `
        -Method Post `
        -Body $body `
        -ContentType "application/json"
}

function Wait-ForWorkflowState {
    param(
        [string]$WorkflowId,
        [string[]]$TargetStates,
        [string[]]$FailureStates,
        [int]$MaxSeconds,
        [string]$Label,
        [scriptblock]$OnFailureState
    )

    $maxPolls = [math]::Ceiling($MaxSeconds / $PollIntervalSeconds)
    $workflow = $null

    for ($i = 1; $i -le $maxPolls; $i++) {
        Start-Sleep -Seconds $PollIntervalSeconds
        $workflow = Get-Workflow -WorkflowId $WorkflowId
        Write-Host "  $Label poll ${i}: state=$($workflow.state) version=$($workflow.version)"

        if ($workflow.state -in $TargetStates) {
            return @{ Success = $true; Workflow = $workflow }
        }

        if ($workflow.state -in $FailureStates) {
            if ($OnFailureState) {
                $workflow = & $OnFailureState $workflow
                continue
            }
            return @{ Success = $false; Workflow = $workflow }
        }
    }

    return @{ Success = $false; Workflow = $workflow }
}

Write-Host ""
Write-Host "=== Workflow Execution Service - Smoke Tests ===" -ForegroundColor Cyan
Write-Host "API:      $ApiBaseUrl"
Write-Host "Frontend: $FrontendUrl"
Write-Host "pgAdmin:  $PgAdminUrl"
Write-Host ""

# 1. Health
try {
    $health = Invoke-RestMethod -Uri "$ApiBaseUrl/health" -Method Get
    if ($health.status -ne "ok") {
        throw "unexpected status: $($health.status)"
    }
    Write-Pass "GET /health"
}
catch {
    Write-Fail "GET /health - $_"
}

# 2. Create workflow
$workflow = $null
try {
    $reference = "SMOKE-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    $body = @{
        reference = $reference
        payload   = @{
            customerId = "smoke-customer"
            amount     = 250
        }
    } | ConvertTo-Json -Depth 5

    $workflow = Invoke-RestMethod `
        -Uri "$ApiBaseUrl/workflows" `
        -Method Post `
        -Body $body `
        -ContentType "application/json"

    Write-Pass "POST /workflows - id=$($workflow.id) state=$($workflow.state)"
}
catch {
    Write-Fail "POST /workflows - $_"
    Write-Host ""
    Write-Host "FAILED: cannot continue without a workflow." -ForegroundColor Red
    exit 1
}

$workflowId = $workflow.id

# 3. START_VALIDATION
try {
    $workflow = Invoke-Transition -Workflow $workflow -Action "START_VALIDATION"
    if ($workflow.state -ne "VALIDATING") {
        throw "expected VALIDATING, got $($workflow.state)"
    }
    Write-Pass "START_VALIDATION -> $($workflow.state)"
}
catch {
    Write-Fail "START_VALIDATION - $_"
}

# 4. Wait for worker validation
$validation = Wait-ForWorkflowState `
    -WorkflowId $workflowId `
    -TargetStates @("APPROVED") `
    -FailureStates @("VALIDATION_FAILED", "CANCELLED") `
    -MaxSeconds $ValidationPollSeconds `
    -Label "validation"

if ($validation.Success) {
    $workflow = $validation.Workflow
    Write-Pass "Worker validation -> APPROVED"
}
else {
    Write-Fail "Worker validation stuck at $($validation.Workflow.state)"
}

# 5. START_PROCESSING + wait for completion (retry on simulated failure)
if ($workflow.state -eq "APPROVED") {
    try {
        $workflow = Invoke-Transition -Workflow $workflow -Action "START_PROCESSING"
        if ($workflow.state -ne "PROCESSING") {
            throw "expected PROCESSING, got $($workflow.state)"
        }
        Write-Pass "START_PROCESSING -> $($workflow.state)"
    }
    catch {
        Write-Fail "START_PROCESSING - $_"
    }
}

$completed = $false
if ($workflow.state -eq "PROCESSING") {
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        $processing = Wait-ForWorkflowState `
            -WorkflowId $workflowId `
            -TargetStates @("COMPLETED") `
            -FailureStates @("PROCESSING_FAILED") `
            -MaxSeconds $ProcessingPollSeconds `
            -Label "processing (attempt $attempt)" `
            -OnFailureState {
                param($current)
                Write-Host "  simulated processing failure, retrying START_PROCESSING..."
                return Invoke-Transition -Workflow $current -Action "START_PROCESSING"
            }

        $workflow = $processing.Workflow
        if ($processing.Success) {
            $completed = $true
            break
        }

        if ($workflow.state -ne "PROCESSING_FAILED") {
            break
        }
    }
}

if ($completed) {
    Write-Pass "Worker processing -> COMPLETED"
}
elseif ($workflow.state -ne "APPROVED") {
    Write-Fail "Worker processing stuck at $($workflow.state)"
}

# 6. History
try {
    $history = Invoke-RestMethod -Uri "$ApiBaseUrl/workflows/$workflowId/history" -Method Get
    $actions = ($history | ForEach-Object { $_.action }) -join " -> "
    Write-Pass "GET /workflows/$workflowId/history - $($history.Count) entries: $actions"
}
catch {
    Write-Fail "GET /history - $_"
}

# 7. List workflows
try {
    $list = Invoke-RestMethod -Uri "$ApiBaseUrl/workflows" -Method Get
    Write-Pass "GET /workflows - $($list.Count) workflow(s)"
}
catch {
    Write-Fail "GET /workflows - $_"
}

# 8. Frontend
if (-not $SkipFrontend) {
    try {
        $response = Invoke-WebRequest -Uri $FrontendUrl -UseBasicParsing
        if ($response.StatusCode -ne 200) {
            throw "HTTP $($response.StatusCode)"
        }
        Write-Pass "Frontend $FrontendUrl"
    }
    catch {
        Write-Fail "Frontend $FrontendUrl - $_"
    }
}

# 9. pgAdmin
if (-not $SkipPgAdmin) {
    try {
        Invoke-WebRequest -Uri $PgAdminUrl -UseBasicParsing | Out-Null
        Write-Pass "pgAdmin $PgAdminUrl"
    }
    catch {
        $status = $_.Exception.Response.StatusCode.value__
        if ($status -in @(200, 301, 302)) {
            Write-Pass "pgAdmin $PgAdminUrl"
        }
        else {
            Write-Fail "pgAdmin $PgAdminUrl - $_"
        }
    }
}

if ($ShowWorkerLogs) {
    Write-Host ""
    Write-Host "=== Worker logs (last 20 lines) ===" -ForegroundColor Cyan
    docker logs workflow-node-worker 2>&1 | Select-Object -Last 20
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
if ($failures.Count -eq 0) {
    Write-Host "All smoke tests PASSED" -ForegroundColor Green
    exit 0
}

Write-Host "Smoke tests FAILED ($($failures.Count) issue(s)):" -ForegroundColor Red
$failures | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
exit 1
