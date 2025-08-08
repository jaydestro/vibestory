import os
import uuid
import httpx
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("image_generation")

class ImageGenerationError(Exception):
    """Base exception for image generation errors"""
    pass

class ContentPolicyError(ImageGenerationError):
    """Exception for content policy violations"""
    pass

async def generate_story_image(
    story_text: str,
    style: str = "digital-art",
    size: str = "1024x1024",
    quality: str = "standard"
) -> Dict[str, Any]:
    """Generate an image using Azure OpenAI DALL-E."""
    # Get configuration from environment
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    api_key = (
        os.getenv("AZURE_OPENAI_KEY") or 
        os.getenv("AZURE_OPENAI_API_KEY") or 
        os.getenv("AZURE_OPENAI_PRIMARY_KEY")
    )
    deployment = os.getenv("AZURE_DALLE_DEPLOYMENT_NAME", "dall-e-3")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    
    # Validate configuration
    if not endpoint:
        raise ImageGenerationError("Azure OpenAI endpoint not configured")
    if not api_key:
        raise ImageGenerationError("Azure OpenAI API key not configured")
    if not deployment:
        raise ImageGenerationError("DALL-E deployment name not configured")
    
    # Create directories if they don't exist
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static", "generated")
    os.makedirs(static_dir, exist_ok=True)
    
    # Create a simple, clean prompt
    prompt = f"A {style} style illustration inspired by a story"
    if story_text:
        # Take first sentence only for simplicity
        first_sentence = story_text.split('.')[0][:200]
        prompt = f"A {style} style artistic illustration of: {first_sentence}"
    
    url = f"{endpoint}/openai/deployments/{deployment}/images/generations?api-version={api_version}"
    payload = {"prompt": prompt, "n": 1, "size": size}
    if quality == "hd":
        payload["quality"] = "hd"
    
    headers = {"api-key": api_key, "Content-Type": "application/json"}
    
    logger.info(f"Generating image with DALL-E deployment: {deployment}")
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 400:
                error_details = response.text
                logger.error(f"Bad request (400): {error_details}")
                try:
                    error_json = response.json()
                    error_message = error_json.get("error", {}).get("message", "")
                    if "content policy" in error_message.lower():
                        raise ContentPolicyError("Content policy violation detected")
                    else:
                        raise ImageGenerationError(f"Request error: {error_message}")
                except:
                    raise ImageGenerationError("Bad request - check story content")
            
            if response.status_code == 404:
                logger.error(f"DALL-E deployment '{deployment}' not found")
                raise ImageGenerationError(f"DALL-E deployment '{deployment}' not found")
            
            if response.status_code == 401:
                logger.error("Azure OpenAI authentication failed")
                raise ImageGenerationError("Authentication failed - check API key")
            
            if response.status_code != 200:
                logger.error(f"Error: HTTP {response.status_code}: {response.text}")
                raise ImageGenerationError(f"Image generation failed: HTTP {response.status_code}")
            
            # Parse response
            data = response.json()
            image_url = data["data"][0]["url"]
            
            # Download image
            img_resp = await client.get(image_url)
            if img_resp.status_code != 200:
                raise ImageGenerationError("Failed to download image")
            
            # Save image
            filename = f"story_image_{uuid.uuid4().hex[:8]}.png"
            file_path = os.path.join(static_dir, filename)
            
            with open(file_path, "wb") as f:
                f.write(img_resp.content)
            
            logger.info(f"Image saved: {filename}")
            
            # Return metadata
            return {
                "image_url": f"/static/generated/{filename}",
                "filename": filename,
                "style": style,
                "size": size,
                "quality": quality,
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            
    except httpx.TimeoutException:
        raise ImageGenerationError("Request timed out")
    except httpx.RequestError:
        raise ImageGenerationError("Network error")
    except ContentPolicyError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise ImageGenerationError("Unexpected error occurred")
            if response.status_code == 429:
                logger.warning("Rate limit exceeded for image generation")
                raise ImageGenerationError("Rate limit exceeded. Please try again later.")
            
            if response.status_code != 200:
                logger.error(f"Image generation failed with status {response.status_code}: {response.text[:200]}")
                raise ImageGenerationError(f"Image generation failed: HTTP {response.status_code}")
            
            # Parse response
            try:
                data = response.json()
                image_url = data["data"][0]["url"]
                logger.info(f"Generated image URL: {image_url}")
            except (KeyError, IndexError, ValueError) as e:
                logger.error(f"Unexpected response format: {response.text[:200]}")
                raise ImageGenerationError("Invalid response from image generation service")
            
            # Download the generated image
            logger.info(f"Downloading generated image from: {image_url}")
            image_response = await client.get(image_url)
            
            if image_response.status_code != 200:
                logger.error(f"Failed to download image: HTTP {image_response.status_code}")
                raise ImageGenerationError("Failed to download generated image")
            
            # Save image to local storage
            filename = f"story_image_{uuid.uuid4().hex[:8]}.png"
            file_path = os.path.join(static_dir, filename)
            
            with open(file_path, "wb") as f:
                f.write(image_response.content)
            
            logger.info(f"Image saved successfully: {filename} ({len(image_response.content)} bytes)")
            
            # Return metadata
            return {
                "image_url": f"/static/generated/{filename}",
                "filename": filename,
                "style": style,
                "size": size,
                "quality": quality,
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            
    except httpx.TimeoutException:
        logger.error("Image generation request timed out")
        raise ImageGenerationError("Image generation timed out. Please try again.")
    except httpx.RequestError as e:
        logger.error(f"Network error during image generation: {e}")
        raise ImageGenerationError("Network error occurred during image generation")
    except ContentPolicyError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error during image generation: {e}")
        raise ImageGenerationError(f"Unexpected error: {str(e)}")
                "style": style,
                "size": size,
                "quality": quality,
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            
    except ContentPolicyError:
        # Re-raise content policy errors as-is
        raise
    except httpx.TimeoutException:
        logger.error("Image generation request timed out")
        raise ImageGenerationError("Image generation timed out. Please try again.")
    except httpx.RequestError as e:
        logger.error(f"Network error during image generation: {e}")
        raise ImageGenerationError("Network error occurred during image generation")
    except ImageGenerationError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error during image generation: {e}")
        raise ImageGenerationError(f"Unexpected error: {str(e)}")
