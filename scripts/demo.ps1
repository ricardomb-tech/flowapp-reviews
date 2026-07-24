# Demo automatizada — FlowApp Reviews (Reto 1 EPAM)
# Ejecutar desde la raíz del proyecto: .\scripts\demo.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "`n=== FlowApp Reviews — Demo ===" -ForegroundColor Cyan

# 1. Dataset
$Official = Join-Path $Root "data\resenas_flowapp.csv"
$Sample = Join-Path $Root "data\reviews_sample.csv"

if (-not (Test-Path $Official)) {
    Write-Host "[1/4] Dataset oficial no encontrado. Generando muestra sintetica..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path (Join-Path $Root "data") | Out-Null
    python scripts/generate_sample_data.py $Sample
    $Dataset = $Sample
} else {
    Write-Host "[1/4] Usando dataset oficial: resenas_flowapp.csv" -ForegroundColor Green
    $Dataset = $Official
}

# 2. Pipeline
Write-Host "[2/4] Ejecutando pipeline..." -ForegroundColor Cyan
python -m flowapp_reviews $Dataset

# 3. Informe
Write-Host "`n[3/4] Generando informe Markdown..." -ForegroundColor Cyan
$OutDir = Join-Path $Root "output"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Report = Join-Path $OutDir "informe_flowapp.md"
python -m flowapp_reviews $Dataset -f markdown -o $Report
Write-Host "Informe escrito en: $Report" -ForegroundColor Green

# 4. Tests
Write-Host "`n[4/4] Corriendo suite de pruebas..." -ForegroundColor Cyan
python -m pytest --cov --cov-report=term-missing -q

Write-Host "`n=== Demo completada ===" -ForegroundColor Green
