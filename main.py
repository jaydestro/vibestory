#!/usr/bin/env python3
"""
VibeStory Application Entry Point
Run this file to start the application without using virtual environments
"""

import os
import sys
import uuid
import json
import re
import logging
import traceback
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from openai import AzureOpenAI

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")

# Create FastAPI app
app = FastAPI(title="VibeStory", description="AI Story Generator")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Global variables for Azure clients
openai_client = None
container = None
cosmos_client = None

# Initialize Azure OpenAI client
try:
    openai_client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
    )
    logger.info("Azure OpenAI client initialized")
except Exception as e:
    logger.error(f"Failed to initialize Azure OpenAI client: {e}")

# Initialize Azure Cosmos DB client
try:
    from azure.cosmos import CosmosClient
    cosmos_endpoint = os.getenv("COSMOS_DB_URL")
    cosmos_key = os.getenv("COSMOS_DB_KEY")
    cosmos_db = os.getenv("COSMOS_DB_NAME")
    cosmos_container_name = os.getenv("COSMOS_CONTAINER_NAME")

    if cosmos_endpoint and cosmos_key and cosmos_db and cosmos_container_name:
        cosmos_client = CosmosClient(cosmos_endpoint, credential=cosmos_key)
        database = cosmos_client.get_database_client(cosmos_db)
        container = database.get_container_client(cosmos_container_name)
        logger.info("Cosmos DB client initialized")
    else:
        logger.warning("Missing Cosmos DB configuration. Database features will be disabled.")
except Exception as e:
    logger.error(f"Failed to initialize Cosmos DB client: {e}")

# Define request models
class StoryCreateRequest(BaseModel):
    prompt: str
    genre: str = "general"
    tone: str = "neutral"
    length: str = "medium"

# Helper functions for story generation
_GENERIC_TITLES = {"untitled", "story", "untitled story", "the story"}

def _synthesize_title(prompt: str, content: str, genre: str) -> str:
    """Generate a fallback title when none is present."""
    if prompt and len(prompt) < 60:
        return f"{prompt.strip()}"
    elif content:
        words = content.split()[:10]
        if len(words) >= 3:
            return " ".join(words) + "..."
    return f"{genre.capitalize()} Story"

def normalize_story_output(raw: str, prompt: str, genre: str) -> tuple[str, str]:
    if not raw:
        return _synthesize_title(prompt, "", genre), ""
    
    txt = raw.strip()
    
    # Remove markdown fences if present
    fence = re.match(r"^```(?:json)?\s*(.+?)\s*```$", txt, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        txt = fence.group(1).strip()
    
    # Try to parse as JSON
    if txt.startswith("{") and txt.endswith("}"):
        try:
            obj = json.loads(txt)
            title = (obj.get("title") or obj.get("story_title") or "").strip()
            body = (obj.get("content") or obj.get("story") or "").strip()
            
            # Ensure we have content
            if not body:
                logger.warning(f"JSON parsed but no content field found: {obj.keys()}")
                body = txt  # Fall back to raw text
            
            # Ensure we have a title
            if not title or title.lower() in _GENERIC_TITLES:
                title = _synthesize_title(prompt, body, genre)
            
            logger.info(f"Successfully parsed JSON story: title='{title[:50]}...', content_len={len(body)}")
            return title, body
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing story JSON: {e}")
    
    # Not JSON, treat as plain text
    lines = [l for l in txt.splitlines() if l.strip()]
    if lines:
        first = lines[0].strip()
        if (len(first) < 100 and
            (first.startswith("#") or first.istitle() or first.lower().startswith(("chapter", "the ")))):
            cleaned = re.sub(r'^#+\s*', '', first)
            remaining = "\n".join(lines[1:]).strip()
            if not cleaned or cleaned.lower() in _GENERIC_TITLES:
                cleaned = _synthesize_title(prompt, remaining or txt, genre)
            return cleaned, (remaining or txt)
    
    return _synthesize_title(prompt, txt, genre), txt

async def generate_story_text(
    prompt: str,
    genre: str = "general",
    tone: str = "neutral",
    length: str = "medium"
) -> str:
    """Generate a story from a text prompt using Azure OpenAI."""
    if not openai_client:
        raise ValueError("OpenAI client not initialized")

    # Configure token limits based on length
    max_tokens = {
        "short": 500,
        "medium": 1000,
        "long": 1800,
    }.get(length, 1000)
    
    # Create a detailed system prompt
    system_prompt = (
        f"You are a creative story writer. Write a {length} {genre} story with a {tone} tone "
        f"based on the prompt provided. Return ONLY JSON with 'title' and 'content'."
    )
    
    # Create the API request
    response = openai_client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.8
    )
    
    # Return the generated content
    return response.choices[0].message.content

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/stories")
async def create_story(req: StoryCreateRequest):
    """Create a story from text prompt using Azure OpenAI"""
    try:
        raw_output = await generate_story_text(
            prompt=req.prompt,
            genre=req.genre,
            tone=req.tone,
            length=req.length
        )
        title, content = normalize_story_output(raw_output, req.prompt, req.genre)
        created_at = datetime.utcnow().isoformat() + "Z"
        word_count = len(content.split())
        story_doc = {
            "id": str(uuid.uuid4()),
            "story_type": "text",
            "prompt": req.prompt,
            "genre": req.genre,
            "tone": req.tone,
            "length": req.length,
            "content": content,
            "title": title,
            "word_count": word_count,
            "created_at": created_at,
        }
        
        # Persist to Cosmos
        if container:
            try:
                container.upsert_item(story_doc)
            except Exception as db_err:
                logger.error(f"Cosmos upsert failed: {db_err}")
        
        return {"success": True, "story": story_doc}
    except Exception as e:
        logger.error(f"Error creating text story: {e}")
        raise HTTPException(status_code=500, detail="Story generation failed")

@app.post("/api/stories/image")
async def create_story_from_image(
    image: UploadFile = File(...),
    image_description: Optional[str] = Form(None),
    theme: str = Form("general"),
    length: str = Form("medium"),
    tone: str = Form("creative"),
):
    """Create a story from uploaded image using Azure OpenAI"""
    try:
        # Save uploaded image
        image_filename = f"{uuid.uuid4()}_{image.filename}"
        save_dir = "static/uploads"
        os.makedirs(save_dir, exist_ok=True)
        image_path = os.path.join(save_dir, image_filename)
        with open(image_path, "wb") as buffer:
            buffer.write(await image.read())

        context = image_description or "an uploaded image"
        prompt = f"Write a {length} {theme} story with a {tone} tone inspired by {context}."
        system_prompt = (
            f"You are a creative story writer. Write a {length} {theme} story with a {tone} tone "
            "based on the image description provided. Return ONLY JSON with 'title' and 'content'."
        )
        response = openai_client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.8
        )
        story_content_raw = response.choices[0].message.content
        title, content = normalize_story_output(story_content_raw, image_description or "", theme)
        created_at = datetime.utcnow().isoformat() + "Z"
        word_count = len(content.split())
        story_doc = {
            "id": str(uuid.uuid4()),
            "story_type": "image",
            "image_filename": image_filename,
            "image_description": image_description,
            "genre": theme,
            "tone": tone,
            "length": length,
            "content": content,
            "title": title,
            "word_count": word_count,
            "created_at": created_at,
        }
        
        # Persist to Cosmos
        if container:
            try:
                container.upsert_item(story_doc)
            except Exception as db_err:
                logger.error(f"Cosmos upsert failed: {db_err}")
        
        return {"success": True, "story": story_doc}
    except Exception as e:
        logger.error(f"Error creating image story: {e}")
        raise HTTPException(status_code=500, detail="Image story generation failed")

@app.get("/api/stories")
async def get_stories(limit: int = 10, skip: int = 0):
    """Get a list of stories from the database."""
    if not container:
        return {"success": True, "stories": []}
    
    try:
        # Create a query with optional pagination
        query = f"SELECT * FROM c ORDER BY c.created_at DESC OFFSET {skip} LIMIT {limit}"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        return {"success": True, "stories": items}
    except Exception as e:
        logger.error(f"Error retrieving stories: {e}")
        return {"success": False, "error": "Failed to retrieve stories"}

@app.delete("/api/stories/{story_id}")
async def delete_story(story_id: str):
    """Delete a story by ID."""
    logger.info(f"DELETE /api/stories/{story_id}")
    
    if not container:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get the story to check if it exists and get image filenames
        try:
            story = container.read_item(item=story_id, partition_key=story_id)
            logger.info(f"Found story to delete: {story.get('title', 'Untitled')}")
        except Exception as e:
            logger.warning(f"Story not found: {e}")
            raise HTTPException(status_code=404, detail="Story not found")
        
        # Delete associated image files if they exist
        deleted_files = []
        
        # Delete uploaded image file (for image-based stories)
        if story.get('image_filename'):
            image_path = os.path.join("static", "uploads", story['image_filename'])
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    deleted_files.append(f"uploads/{story['image_filename']}")
                    logger.info(f"Deleted uploaded image: {story['image_filename']}")
            except Exception as e:
                logger.warning(f"Failed to delete uploaded image {story['image_filename']}: {e}")
        
        # Delete the story document from Cosmos DB
        try:
            container.delete_item(item=story_id, partition_key=story_id)
            logger.info(f"Story deleted successfully: {story_id}")
        except Exception as e:
            logger.error(f"Failed to delete story from database: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete story from database")
        
        return {
            "success": True,
            "message": "Story deleted successfully",
            "story_id": story_id,
            "deleted_files": deleted_files
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting story {story_id}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/stories/stats")
async def story_stats():
    """Return aggregate statistics for stories."""
    if not container:
        return {"success": True, "total": 0, "text": 0, "image": 0, "avg_words": 0}
    
    try:
        items = list(container.query_items(
            query="SELECT c.word_count, c.story_type FROM c",
            enable_cross_partition_query=True
        ))
        total = len(items)
        text_cnt = sum(1 for i in items if i.get("story_type") == "text")
        img_cnt = sum(1 for i in items if i.get("story_type") == "image")
        total_words = sum(int(i.get("word_count") or 0) for i in items)
        avg = int(total_words / total) if total else 0
        return {
            "success": True,
            "total": total,
            "text": text_cnt,
            "image": img_cnt,
            "avg_words": avg
        }
    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        return {"success": False, "error": "stats query failed"}

@app.get("/env-debug")
async def env_debug():
    """Debug endpoint to check environment variables (non-secret)."""
    return {
        "azure_openai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "NOT SET"),
        "azure_openai_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "NOT SET"),
        "cosmos_db_url": os.getenv("COSMOS_DB_URL", "NOT SET"),
        "cosmos_db_name": os.getenv("COSMOS_DB_NAME", "NOT SET"),
        "cosmos_container_name": os.getenv("COSMOS_CONTAINER_NAME", "NOT SET")
    }
async def get_stories(limit: int = 5):
    """Get recent stories from Cosmos DB"""
    logger.info(f"GET /api/stories called with limit={limit}")
    
    try:
        if not container:
            logger.warning("Container not available, returning empty list")
            return {
                "success": True,
                "stories": [],
                "message": "Database not available"
            }
        
        logger.info("Querying Cosmos DB...")
        
        # Simple query first
        try:
            items = list(container.query_items(
                query="SELECT * FROM c ORDER BY c._ts DESC",
                enable_cross_partition_query=True,
                max_item_count=limit
            ))
            
            logger.info(f"Query successful, found {len(items)} items")
            
            return {
                "success": True,
                "stories": items
            }
            
        except Exception as query_error:
            logger.error(f"Query error: {query_error}")
            logger.error(f"Query traceback: {traceback.format_exc()}")
            
            return {
                "success": True,
                "stories": [],
                "error": f"Query failed: {str(query_error)}"
            }
            
    except Exception as e:
        logger.error(f"General error in get_stories: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "stories": [],
            "error": str(e)
        }

@app.post("/api/stories")
async def create_story(req: StoryCreateRequest):
    """Create a story from text prompt using Azure OpenAI"""
    try:
        raw_output = await generate_story_text(
            prompt=req.prompt,
            genre=req.genre,
            tone=req.tone,
            length=req.length
        )
        title, content = normalize_story_output(raw_output, req.prompt, req.genre)
        created_at = datetime.utcnow().isoformat() + "Z"
        story_doc = {
            "id": str(uuid.uuid4()),
            "story_type": "text",
            "prompt": req.prompt,
            "genre": req.genre,
            "tone": req.tone,
            "length": req.length,
            "content": content,
            "title": title,
            "word_count": len(content.split()),
            "created_at": created_at,
        }
        generated_image_meta = None
        if req.generate_image:
            logger.info(f"Image gen (text) style={req.image_style} size={req.image_size} quality={req.image_quality}")
            try:
                generated_image_meta = await generate_story_image(
                    story_text=content,
                    style=req.image_style or "digital-art",
                    size=req.image_size or "1024x1024",
                    quality=req.image_quality or "standard"
                )
                story_doc["generated_image_filename"] = generated_image_meta["filename"]
                story_doc["generated_image_meta"] = {
                    "style": generated_image_meta["style"],
                    "size": generated_image_meta["size"],
                    "quality": generated_image_meta["quality"]
                }
            except ContentPolicyError as cpe:
                logger.warning(f"Policy block (text): {cpe}")
                generated_image_meta = {"error": str(cpe), "error_type": "content_policy", "user_friendly": True}
            except ImageGenerationError as ie:
                logger.warning(f"Image gen fail (text): {ie}")
                generated_image_meta = {"error": str(ie), "error_type": "generation_error"}
            except Exception as ue:
                logger.error(f"Image gen unexpected (text): {ue}")
                generated_image_meta = {"error": "unexpected image generation failure", "error_type": "unexpected_error"}
        if container:
            try:
                container.upsert_item(story_doc)
            except Exception as e:
                logger.error(f"Cosmos upsert fail (text): {e}")
        else:
            logger.warning("Cosmos container not initialized; skipping persist.")
        return {"success": True, "story": story_doc, "generated_image": generated_image_meta}
    except Exception as e:
        logger.error(f"Text story error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Story generation failed")

@app.post("/api/stories/image")
async def create_story_from_image(
    image: UploadFile = File(...),
    image_description: Optional[str] = Form(None),
    theme: str = Form("general"),
    length: str = Form("medium"),
    tone: str = Form("creative"),
    generate_image: Optional[bool] = Form(False),
    image_style: Optional[str] = Form(None),
    image_size: Optional[str] = Form(None),
    image_quality: Optional[str] = Form(None),
):
    """Create a story from uploaded image using Azure OpenAI"""
    try:
        image_filename = f"{uuid.uuid4()}_{image.filename}"
        os.makedirs("static/uploads", exist_ok=True)
        with open(os.path.join("static/uploads", image_filename), "wb") as f:
            f.write(await image.read())
        context = image_description or "an uploaded image"
        sys_prompt = (
            f"You are a creative story writer. Write a {length} {theme} story with a {tone} tone "
            "based on the image description provided. Return ONLY JSON with 'title' and 'content'."
        )
        user_prompt = f"Write a {length} {theme} story with a {tone} tone inspired by {context}."
        response = openai_client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500,
            temperature=0.8
        )
        raw = response.choices[0].message.content
        title, content = normalize_story_output(raw, image_description or "", theme)
        created_at = datetime.utcnow().isoformat() + "Z"
        story_doc = {
            "id": str(uuid.uuid4()),
            "story_type": "image",
            "image_filename": image_filename,
            "image_description": image_description,
            "genre": theme,
            "tone": tone,
            "length": length,
            "content": content,
            "title": title,
            "word_count": len(content.split()),
            "created_at": created_at,
        }
        generated_image_meta = None
        if generate_image:
            logger.info(f"Image gen (image story) style={image_style} size={image_size} quality={image_quality}")
            try:
                generated_image_meta = await generate_story_image(
                    story_text=content,
                    style=image_style or "digital-art",
                    size=image_size or "1024x1024",
                    quality=image_quality or "standard"
                )
                story_doc["generated_image_filename"] = generated_image_meta["filename"]
                story_doc["generated_image_meta"] = {
                    "style": generated_image_meta["style"],
                    "size": generated_image_meta["size"],
                    "quality": generated_image_meta["quality"]
                }
            except ContentPolicyError as cpe:
                logger.warning(f"Policy block (image story): {cpe}")
                generated_image_meta = {"error": str(cpe), "error_type": "content_policy", "user_friendly": True}
            except ImageGenerationError as ie:
                logger.warning(f"Image gen fail (image story): {ie}")
                generated_image_meta = {"error": str(ie), "error_type": "generation_error"}
            except Exception as ue:
                logger.error(f"Image gen unexpected (image story): {ue}")
                generated_image_meta = {"error": "unexpected image generation failure", "error_type": "unexpected_error"}
        if container:
            try:
                container.upsert_item(story_doc)
            except Exception as e:
                logger.error(f"Cosmos upsert fail (image story): {e}")
        else:
            logger.warning("Cosmos container not initialized; skipping persist.")
        return {"success": True, "story": story_doc, "generated_image": generated_image_meta}
    except Exception as e:
        logger.error(f"Image story error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Image story generation failed")

@app.get("/api/image-config")
async def image_config_status():
    """Non-secret status of image generation configuration."""
    return {
        "success": True,
        "endpoint_set": bool(os.getenv("AZURE_OPENAI_ENDPOINT")),
        "key_present": bool(
            os.getenv("AZURE_OPENAI_API_KEY")
            or os.getenv("AZURE_OPENAI_KEY")
            or os.getenv("AZURE_OPENAI_PRIMARY_KEY")
        ),
        "dalle_deployment": os.getenv("AZURE_DALLE_DEPLOYMENT_NAME", "not set"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    }

@app.delete("/api/stories/{story_id}")
async def delete_story(story_id: str):
    """Delete a story by ID"""
    logger.info(f"DELETE /api/stories/{story_id}")
    
    if not container:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        try:
            story = container.read_item(item=story_id, partition_key=story_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Story not found")
        
        deleted_files = []
        
        # Delete uploaded image
        img_filename = story.get("image_filename")
        if img_filename:
            img_path = os.path.join("static", "uploads", img_filename)
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                    deleted_files.append(f"uploads/{img_filename}")
                except Exception as e:
                    logger.warning(f"Failed to delete image: {e}")
        
        # Delete generated image
        gen_filename = story.get("generated_image_filename")
        if gen_filename:
            gen_path = os.path.join("static", "generated", gen_filename)
            if os.path.exists(gen_path):
                try:
                    os.remove(gen_path)
                    deleted_files.append(f"generated/{gen_filename}")
                except Exception as e:
                    logger.warning(f"Failed to delete generated image: {e}")
        
        # Delete from Cosmos DB
        container.delete_item(item=story_id, partition_key=story_id)
        
        return {
            "success": True,
            "story_id": story_id,
            "deleted_files": deleted_files
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/stories/stats")
async def story_stats():
    """Return aggregate statistics for stories."""
    if not container:
        return {"success": True, "total": 0, "text": 0, "image": 0, "avg_words": 0}
    try:
        items = list(container.query_items(
            query="SELECT c.word_count, c.story_type FROM c",
            enable_cross_partition_query=True
        ))
        total = len(items)
        text_cnt = sum(1 for i in items if i.get("story_type") == "text")
        img_cnt = sum(1 for i in items if i.get("story_type") == "image")
        total_words = sum(int(i.get("word_count") or 0) for i in items)
        avg = int(total_words / total) if total else 0
        return {
            "success": True,
            "total": total,
            "text": text_cnt,
            "image": img_cnt,
            "avg_words": avg
        }
    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        return {"success": False, "error": "stats query failed"}

@app.post("/api/analyze-content")
async def analyze_content_for_image(payload: dict):
    """Analyze story text for potential image generation policy issues."""
    story_text = payload.get("content", "")
    if not story_text:
        raise HTTPException(status_code=400, detail="Content is required")
    try:
        # If analyze_story_content was provided in earlier versions keep it;
        # if removed, respond with a simple structure.
        if 'analyze_story_content' in globals():
            analysis = analyze_story_content(story_text)  # type: ignore
        else:
            analysis = {
                "potentially_problematic": [],
                "story_length": len(story_text),
                "word_count": len(story_text.split()),
                "suggestions": [
                    "Use abstract, family‑friendly phrasing",
                    "Avoid explicit violence or adult themes",
                    "Remove real person names or brands"
                ]
            }
        return {"success": True, "analysis": analysis}
    except Exception as e:
        logger.error(f"Content analysis error: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")

@app.get("/env-debug")
async def env_debug():
    """Debug endpoint to check environment variables (non-secret)."""
    return {
        "azure_openai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "NOT SET"),
        "azure_openai_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "NOT SET"),
        "azure_dalle_deployment": os.getenv("AZURE_DALLE_DEPLOYMENT_NAME", "NOT SET"),
        "cosmos_db_url": os.getenv("COSMOS_DB_URL", "NOT SET"),
        "cosmos_db_name": os.getenv("COSMOS_DB_NAME", "NOT SET"),
        "cosmos_container_name": os.getenv("COSMOS_CONTAINER_NAME", "NOT SET")
    }
