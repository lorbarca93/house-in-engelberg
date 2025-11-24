# PowerShell script to push to GitHub
# Run this after creating the private repository on GitHub

Write-Host "=== GitHub Repository Push Script ===" -ForegroundColor Cyan
Write-Host ""

# Check if remote already exists
$remoteExists = git remote get-url origin 2>$null
if ($remoteExists) {
    Write-Host "Remote 'origin' already exists: $remoteExists" -ForegroundColor Yellow
    $useExisting = Read-Host "Use existing remote? (y/n)"
    if ($useExisting -ne "y") {
        Write-Host "Please remove the existing remote first: git remote remove origin" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Please create a private repository on GitHub first:" -ForegroundColor Yellow
    Write-Host "1. Go to https://github.com/new" -ForegroundColor White
    Write-Host "2. Repository name: house-in-engelberg" -ForegroundColor White
    Write-Host "3. Select 'Private'" -ForegroundColor White
    Write-Host "4. DO NOT initialize with README/gitignore" -ForegroundColor White
    Write-Host "5. Click 'Create repository'" -ForegroundColor White
    Write-Host ""
    
    $username = Read-Host "Enter your GitHub username"
    $repoName = Read-Host "Enter repository name (default: house-in-engelberg)"
    if ([string]::IsNullOrWhiteSpace($repoName)) {
        $repoName = "house-in-engelberg"
    }
    
    $remoteUrl = "https://github.com/$username/$repoName.git"
    Write-Host ""
    Write-Host "Adding remote: $remoteUrl" -ForegroundColor Green
    git remote add origin $remoteUrl
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to add remote. It may already exist." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Renaming branch to 'main'..." -ForegroundColor Green
git branch -M main

Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Green
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Success! ===" -ForegroundColor Green
    Write-Host "Your repository has been pushed to GitHub as a private repository." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "=== Error ===" -ForegroundColor Red
    Write-Host "Push failed. Please check:" -ForegroundColor Red
    Write-Host "1. Repository exists on GitHub" -ForegroundColor Yellow
    Write-Host "2. You have push access" -ForegroundColor Yellow
    Write-Host "3. Your GitHub credentials are configured" -ForegroundColor Yellow
}

