# Production Deployment Guide

This application is now configured to use Azure Managed Identity for secure, keyless authentication in production environments.

## Authentication Strategy

- **Development**: Uses API keys from `.env` file
- **Production**: Uses Azure Managed Identity (no keys needed)

## Required Azure Role Assignments

For the application to work with Managed Identity, assign these roles to your App Service/Container App's Managed Identity:

### Azure OpenAI Access
```bash
# Replace with your actual resource names
RESOURCE_GROUP="your-resource-group"
OPENAI_ACCOUNT="your-openai-account"
APP_NAME="your-app-service-name"

# Get the Managed Identity Principal ID
PRINCIPAL_ID=$(az webapp identity show --resource-group $RESOURCE_GROUP --name $APP_NAME --query principalId --output tsv)

# Assign Cognitive Services OpenAI User role
az role assignment create \
  --role "Cognitive Services OpenAI User" \
  --assignee $PRINCIPAL_ID \
  --scope "/subscriptions/{subscription-id}/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$OPENAI_ACCOUNT"
```

### Azure Cosmos DB Access
```bash
# Replace with your actual resource names  
COSMOS_ACCOUNT="your-cosmos-account"

# Assign Cosmos DB Built-in Data Contributor role
az role assignment create \
  --role "Cosmos DB Built-in Data Contributor" \
  --assignee $PRINCIPAL_ID \
  --scope "/subscriptions/{subscription-id}/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.DocumentDB/databaseAccounts/$COSMOS_ACCOUNT"
```

## Deployment Options

### Option 1: Azure App Service

1. Deploy your application to Azure App Service
2. Enable Managed Identity:
   ```bash
   az webapp identity assign --name $APP_NAME --resource-group $RESOURCE_GROUP
   ```
3. Set environment variables (endpoints only, no keys):
   ```bash
   az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP \
     --settings \
     AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/" \
     COSMOS_DB_ENDPOINT="https://your-cosmos.documents.azure.com/" \
     COSMOS_DB_DATABASE="vibestory" \
     COSMOS_DB_CONTAINER="stories" \
     AZURE_OPENAI_DEPLOYMENT="gpt-4o" \
     DEBUG="false"
   ```

### Option 2: Azure Container Apps

1. Deploy to Container Apps with Managed Identity enabled
2. The application will automatically detect the Container Apps environment
3. Configure environment variables through the Azure portal or CLI

## Environment Variables

### Required in Production
- `AZURE_OPENAI_ENDPOINT` - Your OpenAI service endpoint
- `COSMOS_DB_ENDPOINT` - Your Cosmos DB endpoint  
- `COSMOS_DB_DATABASE` - Database name (default: "vibestory")
- `COSMOS_DB_CONTAINER` - Container name (default: "stories")
- `AZURE_OPENAI_DEPLOYMENT` - Model deployment name
- `AZURE_OPENAI_API_VERSION` - API version (default: "2024-02-01")

### NOT Required in Production
- ❌ `AZURE_OPENAI_KEY` - Replaced by Managed Identity
- ❌ `COSMOS_DB_KEY` - Replaced by Managed Identity

## Security Benefits

✅ **No secrets in configuration** - All authentication handled by Azure Managed Identity
✅ **Automatic credential rotation** - Azure handles token refresh
✅ **Principle of least privilege** - Fine-grained role assignments
✅ **Audit trail** - All access logged in Azure Activity Log
✅ **Environment isolation** - Different identities for dev/staging/production

## Local Development

For local development, the application will continue to use API keys from your `.env` file. This hybrid approach allows developers to work locally while production runs securely with Managed Identity.

## Troubleshooting

If you see authentication errors in production:

1. Verify Managed Identity is enabled on your Azure service
2. Check role assignments are correct
3. Ensure endpoints in environment variables are correct
4. Check Azure Activity Logs for detailed error messages

## Testing Production Authentication

You can test the production authentication setup by setting these environment variables locally:

```bash
# Simulate production environment
export MSI_ENDPOINT="http://localhost:50342"  # Fake endpoint to trigger production mode
export AZURE_CLIENT_ID="your-app-service-managed-identity-client-id"
```

Then run your application - it will attempt to use Managed Identity instead of API keys.
