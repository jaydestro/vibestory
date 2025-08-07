"""
Test Cosmos DB connection
"""
import asyncio
import os
from dotenv import load_dotenv
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey

async def test_cosmos_connection():
    """Test the Cosmos DB connection"""
    # Load environment variables
    load_dotenv()
    
    endpoint = os.getenv("COSMOS_DB_ENDPOINT")
    key = os.getenv("COSMOS_DB_KEY")
    database_name = os.getenv("COSMOS_DB_DATABASE", "vibestory")
    container_name = os.getenv("COSMOS_DB_CONTAINER", "stories")
    
    print(f"Testing connection to: {endpoint}")
    print(f"Database: {database_name}")
    print(f"Container: {container_name}")
    print(f"Key (first 10 chars): {key[:10]}...")
    
    try:
        # Create client
        client = CosmosClient(
            url=endpoint,
            credential=key,
            consistency_level='Session'
        )
        
        print("✅ Client created successfully")
        
        # Get or create database
        database = await client.create_database_if_not_exists(id=database_name)
        print(f"✅ Database '{database_name}' ready")
        
        # Get or create container
        container = await database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/id"),
            offer_throughput=400
        )
        print(f"✅ Container '{container_name}' ready")
        
        # Test a simple operation
        test_item = {
            "id": "test-connection",
            "title": "Test Story",
            "content": "This is a test story to verify connection",
            "genre": "test",
            "word_count": 10,
            "created_at": "2025-08-06T21:35:00Z"
        }
        
        # Try to upsert the test item
        result = await container.upsert_item(body=test_item)
        print(f"✅ Test item created/updated: {result['id']}")
        
        # Try to read it back
        read_item = await container.read_item(
            item="test-connection",
            partition_key="test-connection"
        )
        print(f"✅ Test item read back: {read_item['title']}")
        
        # Clean up test item
        await container.delete_item(
            item="test-connection",
            partition_key="test-connection"
        )
        print("✅ Test item cleaned up")
        
        await client.close()
        print("✅ Connection test successful!")
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cosmos_connection())
