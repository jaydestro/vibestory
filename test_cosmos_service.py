"""
Test the updated Cosmos service
"""
import asyncio
from app.services.cosmos_service import CosmosService
from app.models import Story
from datetime import datetime
import uuid

async def test_updated_cosmos_service():
    """Test the updated Cosmos service"""
    print("Testing updated Cosmos service...")
    
    service = CosmosService()
    
    try:
        # Test connection
        print("Testing connection...")
        is_connected = await service.check_connection()
        print(f"Connection status: {'✅ Connected' if is_connected else '❌ Failed'}")
        
        if not is_connected:
            return
        
        # Test saving a story
        print("Testing save story...")
        test_story = Story(
            id=str(uuid.uuid4()),
            title="Test Story",
            content="This is a test story to verify the service works.",
            genre="test",
            story_type="text",
            prompt="Test prompt",
            word_count=10,
            created_at=datetime.now()
        )
        
        await service.save_story(test_story)
        print(f"✅ Story saved: {test_story.id}")
        
        # Test retrieving stories
        print("Testing get stories...")
        stories, total = await service.get_stories(limit=1)
        print(f"✅ Retrieved {len(stories)} stories, total: {total}")
        
        if stories:
            print(f"Latest story: {stories[0].title}")
        
        # Test retrieving specific story
        print("Testing get specific story...")
        retrieved_story = await service.get_story(test_story.id)
        if retrieved_story:
            print(f"✅ Retrieved story: {retrieved_story.title}")
        else:
            print("❌ Could not retrieve story")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.close()
        print("Service closed")

if __name__ == "__main__":
    asyncio.run(test_updated_cosmos_service())
