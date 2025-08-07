"""
Test production-ready authentication setup
"""
import asyncio
from app.services.auth_service import auth_service
from app.services.cosmos_service import CosmosService
from app.services.openai_service import OpenAIService

async def test_production_auth():
    """Test the production authentication setup"""
    print("=== Production Authentication Test ===")
    print(f"Production mode detected: {auth_service.is_production}")
    print()
    
    # Test Cosmos DB service
    print("Testing Cosmos DB service...")
    cosmos_service = CosmosService()
    
    try:
        success = await cosmos_service.check_connection()
        print(f"Cosmos DB connection: {'✅ Success' if success else '❌ Failed'}")
    except Exception as e:
        print(f"Cosmos DB connection: ❌ Error - {e}")
    finally:
        await cosmos_service.close()
    
    print()
    
    # Test OpenAI service  
    print("Testing OpenAI service...")
    openai_service = OpenAIService()
    
    try:
        success = await openai_service.check_connection()
        print(f"OpenAI connection: {'✅ Success' if success else '❌ Failed'}")
    except Exception as e:
        print(f"OpenAI connection: ❌ Error - {e}")
    
    print()
    print("=== Authentication Details ===")
    endpoint, key = auth_service.get_cosmos_auth()
    print(f"Cosmos endpoint: {endpoint}")
    print(f"Cosmos using key: {'Yes' if key else 'No (Managed Identity)'}")
    
    endpoint, key = auth_service.get_openai_auth()
    print(f"OpenAI endpoint: {endpoint}")
    print(f"OpenAI using key: {'Yes' if key else 'No (Managed Identity)'}")

if __name__ == "__main__":
    asyncio.run(test_production_auth())
