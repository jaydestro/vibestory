"""
Debug environment variables
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Environment Variables Debug:")
print(f"COSMOS_DB_ENDPOINT: {os.getenv('COSMOS_DB_ENDPOINT')}")
print(f"COSMOS_DB_KEY type: {type(os.getenv('COSMOS_DB_KEY'))}")
print(f"COSMOS_DB_KEY length: {len(os.getenv('COSMOS_DB_KEY') or '')}")
print(f"COSMOS_DB_KEY preview: {os.getenv('COSMOS_DB_KEY')[:10] if os.getenv('COSMOS_DB_KEY') else 'None'}...")

# Test Azure Cosmos client directly
from azure.cosmos.aio import CosmosClient

async def test_direct_client():
    endpoint = os.getenv('COSMOS_DB_ENDPOINT')
    key = os.getenv('COSMOS_DB_KEY')
    
    print(f"\nDirect client test:")
    print(f"Using endpoint: {endpoint}")
    print(f"Using key type: {type(key)}")
    
    try:
        client = CosmosClient(url=endpoint, credential=key)
        print("✅ Client created successfully")
        await client.close()
        print("✅ Client closed successfully")
    except Exception as e:
        print(f"❌ Client creation failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_direct_client())
