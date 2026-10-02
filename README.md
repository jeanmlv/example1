# example1

# ==============================================================================
# ARGES Commons -> Thea Dashboard synchronization
# ==============================================================================
#
# Workflow:
#
#   ARGES Commons
#       -> develop / update
#       -> test
#       -> commit
#       -> push
#       -> run this script
#
#   Thea Dashboard
#       -> review changes
#       -> test
#       -> commit
#       -> push
#       -> PR
#
# The ARGES Commons repository is the source of truth.
#
# This script synchronizes:
#   - src/
#   - views/
#   - ARGES_COMMONS.xlsx
#
# It does NOT commit or push anything.
# ==============================================================================


# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

$Source = Join-Path $PSScriptRoot "..\arges_commons_dashboard"

$Destination = Join-Path `
    $PSScriptRoot `
    "structure\Arges\Commons Dashboard"


# ------------------------------------------------------------------------------
# Header
# ------------------------------------------------------------------------------

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
# Validate ARGES Commons Git repository
# ------------------------------------------------------------------------------

Write-Host "Checking ARGES Commons repository..."
Write-Host ""


$SourceGitDirectory = Join-Path $Source ".git"

if (-not (Test-Path $SourceGitDirectory)) {

    Write-Host "ERROR: ARGES Commons is not a Git repository."
    Write-Host ""
    Write-Host "Expected Git repository:"
    Write-Host $Source

    exit 1
}


# ------------------------------------------------------------------------------
# Check for uncommitted changes in ARGES Commons
# ------------------------------------------------------------------------------

$ArgesStatus = git -C $Source status --porcelain


if ($LASTEXITCODE -ne 0) {

    Write-Host "ERROR: Unable to read ARGES Commons Git status."

    exit 1
}


if ($ArgesStatus) {

    Write-Host "ERROR: ARGES Commons contains uncommitted changes."
    Write-Host ""

    git -C $Source status --short

    Write-Host ""
    Write-Host "Commit the ARGES Commons changes before synchronization."
    Write-Host ""

    exit 1
}


Write-Host "ARGES Commons working tree is clean."


# ------------------------------------------------------------------------------
# Check current ARGES branch
# ------------------------------------------------------------------------------

$ArgesBranch = git -C $Source branch --show-current


if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($ArgesBranch)) {

    Write-Host ""
    Write-Host "ERROR: Unable to determine ARGES Commons branch."

    exit 1
}


Write-Host "ARGES Commons branch: $ArgesBranch"


# ------------------------------------------------------------------------------
# Fetch ARGES remote information
# ------------------------------------------------------------------------------

Write-Host ""
Write-Host "Checking ARGES Commons remote..."
Write-Host ""


git -C $Source fetch origin --quiet


if ($LASTEXITCODE -ne 0) {

    Write-Host "ERROR: Unable to fetch ARGES Commons origin."
    Write-Host ""
    Write-Host "Check your network/VPN and Git access."

    exit 1
}


# ------------------------------------------------------------------------------
# Check whether current ARGES branch has an upstream
# ------------------------------------------------------------------------------

$ArgesUpstream = git -C $Source `
    rev-parse `
    --abbrev-ref `
    --symbolic-full-name `
    "@{u}" 2>$null


if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($ArgesUpstream)) {

    Write-Host "ERROR: Current ARGES branch has no upstream branch."
    Write-Host ""
    Write-Host "Push the branch first, for example:"
    Write-Host ""
    Write-Host "    git push -u origin $ArgesBranch"
    Write-Host ""

    exit 1
}


Write-Host "ARGES Commons upstream: $ArgesUpstream"


# ------------------------------------------------------------------------------
# Verify that local ARGES commits were pushed
# ------------------------------------------------------------------------------

$AheadCount = git -C $Source `
    rev-list `
    --count `
    "$ArgesUpstream..HEAD"


if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: Unable to compare ARGES Commons with upstream."

    exit 1
}


$BehindCount = git -C $Source `
    rev-list `
    --count `
    "HEAD..$ArgesUpstream"


if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: Unable to compare ARGES Commons with upstream."

    exit 1
}


if ([int]$AheadCount -gt 0) {

    Write-Host ""
    Write-Host "ERROR: ARGES Commons contains commits that have not been pushed."
    Write-Host ""
    Write-Host "Local branch is ahead of $ArgesUpstream by $AheadCount commit(s)."
    Write-Host ""
    Write-Host "Push ARGES Commons before synchronization:"
    Write-Host ""
    Write-Host "    git push"
    Write-Host ""

    exit 1
}


if ([int]$BehindCount -gt 0) {

    Write-Host ""
    Write-Host "ERROR: ARGES Commons is behind its remote branch."
    Write-Host ""
    Write-Host "Local branch is behind $ArgesUpstream by $BehindCount commit(s)."
    Write-Host ""
    Write-Host "Update ARGES Commons before synchronization."
    Write-Host ""

    exit 1
}


Write-Host "ARGES Commons is synchronized with remote."


# ------------------------------------------------------------------------------
# Validate required source items
# ------------------------------------------------------------------------------

$RequiredItems = @(
    "src",
    "views",
    "ARGES_COMMONS.xlsx"
)


foreach ($Item in $RequiredItems) {

    $ItemPath = Join-Path $Source $Item

    if (-not (Test-Path $ItemPath)) {

        Write-Host ""
        Write-Host "ERROR: Required source item not found:"
        Write-Host $ItemPath

        exit 1
    }
}


# ------------------------------------------------------------------------------
# Show synchronization plan
# ------------------------------------------------------------------------------

Write-Host ""
Write-Host "The following items will be synchronized:"
Write-Host ""
Write-Host "  - src"
Write-Host "  - views"
Write-Host "  - ARGES_COMMONS.xlsx"
Write-Host ""

Write-Host "Excluded:"
Write-Host ""
Write-Host "  - __pycache__"
Write-Host "  - *.pyc"
Write-Host ""

Write-Host "IMPORTANT:"
Write-Host "ARGES Commons is the source of truth."
Write-Host ""

Write-Host "Files inside src/ and views/ that do not exist"
Write-Host "in ARGES Commons may be removed from the Thea copy."
Write-Host ""


# ------------------------------------------------------------------------------
# Confirmation
# ------------------------------------------------------------------------------

$Confirmation = Read-Host "Continue synchronization? (y/n)"


if ($Confirmation -notin @("y", "Y")) {

    Write-Host ""
    Write-Host "Synchronization cancelled."
    Write-Host ""

    exit 0
}


Write-Host ""
Write-Host "Starting synchronization..."
Write-Host ""


# ------------------------------------------------------------------------------
# Synchronize src
# ------------------------------------------------------------------------------

Write-Host "----------------------------------------------"
Write-Host " Synchronizing src"
Write-Host "----------------------------------------------"
Write-Host ""


robocopy `
    (Join-Path $Source "src") `
    (Join-Path $Destination "src") `
    /MIR `
    /XD "__pycache__" `
    /XF "*.pyc" `
    /R:2 `
    /W:2


$SrcExitCode = $LASTEXITCODE


if ($SrcExitCode -ge 8) {

    Write-Host ""
    Write-Host "ERROR: Failed to synchronize src."
    Write-Host "Robocopy exit code: $SrcExitCode"
    Write-Host ""

    exit $SrcExitCode
}


Write-Host ""
Write-Host "src synchronized successfully."
Write-Host ""


# ------------------------------------------------------------------------------
# Synchronize views
# ------------------------------------------------------------------------------

Write-Host "----------------------------------------------"
Write-Host " Synchronizing views"
Write-Host "----------------------------------------------"
Write-Host ""


robocopy `
    (Join-Path $Source "views") `
    (Join-Path $Destination "views") `
    /MIR `
    /XD "__pycache__" `
    /XF "*.pyc" `
    /R:2 `
    /W:2


$ViewsExitCode = $LASTEXITCODE


if ($ViewsExitCode -ge 8) {

    Write-Host ""
    Write-Host "ERROR: Failed to synchronize views."
    Write-Host "Robocopy exit code: $ViewsExitCode"
    Write-Host ""

    exit $ViewsExitCode
}


Write-Host ""
Write-Host "views synchronized successfully."
Write-Host ""


# ------------------------------------------------------------------------------
# Synchronize workbook
# ------------------------------------------------------------------------------

Write-Host "----------------------------------------------"
Write-Host " Synchronizing ARGES_COMMONS.xlsx"
Write-Host "----------------------------------------------"
Write-Host ""


try {

    Copy-Item `
        (Join-Path $Source "ARGES_COMMONS.xlsx") `
        (Join-Path $Destination "ARGES_COMMONS.xlsx") `
        -Force `
        -ErrorAction Stop

}
catch {

    Write-Host ""
    Write-Host "ERROR: Failed to copy ARGES_COMMONS.xlsx."
    Write-Host ""
    Write-Host $_.Exception.Message
    Write-Host ""

    exit 1
}


Write-Host "ARGES_COMMONS.xlsx synchronized successfully."
Write-Host ""


# ------------------------------------------------------------------------------
# Synchronization completed
# ------------------------------------------------------------------------------

Write-Host "=============================================="
Write-Host " Synchronization completed"
Write-Host "=============================================="
Write-Host ""

Write-Host "ARGES source branch:"
Write-Host "  $ArgesBranch"
Write-Host ""

Write-Host "ARGES upstream:"
Write-Host "  $ArgesUpstream"
Write-Host ""

Write-Host "Review the Thea Dashboard changes with:"
Write-Host ""
Write-Host "    git status"
Write-Host ""
Write-Host "    git diff --stat"
Write-Host ""
Write-Host "    git diff"
Write-Host ""

Write-Host "IMPORTANT:"
Write-Host "Nothing has been committed or pushed to Thea."
Write-Host ""

Write-Host "Recommended next steps:"
Write-Host ""
Write-Host "  1. Review git status"
Write-Host "  2. Review git diff --stat"
Write-Host "  3. Review important code changes"
Write-Host "  4. Test the dashboard"
Write-Host "  5. Commit the Thea changes"
Write-Host "  6. Push the Thea branch"
Write-Host "  7. Open/update the PR"
Write-Host ""
