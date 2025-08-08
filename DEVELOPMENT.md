# Development Guide - Python Virtual Environment Setup

This guide explains how to develop and run the VibeStory application using Python virtual environments.

## Why Use Virtual Environment?

- **Dependency Isolation**: Prevents conflicts between project dependencies
- **Reproducible Builds**: Ensures consistent package versions
- **Clean Development**: Keeps global Python installation clean
- **Team Consistency**: All developers use the same package versions
- **Deployment Safety**: Matches production environment more closely

## Prerequisites

1. **Python 3.8 or higher**
2. **pip** (included with Python)
3. **Azure subscription** with:
   - Azure OpenAI service
   - Azure Cosmos DB account

## Setup Instructions

### 1. Create Virtual Environment

```powershell
# Navigate to project directory
cd c:\Users\jagord\Downloads\CosmosDBDemoApp\vibestory

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# On Windows (Command Prompt)
venv\Scripts\activate.bat

# On Linux/Mac
source venv/bin/activate
```

### 2. Verify Virtual Environment

```powershell
# Should show path to virtual environment Python
where python

# Should show virtual environment location
pip --version
```

### 3. Install Dependencies

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt
```

### 4. Configure Environment

```powershell
# Copy environment template
copy .env.example .env
```

Edit `.env` with your Azure credentials:
```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_KEY=your_azure_openai_key_here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01

# Azure Cosmos DB Configuration
COSMOS_DB_URL=https://your-cosmosdb-account.documents.azure.com/
COSMOS_DB_KEY=your_cosmos_db_key_here
COSMOS_DB_NAME=vibestory
COSMOS_CONTAINER_NAME=stories
```

### 5. Test Setup

```powershell
# Test environment setup
python -c "import fastapi, uvicorn, openai, azure.cosmos; print('All dependencies installed successfully!')"
```

### 6. Run Application

```powershell
# Using the run script
python run.py

# Or directly with uvicorn
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Virtual Environment Management

### Daily Workflow

```powershell
# Activate environment (do this every time you work on the project)
.\venv\Scripts\Activate.ps1

# Work on your code...
python run.py

# Deactivate when done (optional)
deactivate
```

### Adding New Dependencies

```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1

# Install new package
pip install new-package-name

# Update requirements file
pip freeze > requirements.txt
```

### Updating Dependencies

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Update all packages
pip install --upgrade -r requirements.txt

# Or update specific package
pip install --upgrade fastapi
```

## VS Code Configuration

### Python Interpreter Setup

1. Open VS Code in project directory
2. Press `Ctrl+Shift+P`
3. Type "Python: Select Interpreter"
4. Choose the interpreter from your virtual environment:
   - `.\venv\Scripts\python.exe` (Windows)
   - `./venv/bin/python` (Linux/Mac)

### VS Code Settings

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black"
}
```

### Running in VS Code

1. Open integrated terminal (Ctrl+`)
2. Virtual environment should activate automatically
3. Run: `python run.py`

## Troubleshooting

### Virtual Environment Issues

```powershell
# If activation fails, try enabling script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Recreate virtual environment if corrupted
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Package Installation Issues

```powershell
# Clear pip cache
pip cache purge

# Reinstall packages
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### Import Errors

```powershell
# Verify virtual environment is activated
where python
# Should show: c:\Users\jagord\Downloads\CosmosDBDemoApp\vibestory\venv\Scripts\python.exe

# Verify packages are installed
pip list
```

## Benefits of Virtual Environment

1. **Isolation**: Each project has its own dependencies
2. **Version Control**: Lock specific package versions
3. **Clean Uninstall**: Just delete the venv folder
4. **Multiple Python Versions**: Different projects can use different Python versions
5. **Production Matching**: Environment matches deployment containers

## Deployment Considerations

### For Development
Always use virtual environment for consistent dependency management.

### For Azure Deployment
The deployed container will have its own isolated environment, similar to your local virtual environment.

### For Docker
Virtual environment isn't needed inside containers, but helps ensure consistent requirements.txt generation.

## Quick Reference

```powershell
# Create venv
python -m venv venv

# Activate venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run app
python run.py

# Deactivate venv
deactivate
```
