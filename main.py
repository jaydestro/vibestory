#!/usr/bin/env python3
"""
VibeStory Application Entry Point
Run this file to start the application without using virtual environments
"""

import os
import sys
import subprocess
from pathlib import Path
import base64
import aiohttp

def check_python_version():
    """Check if Python version is supported"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required packages are available"""
    print("📦 Checking dependencies...")
    try:
        import fastapi
        import uvicorn
        import openai
        import azure.cosmos
        import pydantic
        import dotenv
        print("✅ All dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def check_environment():
    """Check if environment variables are configured"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("Please copy .env.example to .env and configure your Azure credentials")
        return False
    
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY", 
        "COSMOS_DB_ENDPOINT",
        "COSMOS_DB_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or "your_" in value.lower():
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or unconfigured environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with actual Azure service credentials")
        return False
    
    print("✅ Environment variables configured")
    return True

def start_application():
    """Start the FastAPI application"""
    port = int(os.getenv("PORT", 8000))
    
    print(f"\n🚀 Starting VibeStory application...")
    print(f"📱 Application will be available at: http://localhost:{port}")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        # Start the application using uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped")
    except FileNotFoundError:
        print("❌ uvicorn not found. Please install dependencies first.")
        return False
    
    return True

def main():
    """Main function"""
    print("🎨 VibeStory - AI Story Generator")
    print("=" * 50)
    print("Running without virtual environment")
    print()
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check environment configuration
    if not check_environment():
        print("\n💡 To get started:")
        print("1. Copy .env.example to .env")
        print("2. Configure your Azure OpenAI and Cosmos DB credentials")
        print("3. Run this script again")
        return 1
    
    # Start the application
    success = start_application()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import logging
import os
import json
from datetime import datetime
import uuid
import traceback
from azure.cosmos import CosmosClient  # ensure available

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="VibeStory", description="AI Story Generator")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure image directories exist
UPLOAD_DIR = "static/uploads"
GENERATED_DIR = "static/generated"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

# Add these constants once (used for file cleanup)
UPLOAD_DIR = "static/uploads"
GENERATED_DIR = "static/generated"

# Templates
templates = Jinja2Templates(directory="templates")

# Global variables for Azure clients
openai_client = None
container = None
cosmos_client = None

# API Models
class StoryRequest(BaseModel):
    prompt: str
    genre: str = "general"
    length: str = "medium"
    tone: str = "neutral"
    # Added optional image generation fields
    generate_image: bool = False
    image_style: Optional[str] = None
    image_size: Optional[str] = "1024x1024"   # e.g., 1024x1024, 1792x1024, 1024x1792
    image_quality: Optional[str] = "standard" # 'standard' or 'hd'

@app.on_event("startup")
async def startup_event():
    """Initialize Azure clients on startup"""
    global openai_client, container, cosmos_client
    
    logger.info("Starting application initialization...")
    
    # Log environment variables (without exposing keys)
    env_vars = {
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "AZURE_OPENAI_DEPLOYMENT_NAME": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION"),
        "COSMOS_DB_URL": os.getenv("COSMOS_DB_URL"),
        "COSMOS_DB_NAME": os.getenv("COSMOS_DB_NAME"),
        "COSMOS_CONTAINER_NAME": os.getenv("COSMOS_CONTAINER_NAME")
    }
    
    for key, value in env_vars.items():
        logger.info(f"{key}: {'✓ SET' if value else '✗ NOT SET'}")
    
    # Check for API keys without logging them
    openai_key = os.getenv("AZURE_OPENAI_KEY")
    cosmos_key = os.getenv("COSMOS_DB_KEY")
    
    logger.info(f"AZURE_OPENAI_KEY: {'✓ SET' if openai_key else '✗ NOT SET'}")
    logger.info(f"COSMOS_DB_KEY: {'✓ SET' if cosmos_key else '✗ NOT SET'}")
    
    # Initialize Azure OpenAI
    if openai_key and env_vars["AZURE_OPENAI_ENDPOINT"]:
        try:
            from openai import AzureOpenAI
            openai_client = AzureOpenAI(
                azure_endpoint=env_vars["AZURE_OPENAI_ENDPOINT"],
                api_key=openai_key,
                api_version=env_vars["AZURE_OPENAI_API_VERSION"]
            )
            logger.info("✓ Azure OpenAI client initialized")
        except Exception as e:
            logger.error(f"✗ Azure OpenAI initialization failed: {e}")
    
    # Initialize Cosmos DB
    if cosmos_key and env_vars["COSMOS_DB_URL"]:
        try:
            from azure.cosmos import CosmosClient
            
            logger.info("Initializing Cosmos DB client...")
            cosmos_client = CosmosClient(
                url=env_vars["COSMOS_DB_URL"],
                credential=cosmos_key
            )
            
            logger.info("Getting database client...")
            database = cosmos_client.get_database_client(env_vars["COSMOS_DB_NAME"])
            
            logger.info("Getting container client...")
            container = database.get_container_client(env_vars["COSMOS_CONTAINER_NAME"])
            
            logger.info("✓ Cosmos DB client initialized")
        except Exception as e:
            logger.error(f"✗ Cosmos DB initialization failed: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Main page"""
    logger.info("Root endpoint accessed")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "VibeStory is running",
        "azure_openai": "connected" if openai_client else "not connected",
        "cosmos_db": "connected" if container else "not connected",
        "environment_check": {
            "AZURE_OPENAI_ENDPOINT": "✓" if os.getenv("AZURE_OPENAI_ENDPOINT") else "✗",
            "AZURE_OPENAI_KEY": "✓" if os.getenv("AZURE_OPENAI_KEY") else "✗",
            "COSMOS_DB_URL": "✓" if os.getenv("COSMOS_DB_URL") else "✗",
            "COSMOS_DB_KEY": "✓" if os.getenv("COSMOS_DB_KEY") else "✗"
        }
    }

@app.get("/api/stories")
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
async def create_text_story(story_request: StoryRequest):
    """Create a story from text prompt using Azure OpenAI"""
    try:
        if not openai_client:
            raise HTTPException(status_code=500, detail="Azure OpenAI not available")
        
        # Generate story using Azure OpenAI
        system_prompt = f"""You are a creative story writer. Write a {story_request.length} {story_request.genre} story with a {story_request.tone} tone. 
        The story should be engaging and well-structured. Format your response as a JSON object with 'title' and 'content' fields."""
        
        response = openai_client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": story_request.prompt}
            ],
            max_tokens=1500,
            temperature=0.8
        )
        
        # Parse the response
        story_text = response.choices[0].message.content
        
        try:
            story_data = json.loads(story_text)
            title = story_data.get('title', 'Untitled Story')
            content = story_data.get('content', story_text)
        except json.JSONDecodeError:
            # Fallback if response isn't JSON
            title = "Generated Story"
            content = story_text
        
        # Create story document
        story = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "genre": story_request.genre,
            "word_count": len(content.split()),
            "story_type": "text",
            "prompt": story_request.prompt,
            "tone": story_request.tone,
            "length": story_request.length,
            "created_at": datetime.utcnow().isoformat()
        }
        
        generated_image_resp = None  # Will carry image result or error for frontend

        # If image generation requested, call Azure OpenAI Images and save locally
        if story_request.generate_image:
            try:
                image_deployment = os.getenv("AZURE_OPENAI_IMAGE_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_IMAGE_MODEL") or "dall-e-3"
                image_style = story_request.image_style or "realistic"
                image_size = story_request.image_size or "1024x1024"
                image_quality = story_request.image_quality or "standard"

                # Build concise prompt from story
                img_prompt = f"Create a {image_style} image illustrating the story titled '{title}'. Scene: {content[:300]}"

                # Request image
                img = openai_client.images.generate(
                    model=image_deployment,
                    prompt=img_prompt,
                    size=image_size,
                    quality=image_quality,
                    n=1
                )

                # Handle URL or base64 responses
                image_bytes = None
                if img.data and len(img.data) > 0:
                    data0 = img.data[0]
                    if getattr(data0, "b64_json", None):
                        image_bytes = base64.b64decode(data0.b64_json)
                    elif getattr(data0, "url", None):
                        async with aiohttp.ClientSession() as session:
                            async with session.get(data0.url) as resp:
                                if resp.status == 200:
                                    image_bytes = await resp.read()
                                else:
                                    raise RuntimeError(f"Image download failed: HTTP {resp.status}")
                if not image_bytes:
                    raise RuntimeError("No image data returned from Azure OpenAI")

                # Persist image
                filename = f"generated_{uuid.uuid4().hex}.png"
                out_path = os.path.join(GENERATED_DIR, filename)
                with open(out_path, "wb") as f:
                    f.write(image_bytes)

                # Attach metadata to story for listing
                story["generated_image_filename"] = filename
                story["generated_image_style"] = image_style
                story["generated_image_size"] = image_size
                story["generated_image_quality"] = image_quality

                generated_image_resp = {
                    "image_url": f"/static/generated/{filename}",
                    "style": image_style,
                    "size": image_size,
                    "quality": image_quality
                }
            except Exception as ie:
                # Graceful degradation: story still returns, image error sent to UI
                msg = str(ie)
                # Best-effort content policy detection
                error_type = "content_policy" if "safety" in msg.lower() or "policy" in msg.lower() else "generation_error"
                generated_image_resp = {
                    "error": f"Image generation failed: {msg}",
                    "error_type": error_type
                }

        # Save to Cosmos DB
        if container:
            try:
                container.create_item(story)
                logger.info(f"Story saved to database: {story['id']}")
            except Exception as db_error:
                logger.error(f"Failed to save story to database: {db_error}")
        
        # Build response including image (if requested)
        resp = {
            "success": True,
            "story": story
        }
        if generated_image_resp:
            resp["generated_image"] = generated_image_resp
        return resp

    except Exception as e:
        logger.error(f"Error creating text story: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate story: {str(e)}")

@app.post("/api/stories/image")
async def create_image_story(
    image: UploadFile = File(...),
    theme: str = Form("general"),
    length: str = Form("medium"),
    tone: str = Form("creative"),
    image_description: Optional[str] = Form(None)
):
    """Create a story from uploaded image using Azure OpenAI"""
    try:
        if not openai_client:
            raise HTTPException(status_code=500, detail="Azure OpenAI not available")
        
        # Save uploaded image
        image_filename = f"{uuid.uuid4()}_{image.filename}"
        image_path = f"static/uploads/{image_filename}"
        
        with open(image_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        # For now, generate a story based on the image description
        context = image_description or "an uploaded image"
        prompt = f"Write a {length} {theme} story with a {tone} tone inspired by {context}."
        
        system_prompt = f"""You are a creative story writer. Write a {length} {theme} story with a {tone} tone based on the image description provided.
        Format your response as a JSON object with 'title' and 'content' fields."""
        
        response = openai_client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.8
        )
        
        # Parse the response
        story_text = response.choices[0].message.content
        
        try:
            story_data = json.loads(story_text)
            title = story_data.get('title', 'Image-Generated Story')
            content = story_data.get('content', story_text)
        except json.JSONDecodeError:
            title = "Image-Generated Story"
            content = story_text
        
        # Create story document
        story = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "genre": theme,
            "word_count": len(content.split()),
            "story_type": "image",
            "image_filename": image_filename,
            "image_description": image_description,
            "tone": tone,
            "length": length,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save to Cosmos DB
        if container:
            try:
                container.create_item(story)
                logger.info(f"Image story saved to database: {story['id']}")
            except Exception as db_error:
                logger.error(f"Failed to save image story to database: {db_error}")
        
        return {
            "success": True,
            "story": story
        }
        
    except Exception as e:
        logger.error(f"Error creating image story: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate story from image: {str(e)}")

@app.get("/api/stories/history")
async def get_story_history():
    """Get story history - same as get_stories but with different limit"""
    return await get_stories(limit=10)

@app.get("/api/stories/stats")
async def get_stories_stats():
    """Return basic stats for stories"""
    try:
        if not container:
            return {
                "success": True,
                "total": 0,
                "text": 0,
                "image": 0,
                "avg_words": 0
            }

        # Total
        total_result = list(container.query_items(
            query="SELECT VALUE COUNT(1) FROM c",
            enable_cross_partition_query=True
        ))
        total = total_result[0] if total_result else 0

        # By type
        text_result = list(container.query_items(
            query="SELECT VALUE COUNT(1) FROM c WHERE c.story_type = 'text'",
            enable_cross_partition_query=True
        ))
        text_count = text_result[0] if text_result else 0

        image_result = list(container.query_items(
            query="SELECT VALUE COUNT(1) FROM c WHERE c.story_type = 'image'",
            enable_cross_partition_query=True
        ))
        image_count = image_result[0] if image_result else 0

        # Average words
        avg_result = list(container.query_items(
            query="SELECT VALUE AVG(c.word_count) FROM c WHERE IS_DEFINED(c.word_count)",
            enable_cross_partition_query=True
        ))
        avg_words = int(avg_result[0]) if avg_result and avg_result[0] else 0

        return {
            "success": True,
            "total": total,
            "text": text_count,
            "image": image_count,
            "avg_words": avg_words
        }
    except Exception as e:
        logger.error(f"Stats endpoint error: {e}")
        return {
            "success": True,
            "total": 0,
            "text": 0,
            "image": 0,
            "avg_words": 0
        }

@app.get("/debug/cosmos")
async def debug_cosmos():
    """Debug endpoint for Cosmos DB connection"""
    debug_info = {
        "cosmos_client": "initialized" if cosmos_client else "not initialized",
        "container": "initialized" if container else "not initialized",
        "environment": {
            "COSMOS_DB_URL": "set" if os.getenv("COSMOS_DB_URL") else "not set",
            "COSMOS_DB_KEY": "set" if os.getenv("COSMOS_DB_KEY") else "not set",
            "COSMOS_DB_NAME": os.getenv("COSMOS_DB_NAME", "not set"),
            "COSMOS_CONTAINER_NAME": os.getenv("COSMOS_CONTAINER_NAME", "not set")
        }
    }
    
    if container:
        try:
            # Test a simple read operation
            container.read()
            debug_info["container_test"] = "✓ Container accessible"
        except Exception as e:
            debug_info["container_test"] = f"✗ Container test failed: {str(e)}"
    
    return debug_info

@app.get("/env-debug")
async def env_debug():
    """Debug endpoint to check environment variables"""
    return {
        "azure_openai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "NOT SET"),
        "azure_openai_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "NOT SET"),
        "cosmos_db_url": os.getenv("COSMOS_DB_URL", "NOT SET"),
        "cosmos_db_name": os.getenv("COSMOS_DB_NAME", "NOT SET"),
        "cosmos_container_name": os.getenv("COSMOS_CONTAINER_NAME", "NOT SET")
    }

@app.delete("/api/stories/{story_id}")
async def delete_story(story_id: str):
    """Delete a story by ID from Cosmos DB and remove associated files"""
    try:
        logger.info(f"Attempting to delete story with ID: {story_id}")

        # Ensure DB initialized
        if not container:
            raise HTTPException(status_code=503, detail="Database not available")

        # 1) Find the story (cross-partition) to get file names and candidate PKs
        query = "SELECT * FROM c WHERE c.id = @id"
        items = list(container.query_items(
            query=query,
            parameters=[{"name": "@id", "value": story_id}],
            enable_cross_partition_query=True
        ))
        if not items:
            logger.warning(f"Story not found: {story_id}")
            raise HTTPException(status_code=404, detail="Story not found")

        story = items[0]
        logger.info(f"Found story to delete: {story.get('title','Untitled')}")

        # 2) Best-effort file cleanup
        try:
            if story.get("image_filename"):
                p = os.path.join(UPLOAD_DIR, story["image_filename"])
                if os.path.exists(p):
                    os.remove(p)
                    logger.info(f"Deleted uploaded image: {p}")
            if story.get("generated_image_filename"):
                p = os.path.join(GENERATED_DIR, story["generated_image_filename"])
                if os.path.exists(p):
                    os.remove(p)
                    logger.info(f"Deleted generated image: {p}")
        except Exception as fe:
            logger.warning(f"File cleanup warning: {fe}")

        # 3) Determine container partition key path (e.g., '/genre')
        pk_path = None
        try:
            meta = container.read()
            pk_info = meta.get("partitionKey") or meta.get("partition_key")
            if isinstance(pk_info, dict):
                paths = pk_info.get("paths") or []
                if paths:
                    pk_path = paths[0]  # '/genre'
        except Exception as me:
            logger.warning(f"Could not read container metadata: {me}")

        # 4) Build candidate PK values in priority order
        candidates = []
        if pk_path and pk_path.startswith("/"):
            field = pk_path[1:]  # 'genre'
            candidates.append(story.get(field))
        for f in ["genre", "theme", "story_type", "user_id", "id"]:
            v = story.get(f)
            if v and v not in candidates:
                candidates.append(v)
        candidates.append("general")  # final fallback

        # 5) Try delete with each candidate PK
        last_err = None
        for pk in [c for c in candidates if c is not None]:
            try:
                logger.info(f"Deleting item {story_id} with partition key '{pk}'")
                container.delete_item(item=story_id, partition_key=pk)
                logger.info("Delete succeeded")
                return {"success": True, "message": f"Story {story_id} deleted successfully"}
            except Exception as de:
                last_err = de
                logger.debug(f"Delete failed with pk '{pk}': {de}")

        detail = f"Failed to delete from database. Tried PKs: {', '.join([str(c) for c in candidates if c is not None])}"
        if last_err:
            detail += f". Last error: {str(last_err)}"
        logger.error(detail)
        raise HTTPException(status_code=500, detail=detail)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting story {story_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete story: {str(e)}")
