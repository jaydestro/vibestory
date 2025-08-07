"""
Azure Authentication Service
Handles both development (key-based) and production (managed identity) authentication
"""
import os
from typing import Optional
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AzureAuthService:
    """Centralized Azure authentication service"""
    
    def __init__(self):
        self.is_production = self._is_production_environment()
        self._sync_credential = None
        self._async_credential = None
    
    def _is_production_environment(self) -> bool:
        """Detect if running in production environment"""
        # Check for common production environment indicators
        return any([
            os.getenv("AZURE_CLIENT_ID"),  # Service Principal
            os.getenv("MSI_ENDPOINT"),     # App Service Managed Identity
            os.getenv("IDENTITY_ENDPOINT"), # Container Apps Managed Identity
            os.getenv("WEBSITE_SITE_NAME"), # App Service
            os.getenv("CONTAINER_APP_NAME") # Container Apps
        ])
    
    def get_sync_credential(self):
        """Get synchronous credential for Azure services"""
        if not self._sync_credential:
            if self.is_production:
                # Use Managed Identity in production
                self._sync_credential = DefaultAzureCredential()
            else:
                # For development, try service principal first, fall back to default
                client_id = os.getenv("AZURE_CLIENT_ID")
                client_secret = os.getenv("AZURE_CLIENT_SECRET")
                tenant_id = os.getenv("AZURE_TENANT_ID")
                
                if client_id and client_secret and tenant_id:
                    self._sync_credential = ClientSecretCredential(
                        tenant_id=tenant_id,
                        client_id=client_id,
                        client_secret=client_secret
                    )
                else:
                    # Fall back to default credential chain
                    self._sync_credential = DefaultAzureCredential()
        
        return self._sync_credential
    
    def get_async_credential(self):
        """Get asynchronous credential for Azure services"""
        if not self._async_credential:
            if self.is_production:
                # Use Managed Identity in production
                self._async_credential = AsyncDefaultAzureCredential()
            else:
                # For development, use default credential chain
                self._async_credential = AsyncDefaultAzureCredential()
        
        return self._async_credential
    
    def get_openai_auth(self) -> tuple[str, Optional[str]]:
        """Get OpenAI authentication (endpoint, key or credential)"""
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if self.is_production:
            # In production, return endpoint and None (will use managed identity)
            return endpoint, None
        else:
            # In development, return endpoint and key
            key = os.getenv("AZURE_OPENAI_KEY")
            return endpoint, key
    
    def get_cosmos_auth(self) -> tuple[str, Optional[str]]:
        """Get Cosmos DB authentication (endpoint, key or None for managed identity)"""
        endpoint = os.getenv("COSMOS_DB_ENDPOINT")
        
        if self.is_production:
            # In production, return endpoint and None (will use managed identity)
            return endpoint, None
        else:
            # In development, return endpoint and key
            key = os.getenv("COSMOS_DB_KEY")
            return endpoint, key
    
    async def close(self):
        """Close async credentials"""
        if self._async_credential:
            await self._async_credential.close()


# Global auth service instance
auth_service = AzureAuthService()
