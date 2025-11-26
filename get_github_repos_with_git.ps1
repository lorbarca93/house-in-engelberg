# Try to use git credentials to authenticate with GitHub API
$username = "lorbarca93"

# Try to get credentials from git credential helper
$credentialHelper = git config --global credential.helper
Write-Host "Credential helper: $credentialHelper" -ForegroundColor Cyan

# Try using git credential fill to get token
$credInput = "protocol=https`nhost=github.com`n"
$credOutput = $credInput | git credential fill 2>&1

Write-Host "`nAttempting to list all repositories..." -ForegroundColor Green

# Try using GitHub API with different authentication methods
$headers = @{
    "Accept" = "application/vnd.github.v3+json"
    "User-Agent" = "PowerShell"
}

# Method 1: Try with stored git credentials via credential manager
try {
    # Use git to get a token if available
    $response = Invoke-RestMethod -Uri "https://api.github.com/user/repos?per_page=100&type=all&affiliation=owner" -Headers $headers -ErrorAction Stop
    Write-Host "Successfully authenticated!`n" -ForegroundColor Green
    Write-Host "Your GitHub Repositories:`n" -ForegroundColor Green
    $response | Select-Object -Property name, full_name, description, @{Name='private';Expression={$_.private}}, clone_url | Format-Table -AutoSize
    Write-Host "`nTotal repos: $($response.Count)" -ForegroundColor Cyan
    $privateCount = ($response | Where-Object { $_.private -eq $true }).Count
    $publicCount = ($response | Where-Object { $_.private -eq $false }).Count
    Write-Host "Public: $publicCount | Private: $privateCount" -ForegroundColor Cyan
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nTrying alternative method..." -ForegroundColor Yellow
    
    # Fallback: Show public repos
    try {
        $response = Invoke-RestMethod -Uri "https://api.github.com/users/$username/repos?per_page=100" -Headers $headers -ErrorAction Stop
        Write-Host "`nPublic Repositories (authentication needed for private repos):`n" -ForegroundColor Yellow
        $response | Select-Object -Property name, full_name, description, @{Name='private';Expression={$_.private}}, clone_url | Format-Table -AutoSize
        Write-Host "`nTotal public repos: $($response.Count)" -ForegroundColor Cyan
    } catch {
        Write-Host "Could not fetch repositories: $($_.Exception.Message)" -ForegroundColor Red
    }
}

