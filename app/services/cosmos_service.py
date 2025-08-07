"""
Azure Cosmos DB Service
Production-ready with Managed Identity support
"""
import os
from dotenv import load_dotenv
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from app.models import Story
from app.services.auth_service import auth_service
from typing import List, Tuple, Optional
from datetime import datetime

# Load environment variables at module level
load_dotenv()


class CosmosService:
    """Service for interacting with Azure Cosmos DB"""
    
    def __init__(self):
        # Get authentication info from auth service
        self.endpoint, self.key = auth_service.get_cosmos_auth()
        self.database_name = os.getenv("COSMOS_DB_DATABASE", "vibestory")
        self.container_name = os.getenv("COSMOS_DB_CONTAINER", "stories")
        
        # Clean up environment variables if they exist
        if self.endpoint:
            self.endpoint = self.endpoint.strip().strip('"').strip("'")
        if self.key:
            self.key = self.key.strip().strip('"').strip("'")
        
        # Don't initialize client in __init__ to avoid session issues
        self.client = None
        self.database = None
        self.container = None
    
    async def _get_client(self):
        """Get or create Cosmos client with appropriate authentication"""
        if not self.client:
            if auth_service.is_production:
                # Use Managed Identity in production
                credential = auth_service.get_async_credential()
                self.client = CosmosClient(
                    url=self.endpoint, 
                    credential=credential
                )
            else:
                # Use key-based authentication in development
                self.client = CosmosClient(
                    url=self.endpoint, 
                    credential=self.key
                )
        return self.client
    
    async def _ensure_database_and_container(self):
        """Ensure database and container exist"""
        try:
            client = await self._get_client()
            
            if not self.database:
                self.database = await client.create_database_if_not_exists(
                    id=self.database_name
                )
            
            if not self.container:
                self.container = await self.database.create_container_if_not_exists(
                    id=self.container_name,
                    partition_key=PartitionKey(path="/id"),
                    offer_throughput=400
                )
        except Exception as e:
            print(f"Error initializing database/container: {e}")
            raise
    
    async def check_connection(self) -> bool:
        """Check if Cosmos DB is accessible"""
        try:
            await self._ensure_database_and_container()
            return True
        except Exception:
            return False
    
    async def save_story(self, story: Story) -> None:
        """Save a story to Cosmos DB"""
        try:
            await self._ensure_database_and_container()
            
            # Convert story to dict for Cosmos DB
            story_dict = {
                "id": story.id,
                "title": story.title,
                "content": story.content,
                "genre": story.genre,
                "prompt": story.prompt,
                "image_filename": story.image_filename,
                "image_description": story.image_description,
                "story_type": story.story_type,
                "created_at": story.created_at.isoformat(),
                "word_count": story.word_count
            }
            
            # Use upsert instead of create to handle duplicates
            await self.container.upsert_item(body=story_dict)
            
        except Exception as e:
            print(f"Cosmos DB save error: {e}")
            raise Exception(f"Failed to save story: {str(e)}")
    
    async def get_story(self, story_id: str) -> Optional[Story]:
        """Get a story by ID"""
        try:
            await self._ensure_database_and_container()
            
            item = await self.container.read_item(
                item=story_id,
                partition_key=story_id
            )
            
            return Story(
                id=item["id"],
                title=item["title"],
                content=item["content"],
                genre=item["genre"],
                prompt=item.get("prompt"),
                image_filename=item.get("image_filename"),
                image_description=item.get("image_description"),
                story_type=item.get("story_type", "text"),
                created_at=datetime.fromisoformat(item["created_at"]),
                word_count=item["word_count"]
            )
            
        except Exception:
            return None
    
    async def get_stories(self, limit: int = 10, offset: int = 0) -> Tuple[List[Story], int]:
        """Get a list of stories with pagination"""
        try:
            await self._ensure_database_and_container()
            
            # Query for total count
            count_query = "SELECT VALUE COUNT(1) FROM c"
            count_items = [item async for item in self.container.query_items(
                query=count_query,
                partition_key=None
            )]
            total = count_items[0] if count_items else 0
            
            # Query for stories with pagination
            query = f"SELECT * FROM c ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
            items = [item async for item in self.container.query_items(
                query=query,
                partition_key=None
            )]
            
            stories = []
            for item in items:
                story = Story(
                    id=item["id"],
                    title=item["title"],
                    content=item["content"],
                    genre=item["genre"],
                    prompt=item.get("prompt"),
                    image_filename=item.get("image_filename"),
                    image_description=item.get("image_description"),
                    story_type=item.get("story_type", "text"),
                    created_at=datetime.fromisoformat(item["created_at"]),
                    word_count=item["word_count"]
                )
                stories.append(story)
            
            return stories, total
            
        except Exception as e:
            raise Exception(f"Failed to retrieve stories: {str(e)}")
    
    async def close(self):
        """Close the Cosmos client and auth service"""
        if self.client:
            await self.client.close()
            self.client = None
            self.database = None
            self.container = None
        
        # Close auth service if in production
        if auth_service.is_production:
            await auth_service.close()
