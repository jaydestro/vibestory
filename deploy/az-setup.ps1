param(
  [string]$Location = "eastus",
  [string]$ResourceGroup = "rg-vibestory",
  [string]$Plan = "asp-vibestory",
  [string]$WebApp = "vibestory-web-$(Get-Random)",
  [string]$CosmosAccount = "vibestory-cosmos-$(Get-Random)",
  [string]$CosmosDb = "vibestorydb",
  [string]$CosmosContainer = "stories",
  [string]$PartitionKey = "/genre"
)

# Login first if needed: az login
az group create -n $ResourceGroup -l $Location

# App Service Plan (Linux)
az appservice plan create -g $ResourceGroup -n $Plan --is-linux --sku B1

# Web App (Python 3.10)
az webapp create -g $ResourceGroup -p $Plan -n $WebApp --runtime "PYTHON:3.10"

# Cosmos DB for NoSQL
az cosmosdb create -g $ResourceGroup -n $CosmosAccount --kind GlobalDocumentDB
az cosmosdb sql database create -a $CosmosAccount -g $ResourceGroup -n $CosmosDb
az cosmosdb sql container create -a $CosmosAccount -g $ResourceGroup -d $CosmosDb -n $CosmosContainer --partition-key-path $PartitionKey

# Keys and endpoints
$cosmosKey = az cosmosdb keys list -g $ResourceGroup -n $CosmosAccount --type keys --query primaryMasterKey -o tsv
$cosmosUrl = az cosmosdb show -g $ResourceGroup -n $CosmosAccount --query documentEndpoint -o tsv

# REQUIRED: set these before running, or set afterwards in Portal
# $env:AZURE_OPENAI_ENDPOINT="https://<your-openai>.openai.azure.com/"
# $env:AZURE_OPENAI_KEY="<your-key>"
# $env:AZURE_OPENAI_API_VERSION="2024-02-15-preview"
# $env:AZURE_OPENAI_DEPLOYMENT_NAME="<your-chat-deployment>"
# $env:AZURE_OPENAI_IMAGE_DEPLOYMENT_NAME="<your-image-deployment>"

# App settings
$settings = @(
  "WEBSITES_PORT=8000",
  "AZURE_OPENAI_ENDPOINT=$env:AZURE_OPENAI_ENDPOINT",
  "AZURE_OPENAI_KEY=$env:AZURE_OPENAI_KEY",
  "AZURE_OPENAI_API_VERSION=$env:AZURE_OPENAI_API_VERSION",
  "AZURE_OPENAI_DEPLOYMENT_NAME=$env:AZURE_OPENAI_DEPLOYMENT_NAME",
  "AZURE_OPENAI_IMAGE_DEPLOYMENT_NAME=$env:AZURE_OPENAI_IMAGE_DEPLOYMENT_NAME",
  "COSMOS_DB_URL=$cosmosUrl",
  "COSMOS_DB_KEY=$cosmosKey",
  "COSMOS_DB_NAME=$CosmosDb",
  "COSMOS_CONTAINER_NAME=$CosmosContainer"
)

az webapp config appsettings set -g $ResourceGroup -n $WebApp --settings $settings

# Startup command
az webapp config set -g $ResourceGroup -n $WebApp --startup-file "bash startup.sh"

Write-Host "Deployed resources:"
Write-Host "Web App: https://$WebApp.azurewebsites.net"
Write-Host "Set GitHub secrets AZURE_WEBAPP_NAME=$WebApp and AZURE_WEBAPP_PUBLISH_PROFILE from the portal."
