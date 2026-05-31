param(
    [switch]$NoFrontend
)

Write-Host "=== BorderVision v2.0 Setup ===" -ForegroundColor Cyan

Write-Host "[1/3] Creating Python virtual environment..." -ForegroundColor Yellow
python -m venv .venv
if (-not $?) { Write-Host "Failed to create venv" -ForegroundColor Red; exit 1 }

$venvPath = if ($IsWindows -or $env:OS) { ".\.venv\Scripts\Activate.ps1" } else { ".venv/bin/activate" }

Write-Host "[2/3] Installing Python dependencies..." -ForegroundColor Yellow
. $venvPath
pip install -e . 2>&1 | Out-Null
if (-not $?) { Write-Host "pip install failed" -ForegroundColor Red; exit 1 }
python -c "from ultralytics import YOLO; YOLO('yolov8s')" 2>&1 | Out-Null
Write-Host "  YOLOv8s model cached" -ForegroundColor Green

Write-Host "[3/3] Setting up frontend..." -ForegroundColor Yellow
if (-not $NoFrontend) {
    Set-Location frontend
    npm install 2>&1 | Out-Null
    if (-not $?) { Write-Host "npm install failed" -ForegroundColor Red; exit 1 }
    Set-Location ..
}

Write-Host "=== Setup complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick start:"
Write-Host "  . .venv/Scripts/Activate.ps1"
Write-Host "  border-vision --camera 0"
Write-Host ""
Write-Host "Or with calibration:"
Write-Host "  border-vision --camera 0 --calibrate"
