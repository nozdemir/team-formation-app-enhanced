# Heroku App Management Script
# Usage: .\heroku-manage.ps1 [command] [app-name]

param(
    [string]$Command,
    [string]$AppName = "team-formation-app-new-05"
)

$Apps = @{
    "production" = "team-formation-app-new-05"
    "gazi" = "team-formation-app-gazi"
    "gazi2" = "team-formation-app-gazi-2"
    "working" = "team-formation-working-app"
}

function Show-Status {
    Write-Host "=== Current App Status ===" -ForegroundColor Green
    foreach ($app in $Apps.Values) {
        Write-Host "Checking $app..." -ForegroundColor Yellow
        heroku ps -a $app
        Write-Host ""
    }
}

function Start-App {
    param([string]$App)
    if ($Apps.ContainsKey($App)) {
        $AppName = $Apps[$App]
        Write-Host "Starting $AppName..." -ForegroundColor Green
        heroku ps:scale web=1 -a $AppName
        Write-Host "App started! URL: https://$AppName.herokuapp.com" -ForegroundColor Green
    } else {
        Write-Host "Unknown app: $App. Available: $($Apps.Keys -join ', ')" -ForegroundColor Red
    }
}

function Stop-App {
    param([string]$App)
    if ($Apps.ContainsKey($App)) {
        $AppName = $Apps[$App]
        Write-Host "Stopping $AppName..." -ForegroundColor Yellow
        heroku ps:scale web=0 -a $AppName
        Write-Host "App stopped. No longer billing." -ForegroundColor Green
    } else {
        Write-Host "Unknown app: $App. Available: $($Apps.Keys -join ', ')" -ForegroundColor Red
    }
}

function Stop-All {
    Write-Host "Stopping all non-production apps..." -ForegroundColor Yellow
    foreach ($key in $Apps.Keys) {
        if ($key -ne "production") {
            Stop-App $key
        }
    }
    Write-Host "All test apps stopped. Only production running." -ForegroundColor Green
}

function Show-Costs {
    Write-Host "=== Monthly Cost Breakdown ===" -ForegroundColor Green
    $runningApps = 0
    foreach ($app in $Apps.Values) {
        $status = heroku ps -a $app 2>$null
        if ($status -match "up \d") {
            $runningApps++
            Write-Host "$app : $7/month (RUNNING)" -ForegroundColor Red
        } else {
            Write-Host "$app : $0/month (STOPPED)" -ForegroundColor Green
        }
    }
    Write-Host ""
    Write-Host "Total running apps: $runningApps" -ForegroundColor Yellow
    Write-Host "Monthly cost: $($runningApps * 7)" -ForegroundColor Yellow
    Write-Host "GitHub Student credit: $13" -ForegroundColor Green
    $net = ($runningApps * 7) - 13
    if ($net -le 0) {
        Write-Host "Net cost: FREE (surplus: $([Math]::Abs($net)))" -ForegroundColor Green
    } else {
        Write-Host "Net cost: $net/month" -ForegroundColor Red
    }
}

# Main script logic
switch ($Command.ToLower()) {
    "status" { Show-Status }
    "start" { Start-App $AppName }
    "stop" { Stop-App $AppName }
    "stopall" { Stop-All }
    "costs" { Show-Costs }
    default {
        Write-Host "Heroku App Manager" -ForegroundColor Cyan
        Write-Host "=================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Usage: .\heroku-manage.ps1 [command] [app]" -ForegroundColor White
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Yellow
        Write-Host "  status    - Show all app status" -ForegroundColor White
        Write-Host "  start     - Start an app (costs `$7/month)" -ForegroundColor White
        Write-Host "  stop      - Stop an app (saves `$7/month)" -ForegroundColor White
        Write-Host "  stopall   - Stop all non-production apps" -ForegroundColor White
        Write-Host "  costs     - Show current cost breakdown" -ForegroundColor White
        Write-Host ""
        Write-Host "Available apps:" -ForegroundColor Yellow
        foreach ($key in $Apps.Keys) {
            Write-Host "  $key -> $($Apps[$key])" -ForegroundColor White
        }
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Yellow
        Write-Host "  .\heroku-manage.ps1 status" -ForegroundColor White
        Write-Host "  .\heroku-manage.ps1 start gazi" -ForegroundColor White
        Write-Host "  .\heroku-manage.ps1 stop working" -ForegroundColor White
        Write-Host "  .\heroku-manage.ps1 stopall" -ForegroundColor White
        Write-Host "  .\heroku-manage.ps1 costs" -ForegroundColor White
    }
}