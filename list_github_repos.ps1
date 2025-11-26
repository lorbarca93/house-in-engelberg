# Script to list GitHub repositories (including private ones)
$username = "lorbarca93"
$headers = @{}

# Check for GitHub token in environment variables
if ($env:GITHUB_TOKEN) {
    $headers['Authorization'] = "token $env:GITHUB_TOKEN"
    Write-Host "Using GITHUB_TOKEN from environment" -ForegroundColor Green
} elseif ($env:GH_TOKEN) {
    $headers['Authorization'] = "token $env:GH_TOKEN"
    Write-Host "Using GH_TOKEN from environment" -ForegroundColor Green
} else {
    Write-Host "No GitHub token found in environment variables" -ForegroundColor Yellow
    Write-Host "`nTo see ALL repositories (including private), you need to:" -ForegroundColor Yellow
    Write-Host "1. Create a Personal Access Token (PAT) at: https://github.com/settings/tokens" -ForegroundColor Cyan
    Write-Host "2. Set it as an environment variable:" -ForegroundColor Cyan
    Write-Host "   `$env:GITHUB_TOKEN = 'your_token_here'" -ForegroundColor White
    Write-Host "`nFor now, showing only PUBLIC repositories...`n" -ForegroundColor Yellow
}

try {
    # Try authenticated first (for private repos)
    if ($headers.ContainsKey('Authorization')) {
        Write-Host "Fetching ALL repositories (public + private)...`n" -ForegroundColor Green
        $response = Invoke-RestMethod -Uri "https://api.github.com/user/repos?per_page=100&type=all&affiliation=owner" -Headers $headers -ErrorAction Stop
    } else {
        # Fall back to public repos only
        Write-Host "Fetching PUBLIC repositories only...`n" -ForegroundColor Yellow
        $response = Invoke-RestMethod -Uri "https://api.github.com/users/$username/repos?per_page=100" -Headers $headers -ErrorAction Stop
    }
    
    Write-Host "Your GitHub Repositories:`n" -ForegroundColor Green
    $response | Select-Object -Property name, full_name, description, @{Name='private';Expression={$_.private}}, clone_url | Format-Table -AutoSize
    Write-Host "`nTotal repos: $($response.Count)" -ForegroundColor Cyan
    $privateCount = ($response | Where-Object { $_.private -eq $true }).Count
    $publicCount = ($response | Where-Object { $_.private -eq $false }).Count
    Write-Host "Public: $publicCount | Private: $privateCount" -ForegroundColor Cyan
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "`nAuthentication failed. Please check your token." -ForegroundColor Red
    } elseif ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "`nUser not found or no access." -ForegroundColor Red
    }
}

