"""
Application entry point
"""
import uvicorn
import os
from dotenv import load_dotenv

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get port from environment or default
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting VibeStory on port {port}")
    print("Environment loaded from .env file")
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=port,
        reload=True,  # Enable hot reload for development
        log_level="info"
    )
