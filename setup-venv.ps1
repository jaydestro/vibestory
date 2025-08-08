#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Set up Python virtual environment for VibeStory

.DESCRIPTION
    This script creates a virtual environment and installs all dependencies for the VibeStory project.
#>

Write-Host "🐍 Setting up Python Virtual Environment for VibeStory" -ForegroundColor Cyan

# Check if Python is installed
if (!(Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Check Python version
$pythonVersion = python --version
Write-Host "✅ Found $pythonVersion" -ForegroundColor Green

# Remove existing virtual environment if it exists
if (Test-Path "venv") {
    Write-Host "🗑️  Removing existing virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force venv
}

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Green
python -m venv venv

if (!(Test-Path "venv")) {
    Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "⬆️  Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Green
pip install -r requirements.txt

# Verify installation
Write-Host "✅ Verifying installation..." -ForegroundColor Green
python -c "import fastapi, uvicorn, openai, azure.cosmos; print('All dependencies installed successfully!')"

Write-Host "`n🎉 Virtual environment setup complete!" -ForegroundColor Green
Write-Host "To activate the environment in the future, run:" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "`nTo run the application:" -ForegroundColor Yellow
Write-Host "  python run.py" -ForegroundColor Cyan
