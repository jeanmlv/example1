# example1

# ==============================================================================
# ARGES Commons -> Thea Dashboard synchronization
# ==============================================================================

$Source = Join-Path $PSScriptRoot "..\arges_commons_dashboard"
$Destination = Join-Path $PSScriptRoot "structure\Arges\Commons Dashboard"

Write-Host ""
Write-Host "=============================================="
Write-Host " ARGES Commons -> Thea Dashboard Sync"
Write-Host "=============================================="
Write-Host ""

# ------------------------------------------------------------------------------
# Validate paths
# ------------------------------------------------------------------------------

if (-not (Test-Path $Source)) {
    Write-Host "ERROR: Source repository not found:"
    Write-Host $Source
    exit 1
}

if (-not (Test-Path $Destination)) {
    Write-Host "ERROR: Thea Dashboard destination not found:"
    Write-Host $Destination
    exit 1
}

Write-Host "Source:"
Write-Host $Source

Write-Host ""
Write-Host "Destination:"
Write-Host $Destination
Write-Host ""

# ------------------------------------------------------------------------------
# Files/directories to synchronize
# ------------------------------------------------------------------------------

$Items = @(
    "src",
    "views",
    "ARGES_COMMONS.xlsx"
)

Write-Host "The following items will be synchronized:"
foreach ($Item in $Items) {
    Write-Host "  - $Item"
}

Write-Host ""

# ------------------------------------------------------------------------------
# Confirmation
# ------------------------------------------------------------------------------

$Confirmation = Read-Host "Continue? (y/n)"

if ($Confirmation -ne "y") {
    Write-Host ""
    Write-Host "Synchronization cancelled."
    exit
}

Write-Host ""
Write-Host "Starting synchronization..."
Write-Host ""

# ------------------------------------------------------------------------------
# Copy src
# ------------------------------------------------------------------------------

robocopy `
    (Join-Path $Source "src") `
    (Join-Path $Destination "src") `
    /E `
    /XD "__pycache__" `
    /XF "*.pyc"

# ------------------------------------------------------------------------------
# Copy views
# ------------------------------------------------------------------------------

robocopy `
    (Join-Path $Source "views") `
    (Join-Path $Destination "views") `
    /E `
    /XD "__pycache__" `
    /XF "*.pyc"

# ------------------------------------------------------------------------------
# Copy workbook
# ------------------------------------------------------------------------------

Copy-Item `
    (Join-Path $Source "ARGES_COMMONS.xlsx") `
    (Join-Path $Destination "ARGES_COMMONS.xlsx") `
    -Force

Write-Host ""
Write-Host "=============================================="
Write-Host " Synchronization completed"
Write-Host "=============================================="
Write-Host ""
Write-Host "Review the changes with:"
Write-Host ""
Write-Host "    git status"
Write-Host "    git diff --stat"
Write-Host ""
Write-Host "Nothing has been committed or pushed."
Write-Host ""
