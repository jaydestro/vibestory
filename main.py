#!/usr/bin/env python3
"""
VibeStory Application Entry Point
Run this file to start the application without using virtual environments
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is supported"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required packages are available"""
    print("📦 Checking dependencies...")
    try:
        import fastapi
        import uvicorn
        import openai
        import azure.cosmos
        import pydantic
        import dotenv
        print("✅ All dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def check_environment():
    """Check if environment variables are configured"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("Please copy .env.example to .env and configure your Azure credentials")
        return False
    
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY", 
        "COSMOS_DB_ENDPOINT",
        "COSMOS_DB_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or "your_" in value.lower():
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or unconfigured environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with actual Azure service credentials")
        return False
    
    print("✅ Environment variables configured")
    return True

def start_application():
    """Start the FastAPI application"""
    port = int(os.getenv("PORT", 8000))
    
    print(f"\n🚀 Starting VibeStory application...")
    print(f"📱 Application will be available at: http://localhost:{port}")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        # Start the application using uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped")
    except FileNotFoundError:
        print("❌ uvicorn not found. Please install dependencies first.")
        return False
    
    return True

def main():
    """Main function"""
    print("🎨 VibeStory - AI Story Generator")
    print("=" * 50)
    print("Running without virtual environment")
    print()
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check environment configuration
    if not check_environment():
        print("\n💡 To get started:")
        print("1. Copy .env.example to .env")
        print("2. Configure your Azure OpenAI and Cosmos DB credentials")
        print("3. Run this script again")
        return 1
    
    # Start the application
    success = start_application()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
