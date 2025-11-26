# PowerShell script to push to GitHub for lorbarca93 account
# Make sure you've created the repository at https://github.com/lorbarca93/house-in-engelberg first

Write-Host "=== Pushing to GitHub (lorbarca93 account) ===" -ForegroundColor Cyan
Write-Host ""

# Check if we're in a git repository
if (-not (Test-Path .git)) {
    Write-Host "[ERROR] Not a git repository!" -ForegroundColor Red
    exit 1
}

# Check git status
Write-Host "[*] Checking git status..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Host "[!] You have uncommitted changes:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    $response = Read-Host "Do you want to commit these changes? (y/n)"
    if ($response -eq "y") {
        git add .
        $commitMsg = Read-Host "Enter commit message (or press Enter for default)"
        if ([string]::IsNullOrWhiteSpace($commitMsg)) {
            $commitMsg = "Update repository"
        }
        git commit -m $commitMsg
    }
}

# Set remote URL
Write-Host "[*] Setting remote URL to lorbarca93 account..." -ForegroundColor Yellow
git remote set-url origin https://github.com/lorbarca93/house-in-engelberg.git

# Verify remote
Write-Host "[*] Verifying remote configuration..." -ForegroundColor Yellow
git remote -v

# Push to GitHub
Write-Host ""
Write-Host "[*] Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "Note: You may be prompted for GitHub credentials" -ForegroundColor Cyan
Write-Host ""

try {
    git push -u origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[+] Successfully pushed to GitHub!" -ForegroundColor Green
        Write-Host "Repository: https://github.com/lorbarca93/house-in-engelberg" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "[ERROR] Push failed. Make sure:" -ForegroundColor Red
        Write-Host "  1. The repository exists at https://github.com/lorbarca93/house-in-engelberg" -ForegroundColor Yellow
        Write-Host "  2. You have push access to the repository" -ForegroundColor Yellow
        Write-Host "  3. Your GitHub credentials are correct" -ForegroundColor Yellow
    }
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to push: $_" -ForegroundColor Red
}

