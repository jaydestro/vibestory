"""
Story Routes
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
import os
import uuid
from datetime import datetime

from app.models import StoryRequest, StoryResponse, StoriesListResponse, Story, ImageStoryRequest
from app.services.cosmos_service import CosmosService
from app.services.openai_service import OpenAIService

router = APIRouter()

@router.post("/stories", response_model=StoryResponse)
async def generate_story(request: StoryRequest):
    """Generate a new story using Azure OpenAI"""
    try:
        # Initialize services
        openai_service = OpenAIService()
        cosmos_service = CosmosService()
        
        # Generate story content
        story_content = await openai_service.generate_story(
            prompt=request.prompt,
            genre=request.genre,
            length=request.length,
            tone=request.tone
        )
        
        # Generate title
        title = await openai_service.generate_title(story_content)
        
        # Create story object
        story = Story(
            id=str(uuid.uuid4()),
            title=title,
            content=story_content,
            genre=request.genre or "general",
            prompt=request.prompt,
            image_filename=None,
            image_description=None,
            story_type="text",
            created_at=datetime.utcnow(),
            word_count=len(story_content.split())
        )
        
        # Save to Cosmos DB
        await cosmos_service.save_story(story)
        
        return StoryResponse(
            success=True,
            story=story,
            message="Story generated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate story: {str(e)}"
        )

@router.post("/stories/image", response_model=StoryResponse)
async def generate_story_from_image(
    image: UploadFile = File(...),
    theme: str = Form("general"),
    length: str = Form("short"),
    tone: str = Form("creative"),
    image_description: Optional[str] = Form(None)
):
    """Generate a story from an uploaded image"""
    try:
        # Validate image file
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Please upload a valid image file"
            )
        
        # Generate unique filename
        file_extension = image.filename.split('.')[-1] if image.filename and '.' in image.filename else 'jpg'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Ensure uploads directory exists
        uploads_dir = "static/uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save uploaded image
        image_path = os.path.join(uploads_dir, unique_filename)
        with open(image_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        # Initialize services
        openai_service = OpenAIService()
        cosmos_service = CosmosService()
        
        # Generate story from image
        story_content = await openai_service.generate_story_from_image(
            image_path=image_path,
            theme=theme,
            length=length,
            tone=tone,
            additional_context=image_description or ""
        )
        
        # Generate title
        title = await openai_service.generate_title(story_content)
        
        # Create story object
        story = Story(
            id=str(uuid.uuid4()),
            title=title,
            content=story_content,
            genre=theme,
            prompt=None,
            image_filename=unique_filename,
            image_description=image_description,
            story_type="image",
            created_at=datetime.utcnow(),
            word_count=len(story_content.split())
        )
        
        # Save to Cosmos DB
        await cosmos_service.save_story(story)
        
        return StoryResponse(
            success=True,
            story=story,
            message="Story generated from image successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up uploaded file if story generation failed
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate story from image: {str(e)}"
        )

@router.get("/stories", response_model=StoriesListResponse)
async def get_stories(limit: int = 10, offset: int = 0):
    """Get list of stories"""
    try:
        cosmos_service = CosmosService()
        stories, total = await cosmos_service.get_stories(limit=limit, offset=offset)
        
        return StoriesListResponse(
            success=True,
            stories=stories,
            total=total,
            message="Stories retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve stories: {str(e)}"
        )

@router.get("/stories/{story_id}", response_model=StoryResponse)
async def get_story(story_id: str):
    """Get a specific story by ID"""
    try:
        cosmos_service = CosmosService()
        story = await cosmos_service.get_story(story_id)
        
        if not story:
            raise HTTPException(
                status_code=404,
                detail="Story not found"
            )
        
        return StoryResponse(
            success=True,
            story=story,
            message="Story retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve story: {str(e)}"
        )
