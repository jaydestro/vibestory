"""
Health Check Routes
"""
from fastapi import APIRouter
from datetime import datetime
from app.models import HealthResponse
from app.services.cosmos_service import CosmosService
from app.services.openai_service import OpenAIService

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services_status = {}
    
    # Check Cosmos DB connection
    try:
        cosmos_service = CosmosService()
        await cosmos_service.check_connection()
        services_status["cosmos_db"] = "healthy"
    except Exception as e:
        services_status["cosmos_db"] = f"unhealthy: {str(e)}"
    
    # Check OpenAI service
    try:
        openai_service = OpenAIService()
        await openai_service.check_connection()
        services_status["azure_openai"] = "healthy"
    except Exception as e:
        services_status["azure_openai"] = f"unhealthy: {str(e)}"
    
    # Determine overall status
    overall_status = "healthy" if all("healthy" in status for status in services_status.values()) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        services=services_status
    )
