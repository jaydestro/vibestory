"""
Test Cosmos DB connection with synchronous client
"""
import os
from dotenv import load_dotenv
from azure.cosmos import CosmosClient, PartitionKey

def test_cosmos_sync():
    """Test the Cosmos DB connection with sync client"""
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
            credential=key
        )
        
        print("✅ Client created successfully")
        
        # Get database
        database = client.get_database_client(database_name)
        print(f"✅ Database client ready")
        
        # Get container
        container = database.get_container_client(container_name)
        print(f"✅ Container client ready")
        
        # Test a simple operation
        test_item = {
            "id": "test-sync-connection",
            "title": "Test Story Sync",
            "content": "This is a sync test story",
            "genre": "test",
            "word_count": 8,
            "created_at": "2025-08-06T21:40:00Z"
        }
        
        # Try to upsert the test item
        result = container.upsert_item(body=test_item)
        print(f"✅ Test item created/updated: {result['id']}")
        
        # Try to read it back
        read_item = container.read_item(
            item="test-sync-connection",
            partition_key="test-sync-connection"
        )
        print(f"✅ Test item read back: {read_item['title']}")
        
        # Clean up test item
        container.delete_item(
            item="test-sync-connection",
            partition_key="test-sync-connection"
        )
        print("✅ Test item cleaned up")
        
        print("✅ Sync connection test successful!")
        
    except Exception as e:
        print(f"❌ Sync connection test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cosmos_sync()
