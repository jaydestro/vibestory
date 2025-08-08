#!/usr/bin/env python3
"""
Test script for Azure OpenAI DALL-E image generation service
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the service
sys.path.insert(0, str(Path(__file__).parent))

from services.image_generation import generate_story_image, ImageGenerationError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_image_generation():
    """Test the image generation service with various scenarios"""
    
    print("🧪 Testing Azure OpenAI DALL-E Image Generation")
    print("=" * 50)
    
    # Check environment variables
    print("\n1. Checking Configuration...")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_DALLE_DEPLOYMENT_NAME")
    
    print(f"   Endpoint: {'✓ SET' if endpoint else '✗ MISSING'}")
    print(f"   API Key:  {'✓ SET' if api_key else '✗ MISSING'}")
    print(f"   DALL-E:   {'✓ SET' if deployment else '✗ MISSING'} ({deployment})")
    
    if not all([endpoint, api_key, deployment]):
        print("\n❌ Missing required configuration. Please check your .env file.")
        return False
    
    # Test cases
    test_cases = [
        {
            "name": "Simple Story Test",
            "story": "A brave knight rescues a dragon from an evil princess in a magical forest.",
            "style": "fantasy",
            "size": "1024x1024",
            "quality": "standard"
        },
        {
            "name": "Modern Story Test", 
            "story": "In a bustling cyberpunk city, a hacker discovers a secret that could change everything.",
            "style": "digital-art",
            "size": "1792x1024",
            "quality": "standard"
        },
        {
            "name": "Short Story Test",
            "story": "A cat sits by the window watching rain.",
            "style": "watercolor",
            "size": "1024x1024",
            "quality": "standard"
        }
    ]
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Story: {test_case['story'][:50]}...")
        print(f"   Style: {test_case['style']}, Size: {test_case['size']}, Quality: {test_case['quality']}")
        
        try:
            print("   🔄 Generating image... (this may take 30-60 seconds)")
            
            result = await generate_story_image(
                story_text=test_case['story'],
                style=test_case['style'], 
                size=test_case['size'],
                quality=test_case['quality']
            )
            
            print(f"   ✅ SUCCESS!")
            print(f"      Image URL: {result['image_url']}")
            print(f"      Filename: {result['filename']}")
            print(f"      Created: {result['created_at']}")
            
            # Verify file exists
            file_path = os.path.join("static", "generated", result['filename'])
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"      File size: {file_size:,} bytes")
            else:
                print(f"      ⚠️ Warning: File not found at {file_path}")
            
            successful_tests += 1
            
        except ImageGenerationError as e:
            print(f"   ❌ Image Generation Error: {e}")
            
        except Exception as e:
            print(f"   ❌ Unexpected Error: {e}")
    
    # Summary
    print(f"\n📊 Test Results")
    print("=" * 20)
    print(f"Successful: {successful_tests}/{total_tests}")
    print(f"Failed:     {total_tests - successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("\n🎉 All tests passed! Image generation is working correctly.")
        return True
    elif successful_tests > 0:
        print(f"\n⚠️  Partial success. {successful_tests} out of {total_tests} tests passed.")
        return True
    else:
        print("\n❌ All tests failed. Please check your Azure OpenAI configuration.")
        return False

async def test_error_handling():
    """Test error handling scenarios"""
    
    print("\n🛡️  Testing Error Handling")
    print("=" * 30)
    
    # Test with empty story
    try:
        print("1. Testing with empty story...")
        result = await generate_story_image("", "realistic", "1024x1024", "standard")
        print("   ✅ Handled empty story successfully")
    except Exception as e:
        print(f"   ✅ Properly caught error: {e}")
    
    # Test with very long story
    try:
        print("2. Testing with very long story...")
        long_story = "A very long story. " * 200  # Create a very long story
        result = await generate_story_image(long_story, "realistic", "1024x1024", "standard")
        print("   ✅ Handled long story successfully")
    except Exception as e:
        print(f"   ✅ Properly caught error: {e}")

def main():
    """Main test function"""
    print("Starting Azure OpenAI DALL-E Image Generation Tests")
    print("This will test the image generation service with your current configuration")
    print("\nNote: Each test may take 30-60 seconds to complete")
    
    # Run the async tests
    try:
        success = asyncio.run(test_image_generation())
        asyncio.run(test_error_handling())
        
        if success:
            print("\n✅ Image generation service is working correctly!")
            print("You can now use image generation in your VibeStory application.")
        else:
            print("\n❌ Image generation service has issues.")
            print("Please check the error messages above and verify your Azure OpenAI configuration.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests cancelled by user")
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")

if __name__ == "__main__":
    main()
