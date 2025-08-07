"""
Azure OpenAI Service
Production-ready with Managed Identity support
"""
import os
import base64
from openai import AsyncAzureOpenAI
from app.services.auth_service import auth_service
from typing import Optional


class OpenAIService:
    """Service for interacting with Azure OpenAI"""
    
    def __init__(self):
        # Get authentication info from auth service
        endpoint, api_key = auth_service.get_openai_auth()
        
        if auth_service.is_production:
            # Use Managed Identity in production
            from azure.identity.aio import get_bearer_token_provider
            credential = auth_service.get_async_credential()
            token_provider = get_bearer_token_provider(
                credential, 
                "https://cognitiveservices.azure.com/.default"
            )
            self.client = AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                azure_ad_token_provider=token_provider,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
            )
        else:
            # Use API key in development
            self.client = AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
            )
        
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    
    async def check_connection(self) -> bool:
        """Check if the OpenAI service is accessible"""
        try:
            # Simple test call to verify connection
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False
    
    async def generate_story(
        self, 
        prompt: str, 
        genre: str = "general", 
        length: str = "short", 
        tone: str = "neutral"
    ) -> str:
        """Generate a story based on the given parameters"""
        
        # Create a detailed prompt
        system_prompt = f"""You are a creative story writer. Generate a {length} {genre} story with a {tone} tone.
        
        Length guidelines:
        - Short: 200-400 words
        - Medium: 500-800 words  
        - Long: 900-1500 words
        
        Make the story engaging, well-structured, and complete."""
        
        user_prompt = f"Write a story based on this prompt: {prompt}"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Failed to generate story: {str(e)}")
    
    async def generate_story_from_image(
        self, 
        image_path: str,
        theme: str = "general", 
        length: str = "short", 
        tone: str = "creative",
        additional_context: str = ""
    ) -> str:
        """Generate a story based on an uploaded image"""
        
        # Read and encode image
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Failed to read image file: {str(e)}")
        
        # Create a detailed prompt based on theme
        theme_prompts = {
            "horror": "Write a spine-chilling horror story inspired by this image. Include suspense, mystery, and eerie elements.",
            "sci-fi": "Write a science fiction story inspired by this image. Include futuristic technology, space, or advanced concepts.",
            "kids": "Write a fun, wholesome children's story inspired by this image. Keep it age-appropriate and imaginative.",
            "romance": "Write a romantic story inspired by this image. Include love, relationships, and emotional connections.",
            "mystery": "Write a mystery story inspired by this image. Include clues, investigation, and suspenseful reveals.",
            "adventure": "Write an exciting adventure story inspired by this image. Include exploration, challenges, and heroic journeys.",
            "fantasy": "Write a fantasy story inspired by this image. Include magic, mythical creatures, or enchanted worlds.",
            "comedy": "Write a humorous, funny story inspired by this image. Include wit, amusing situations, and light-hearted elements.",
            "general": "Write an engaging, creative story inspired by this image."
        }
        
        base_prompt = theme_prompts.get(theme, theme_prompts["general"])
        
        # Length guidelines
        length_guide = {
            "short": "Keep it between 200-400 words",
            "medium": "Write 500-800 words", 
            "long": "Create a detailed story of 900-1500 words"
        }
        
        system_prompt = f"""You are a creative storyteller. Look at the image provided and {base_prompt.lower()}
        
        Guidelines:
        - {length_guide.get(length, length_guide["short"])}
        - Use a {tone} tone
        - Create engaging characters and dialogue
        - Include vivid descriptions inspired by what you see
        - Make the story complete with a beginning, middle, and end
        
        {f"Additional context: {additional_context}" if additional_context else ""}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please write a story based on this image:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Failed to generate story from image: {str(e)}")

    async def generate_title(self, story_content: str) -> str:
        """Generate a title for the given story content"""
        
        prompt = f"""Generate a compelling, creative title for this story. Return only the title, nothing else:

        {story_content[:500]}..."""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.7
            )
            
            title = response.choices[0].message.content.strip()
            # Remove quotes if present
            title = title.strip('"').strip("'")
            return title
            
        except Exception as e:
            # Fallback title if generation fails
            return "Untitled Story"
