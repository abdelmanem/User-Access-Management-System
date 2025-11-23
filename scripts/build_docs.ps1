# Build MkDocs documentation for production (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Building MkDocs Documentation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if mkdocs is installed
try {
    $mkdocsVersion = mkdocs --version 2>&1
    Write-Host "MkDocs version: $mkdocsVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: mkdocs is not installed" -ForegroundColor Red
    Write-Host "Install it with: pip install mkdocs-material" -ForegroundColor Yellow
    exit 1
}

# Build documentation
Write-Host "`nBuilding documentation..." -ForegroundColor Yellow
mkdocs build --clean

# Verify build
if (-not (Test-Path "site")) {
    Write-Host "Error: site directory was not created" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Documentation built successfully!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Output directory: site/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test locally: mkdocs serve" -ForegroundColor White
Write-Host "2. Deploy to production (see doc/DEPLOYMENT.md)" -ForegroundColor White
Write-Host ""

