"""
Pydantic Models for VibeStory API
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class StoryRequest(BaseModel):
    """Request model for text-based story generation"""
    prompt: str = Field(..., description="The story prompt or theme")
    genre: Optional[str] = Field("general", description="Story genre")
    length: Optional[str] = Field("short", description="Story length (short, medium, long)")
    tone: Optional[str] = Field("neutral", description="Story tone")


class ImageStoryRequest(BaseModel):
    """Request model for image-to-story generation"""
    image_description: Optional[str] = Field(None, description="Optional description to add context")
    theme: Optional[str] = Field("general", description="Story theme (horror, sci-fi, kids, romance, mystery, adventure)")
    length: Optional[str] = Field("short", description="Story length (short, medium, long)")
    tone: Optional[str] = Field("creative", description="Story tone")


class Story(BaseModel):
    """Story model"""
    id: str = Field(..., description="Unique story identifier")
    title: str = Field(..., description="Story title")
    content: str = Field(..., description="Story content")
    genre: str = Field(..., description="Story genre/theme")
    prompt: Optional[str] = Field(None, description="Original text prompt (if any)")
    image_filename: Optional[str] = Field(None, description="Uploaded image filename (if any)")
    image_description: Optional[str] = Field(None, description="User-provided image description")
    story_type: str = Field(..., description="Type of story: 'text' or 'image'")
    created_at: datetime = Field(..., description="Creation timestamp")
    word_count: int = Field(..., description="Number of words in the story")


class StoryResponse(BaseModel):
    """Response model for story operations"""
    success: bool = Field(..., description="Operation success status")
    story: Optional[Story] = Field(None, description="The generated or retrieved story")
    message: Optional[str] = Field(None, description="Status message")


class StoriesListResponse(BaseModel):
    """Response model for listing stories"""
    success: bool = Field(..., description="Operation success status")
    stories: List[Story] = Field(..., description="List of stories")
    total: int = Field(..., description="Total number of stories")
    message: Optional[str] = Field(None, description="Status message")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    services: dict = Field(..., description="Individual service statuses")
