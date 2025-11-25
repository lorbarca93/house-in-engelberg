# PowerShell script to push to GitHub
# Run this AFTER creating the repository on GitHub

Write-Host "`n=== Pushing to GitHub ===" -ForegroundColor Green
Write-Host ""

# Check if remote exists
$remote = git remote get-url origin 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] No remote configured. Please set up the remote first." -ForegroundColor Red
    Write-Host "Run: git remote add origin <your-repo-url>" -ForegroundColor Yellow
    exit 1
}

Write-Host "Remote URL: $remote" -ForegroundColor Cyan
Write-Host ""

# Check current branch
$branch = git branch --show-current
Write-Host "Current branch: $branch" -ForegroundColor Cyan
Write-Host ""

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push -u origin $branch

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] All changes pushed to GitHub!" -ForegroundColor Green
    Write-Host "Repository: $remote" -ForegroundColor Cyan
} else {
    Write-Host "`n[ERROR] Push failed. Possible reasons:" -ForegroundColor Red
    Write-Host "1. Repository doesn't exist on GitHub yet" -ForegroundColor Yellow
    Write-Host "   - Create it at: https://github.com/new" -ForegroundColor Gray
    Write-Host "   - Name: house-in-engelberg" -ForegroundColor Gray
    Write-Host "   - Make it PRIVATE" -ForegroundColor Gray
    Write-Host "   - DO NOT initialize with README" -ForegroundColor Gray
    Write-Host "2. Authentication required" -ForegroundColor Yellow
    Write-Host "   - Use GitHub CLI: gh auth login" -ForegroundColor Gray
    Write-Host "   - Or use personal access token" -ForegroundColor Gray
    Write-Host "3. Wrong remote URL" -ForegroundColor Yellow
    Write-Host "   - Update with: git remote set-url origin <correct-url>" -ForegroundColor Gray
}

