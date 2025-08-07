#!/usr/bin/env python3
"""
Quick test script to verify the VibeStory application setup
Run this to test if everything is working without starting the full server
"""

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn imported successfully")
    except ImportError as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        from openai import AsyncAzureOpenAI
        print("✅ Azure OpenAI imported successfully")
    except ImportError as e:
        print(f"❌ Azure OpenAI import failed: {e}")
        return False
    
    try:
        from azure.cosmos.aio import CosmosClient
        print("✅ Azure Cosmos DB imported successfully")
    except ImportError as e:
        print(f"❌ Azure Cosmos DB import failed: {e}")
        return False
    
    try:
        from app.models import Story, StoryRequest
        print("✅ App models imported successfully")
    except ImportError as e:
        print(f"❌ App models import failed: {e}")
        return False
    
    return True

def test_app_creation():
    """Test FastAPI app creation"""
    print("\nTesting app creation...")
    
    try:
        from app.main import app
        print(f"✅ FastAPI app created successfully")
        print(f"   App title: {app.title}")
        print(f"   App version: {app.version}")
        return True
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 VibeStory - Setup Test")
    print("=" * 40)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test app creation
    if not test_app_creation():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All tests passed! Your setup is working correctly.")
        print("\nNext steps:")
        print("1. Configure your .env file with Azure credentials")
        print("2. Run: python main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
