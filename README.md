# VibeStory - AI-Powered Story Generator

A FastAPI web application that generates creative stories using Azure OpenAI and stores them in Azure Cosmos DB.

## 🏗️ Architecture Overview

```
┌──────────────────┐    ┌─────────────────┐
│   FastAPI        │◄──►│   Azure         │
│   Application    │    │   OpenAI        │
│                  │    │   Service       │
└─────────┬────────┘    └─────────────────┘
          │
          ▼
┌─────────────────┐
│   Azure         │
│   Cosmos DB     │
└─────────────────┘
```

## 🚀 Features

- **AI Story Generation**: Powered by Azure OpenAI GPT-4o model
- **Story Persistence**: Stories stored in Azure Cosmos DB
- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **Environment Configuration**: Uses environment variables for configuration

## 📁 Project Structure

```
vibestory/
├── .github/
│   └── copilot-instructions.md    # GitHub Copilot workspace instructions
├── Dockerfile                     # Container image definition
├── requirements.txt               # Python dependencies
├── run.py                        # Application entry point
├── main.py                       # FastAPI application
├── .env                          # Environment variables (local dev only)
├── README.md                     # Project documentation
└── PROJECT-STRUCTURE.md          # Detailed project structure
```

## 🛠️ Prerequisites

- Python 3.11+
- Azure OpenAI resource with GPT-4o deployment
- Azure Cosmos DB account with database and container

## 🔧 Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vibestory
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file with your Azure resource details:
   ```bash
   # Azure OpenAI Configuration
   AZURE_OPENAI_ENDPOINT="https://your-region.api.cognitive.microsoft.com/"
   AZURE_OPENAI_KEY="your-openai-key"
   AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
   AZURE_OPENAI_API_VERSION="2024-02-01"

   # Azure Cosmos DB Configuration
   COSMOS_DB_URL="https://your-cosmos-account.documents.azure.com/"
   COSMOS_DB_KEY="your-cosmos-key"
   COSMOS_DB_NAME="your-database-name"
   COSMOS_CONTAINER_NAME="your-container-name"

   # Application Configuration
   PORT="8000"
   DEBUG="true"
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Access the application**
   - Application: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## 🔐 Security Features

- **Environment Variables**: Configuration through environment variables
- **HTTPS Ready**: Application supports HTTPS deployment
- **Input Validation**: Pydantic models for request/response validation

## 📝 API Endpoints

### Story Generation
- `POST /generate-story`: Generate a new story
- `GET /stories`: List all stories
- `GET /stories/{story_id}`: Get specific story

### Health & Info
- `GET /health`: Application health check
- `GET /`: Application information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Create an issue in this repository
- Check Azure documentation for service-specific problems
- Review application logs for debugging
2. **Configure deployment parameters**
   Update `azure.yaml` with your existing resource details:
   ```yaml
   infra:
     parameters:
       existingOpenAiEndpoint: "https://your-region.api.cognitive.microsoft.com/"
       existingOpenAiDeploymentName: "gpt-4o"
       existingCosmosEndpoint: "https://your-cosmos-account.documents.azure.com/"
       existingCosmosDatabaseName: "your-database-name"
       existingCosmosContainerName: "your-container-name"
   ```

3. **Deploy the application**
   ```bash
   azd up
   ```
   This will:
   - Package your application into a container
   - Provision Azure Container Apps infrastructure
   - Deploy your application
   - Create a managed identity

4. **Assign permissions to existing resources**
   After deployment, run the permission script:
   ```bash
   ./scripts/assign-permissions.sh \
     --managed-identity-name "id-vibestory-{resource-token}" \
     --resource-group "rg-prod-{resource-token}" \
     --openai-resource "your-openai-resource-name" \
     --cosmos-account "your-cosmos-account-name" \
     --subscription-id "your-subscription-id"
   ```

## 🔐 Security Features

- **Managed Identity Authentication**: No API keys stored in the application
- **Azure RBAC**: Fine-grained permissions using Azure role assignments
- **Secure Configuration**: Environment variables injected at runtime
- **HTTPS Only**: All traffic encrypted in transit

## 🏗️ Infrastructure Components

### Azure Container Apps
- **Environment**: Managed Container Apps environment
- **App**: Scalable container running FastAPI application
- **Ingress**: HTTPS endpoint with custom domain support
- **Scaling**: Auto-scale from 0-3 instances based on load

### Managed Identity
- **User-Assigned Identity**: Dedicated identity for the application
- **Role Assignments**: 
  - `Cognitive Services OpenAI User` for Azure OpenAI access
  - `Cosmos DB Built-in Data Contributor` for Cosmos DB access

### Environment Variables
The application uses these environment variables in production:
- `AZURE_CLIENT_ID`: Managed identity client ID
- `AZURE_OPENAI_ENDPOINT`: OpenAI service endpoint
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Model deployment name
- `COSMOS_DB_URL`: Cosmos DB account endpoint
- `COSMOS_DB_NAME`: Database name
- `COSMOS_CONTAINER_NAME`: Container name

## 📊 Monitoring & Observability

- **Application Insights**: Automatic telemetry collection
- **Container Logs**: Available through Azure Portal or CLI
- **Health Endpoints**: Built-in health checks
- **Metrics**: Request/response metrics and performance counters

## 🔄 CI/CD Pipeline

The project is configured for GitHub Actions deployment:
- **Build**: Container image creation
- **Deploy**: Automated deployment to Azure Container Apps
- **Security**: Managed identity authentication

## 🛟 Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   - Ensure managed identity has proper role assignments
   - Run the permission assignment script

2. **Container Startup Issues**
   - Check container logs: `az containerapp logs show`
   - Verify environment variables are set correctly

3. **OpenAI Quota Errors**
   - Check your OpenAI resource quota limits
   - Consider using different deployment models

### Deployment Issues

4. **Resource Group Not Found Error**
   ```
   ERROR: resource not found: 0 resource groups with prefix or suffix with value: 'vibestory-prod'
   ```
   **Solutions:**
   ```bash
   # Check current environment status
   azd env list
   azd env get-values
   
   # If environment exists but resources missing, provision again
   azd provision
   
   # If you need to start fresh
   azd env new vibestory-prod
   azd up
   ```

5. **Deployment Not Found Error**
   ```
   ERROR: no resources found for deployment, 'vibestory-prod-xxxxxxxxxx'
   ```
   **Solutions:**
   ```bash
   # Check if resource group exists
   az group list --query "[?starts_with(name, 'rg-prod')]"
   
   # If resource group exists, try redeploying
   azd deploy
   
   # If no resource group, start fresh
   azd env new
   azd up
   ```

6. **Docker Not Running Error**
   ```
   ERROR: Docker daemon is not running
   ```
   **Solutions:**
   - Start Docker Desktop
   - Verify Docker is running: `docker --version`
   - Alternative: Use GitHub Codespaces for deployment

7. **Environment Variables Not Loading**
   - Ensure `.env` file is in project root
   - Check parameter values in `azure.yaml`
   - Verify no syntax errors in YAML file

8. **Bicep Compilation Errors**
   - Check Bicep file syntax
   - Ensure all required parameters are provided
   - Validate with: `az bicep build --file infra/main.bicep`

9. **Subscription Deployment Location Error**
   ```
   ERROR: The 'location' property must be specified for deployment
   ```
   **Solutions:**
   ```bash
   # Ensure location is specified in azure.yaml
   # Check that you're using the latest azd version
   azd version
   azd upgrade
   
   # Try specifying location explicitly
   azd up --location eastus
   
   # Alternative: Use resource group scope instead
   # (requires modifying main.bicep to use resourceGroup scope)
   ```

### Clean Start Process

If you encounter persistent deployment issues:

```bash
# 1. Clean up existing environment
azd env list
azd env select vibestory-prod  # if exists
azd down --purge  # if deployment exists

# 2. Remove local environment
azd env new vibestory-new

# 3. Fresh deployment
azd up
```

### Verification Commands

After successful deployment:

```bash
# Check resource group
az group list --query "[?starts_with(name, 'rg-prod')]"

# Check container app status
az containerapp list --query "[].{Name:name,Status:properties.provisioningState}"

# Check managed identity
az identity list --query "[?starts_with(name, 'id-vibestory')]"

# Test application endpoint
curl https://your-container-app-url.azurecontainerapps.io/health
```

### Logs and Monitoring

```bash
# View container app logs
az containerapp logs show --name ca-vibestory-{token} --resource-group rg-prod-{token}

# Stream logs in real-time
az containerapp logs tail --name ca-vibestory-{token} --resource-group rg-prod-{token}

# Check deployment status
azd show
```

## 📝 API Endpoints

### Story Generation
- `POST /generate-story`: Generate a new story
- `GET /stories`: List all stories
- `GET /stories/{story_id}`: Get specific story

### Health & Info
- `GET /health`: Application health check
- `GET /`: Application information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Create an issue in this repository
- Check Azure documentation for service-specific problems
- Review application logs in Azure Portal
