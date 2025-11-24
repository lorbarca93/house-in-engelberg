# PowerShell script to create private GitHub repository and push code
# This script will guide you through the process

param(
    [string]$GitHubUsername = "barcarolol-bit",
    [string]$RepoName = "house-in-engelberg",
    [string]$PersonalAccessToken = ""
)

Write-Host "=== GitHub Repository Creation and Push ===" -ForegroundColor Cyan
Write-Host ""

# Check if remote already exists
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "Remote 'origin' already exists: $existingRemote" -ForegroundColor Yellow
    $useExisting = Read-Host "Use existing remote and push? (y/n)"
    if ($useExisting -eq "y") {
        Write-Host "Pushing to existing remote..." -ForegroundColor Green
        git branch -M main
        git push -u origin main
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n=== Success! ===" -ForegroundColor Green
            Write-Host "Code pushed to: $existingRemote" -ForegroundColor Green
        }
        exit
    } else {
        Write-Host "Removing existing remote..." -ForegroundColor Yellow
        git remote remove origin
    }
}

# If no token provided, try to create repo via web interface instructions
if ([string]::IsNullOrWhiteSpace($PersonalAccessToken)) {
    Write-Host "GitHub CLI is not installed. Please create the repository manually:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Go to: https://github.com/new" -ForegroundColor White
    Write-Host "2. Repository name: $RepoName" -ForegroundColor White
    Write-Host "3. Description: Real Estate Investment Analysis Suite for Engelberg Property" -ForegroundColor White
    Write-Host "4. Select 'Private'" -ForegroundColor White
    Write-Host "5. DO NOT initialize with README, .gitignore, or license" -ForegroundColor White
    Write-Host "6. Click 'Create repository'" -ForegroundColor White
    Write-Host ""
    
    $continue = Read-Host "Have you created the repository? (y/n)"
    if ($continue -ne "y") {
        Write-Host "Please create the repository first, then run this script again." -ForegroundColor Red
        exit 1
    }
    
    $username = Read-Host "Enter your GitHub username (default: $GitHubUsername)"
    if ([string]::IsNullOrWhiteSpace($username)) {
        $username = $GitHubUsername
    }
    
    $repoName = Read-Host "Enter repository name (default: $RepoName)"
    if ([string]::IsNullOrWhiteSpace($repoName)) {
        $repoName = $RepoName
    }
    
    $remoteUrl = "https://github.com/$username/$repoName.git"
} else {
    # Use API to create repository
    Write-Host "Creating private repository via GitHub API..." -ForegroundColor Green
    
    $headers = @{
        "Authorization" = "token $PersonalAccessToken"
        "Accept" = "application/vnd.github.v3+json"
    }
    
    $body = @{
        name = $RepoName
        description = "Real Estate Investment Analysis Suite for Engelberg Property"
        private = $true
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Method Post -Headers $headers -Body $body -ContentType "application/json"
        $remoteUrl = $response.clone_url
        Write-Host "Repository created successfully!" -ForegroundColor Green
        Write-Host "Repository URL: $($response.html_url)" -ForegroundColor Cyan
    } catch {
        Write-Host "Failed to create repository via API: $_" -ForegroundColor Red
        Write-Host "Please create it manually at https://github.com/new" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Adding remote: $remoteUrl" -ForegroundColor Green
git remote add origin $remoteUrl

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to add remote. It may already exist." -ForegroundColor Red
    exit 1
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
    Write-Host "Repository URL: https://github.com/$username/$repoName" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "=== Push Failed ===" -ForegroundColor Red
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "1. Repository exists on GitHub" -ForegroundColor Yellow
    Write-Host "2. You have push access" -ForegroundColor Yellow
    Write-Host "3. Your GitHub credentials are configured" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You may need to authenticate. Try:" -ForegroundColor Yellow
    Write-Host "  git push -u origin main" -ForegroundColor White
    Write-Host ""
    Write-Host "If prompted for credentials, use:" -ForegroundColor Yellow
    Write-Host "  Username: Your GitHub username" -ForegroundColor White
    Write-Host "  Password: A Personal Access Token (not your password)" -ForegroundColor White
    Write-Host "  Create token at: https://github.com/settings/tokens" -ForegroundColor White
}

