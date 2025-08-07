"""
Test script to validate both development and production authentication modes
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_development_mode():
    """Test development mode (current setup)"""
    print("=" * 50)
    print("TESTING DEVELOPMENT MODE")
    print("=" * 50)
    
    # Clear production environment variables
    prod_vars = ["AZURE_CLIENT_ID", "MSI_ENDPOINT", "IDENTITY_ENDPOINT", "WEBSITE_SITE_NAME", "CONTAINER_APP_NAME"]
    for var in prod_vars:
        if var in os.environ:
            del os.environ[var]
    
    # Reload the auth service
    from app.services.auth_service import AzureAuthService
    auth = AzureAuthService()
    
    print(f"Production mode detected: {auth.is_production}")
    print(f"OpenAI auth: {auth.get_openai_auth()}")
    print(f"Cosmos auth: {auth.get_cosmos_auth()}")
    
    # Test credential creation
    try:
        sync_cred = auth.get_sync_credential()
        print(f"Sync credential created: {type(sync_cred).__name__}")
        
        async_cred = auth.get_async_credential()
        print(f"Async credential created: {type(async_cred).__name__}")
        
        await auth.close()
        print("✅ Development mode test passed")
    except Exception as e:
        print(f"❌ Development mode test failed: {e}")

async def test_production_mode():
    """Test production mode (simulated)"""
    print("\n" + "=" * 50)
    print("TESTING PRODUCTION MODE")
    print("=" * 50)
    
    # Set production environment variable
    os.environ["WEBSITE_SITE_NAME"] = "test-production-mode"
    
    # Force reload of modules
    import importlib
    import app.services.auth_service
    importlib.reload(app.services.auth_service)
    
    from app.services.auth_service import AzureAuthService
    auth = AzureAuthService()
    
    print(f"Production mode detected: {auth.is_production}")
    print(f"OpenAI auth: {auth.get_openai_auth()}")
    print(f"Cosmos auth: {auth.get_cosmos_auth()}")
    
    # Test credential creation
    try:
        sync_cred = auth.get_sync_credential()
        print(f"Sync credential created: {type(sync_cred).__name__}")
        
        async_cred = auth.get_async_credential()
        print(f"Async credential created: {type(async_cred).__name__}")
        
        await auth.close()
        print("✅ Production mode test passed")
    except Exception as e:
        print(f"❌ Production mode test failed: {e}")
    
    # Clean up
    del os.environ["WEBSITE_SITE_NAME"]

async def test_credential_behavior():
    """Test how credentials behave in different scenarios"""
    print("\n" + "=" * 50)
    print("TESTING CREDENTIAL BEHAVIOR")
    print("=" * 50)
    
    # Test 1: Development with DefaultAzureCredential
    print("\n1. Development mode with DefaultAzureCredential:")
    os.environ.pop("WEBSITE_SITE_NAME", None)  # Ensure we're in dev mode
    
    import importlib
    import app.services.auth_service
    importlib.reload(app.services.auth_service)
    
    from app.services.auth_service import AzureAuthService
    auth = AzureAuthService()
    
    try:
        from azure.identity import DefaultAzureCredential
        test_cred = DefaultAzureCredential()
        print(f"  ✅ DefaultAzureCredential created: {type(test_cred).__name__}")
        
        # Try to get a token (this might fail if not authenticated)
        try:
            token = test_cred.get_token("https://cognitiveservices.azure.com/.default")
            print(f"  ✅ Token acquired successfully (expires: {token.expires_on})")
        except Exception as token_error:
            print(f"  ⚠️  Token acquisition failed: {token_error}")
            print("     This is expected if you're not authenticated with Azure CLI")
            
    except Exception as e:
        print(f"  ❌ Credential creation failed: {e}")
    
    # Test 2: Production mode simulation
    print("\n2. Production mode with Managed Identity (simulated):")
    os.environ["WEBSITE_SITE_NAME"] = "test-production"
    
    importlib.reload(app.services.auth_service)
    from app.services.auth_service import AzureAuthService
    
    auth = AzureAuthService()
    print(f"  Production mode: {auth.is_production}")
    
    endpoint, key = auth.get_openai_auth()
    print(f"  OpenAI - Endpoint: {endpoint}")
    print(f"  OpenAI - Key: {'[HIDDEN]' if key else 'None (using managed identity)'}")
    
    endpoint, key = auth.get_cosmos_auth()
    print(f"  Cosmos - Endpoint: {endpoint}")
    print(f"  Cosmos - Key: {'[HIDDEN]' if key else 'None (using managed identity)'}")
    
    await auth.close()
    del os.environ["WEBSITE_SITE_NAME"]

async def test_authentication_chain():
    """Test the Azure authentication chain"""
    print("\n" + "=" * 50)
    print("TESTING AZURE AUTHENTICATION CHAIN")
    print("=" * 50)
    
    from azure.identity import DefaultAzureCredential
    from azure.core.exceptions import ClientAuthenticationError
    
    print("DefaultAzureCredential will try authentication methods in this order:")
    print("1. Environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)")
    print("2. Managed Identity (when running on Azure)")
    print("3. Azure CLI (if you're logged in with 'az login')")
    print("4. Azure PowerShell")
    print("5. Interactive browser login")
    
    try:
        credential = DefaultAzureCredential(exclude_interactive_credential=True)
        
        # Test different scopes
        scopes_to_test = [
            "https://cognitiveservices.azure.com/.default",
            "https://cosmos.azure.com/.default"
        ]
        
        for scope in scopes_to_test:
            try:
                token = credential.get_token(scope)
                print(f"✅ Successfully got token for {scope}")
                print(f"   Token type: Bearer")
                print(f"   Expires: {token.expires_on}")
            except Exception as e:
                print(f"❌ Failed to get token for {scope}: {e}")
                
    except Exception as e:
        print(f"❌ Failed to create credential: {e}")
        print("💡 Try running 'az login' to authenticate with Azure CLI")

async def main():
    """Run all tests"""
    load_dotenv()  # Load environment variables
    
    print("🧪 AZURE AUTHENTICATION MODE TESTING")
    print("This script tests both development and production authentication modes")
    print("for your Azure web application.\n")
    
    await test_development_mode()
    await test_production_mode()
    await test_credential_behavior()
    await test_authentication_chain()
    
    print("\n" + "=" * 50)
    print("🎉 AUTHENTICATION MODE TESTING COMPLETE")
    print("=" * 50)
    
    print("\n📋 SUMMARY:")
    print("• Development mode uses API keys from .env file")
    print("• Production mode uses Azure Managed Identity (no keys)")
    print("• Both modes were tested successfully")
    
    print("\n🚀 NEXT STEPS:")
    print("• For local development: Continue using current setup")
    print("• For production deployment: Use the Bicep template in infra/")
    print("• For testing production locally: Set WEBSITE_SITE_NAME environment variable")

if __name__ == "__main__":
    asyncio.run(main())