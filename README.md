# Azure VibeStory App

A modern web application built with FastAPI that integrates Azure OpenAI and Cosmos DB to create AI-powered story generation.

## Features

- AI-powered story generation using Azure OpenAI
- Story storage and retrieval with Azure Cosmos DB
- Clean, responsive web interface
- RESTful API design
- Easy deployment to Azure App Service

## Prerequisites

- Python 3.8 or higher
- Azure subscription with:
  - Azure OpenAI service
  - Azure Cosmos DB account

## Local Development

1. **Clone and Setup**
   ```bash
   # Navigate to project directory
   cd vibestory
   
   # Install dependencies globally (no virtual environment needed)
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Fill in your Azure service credentials

3. **Run the Application**
   ```bash
   python main.py
   ```
   
   The application will be available at `http://localhost:8000`

## Azure Deployment

This project is configured for deployment using Azure Developer CLI (azd):

```bash
azd up
```

## Project Structure

```
vibestory/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── models.py            # Pydantic models
│   ├── routes/              # API route handlers
│   └── services/            # Azure service integrations
├── static/                  # Static web assets
├── templates/               # HTML templates
├── infra/                   # Infrastructure as Code (Bicep)
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
├── main.py                  # Application runner
└── azure.yaml              # Azure deployment configuration
```

## API Endpoints

- `GET /` - Home page
- `POST /api/stories` - Generate a new story
- `GET /api/stories` - List all stories
- `GET /api/stories/{id}` - Get specific story

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI service endpoint |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | OpenAI model deployment name |
| `COSMOS_DB_ENDPOINT` | Cosmos DB account endpoint |
| `COSMOS_DB_KEY` | Cosmos DB primary key |
| `COSMOS_DB_DATABASE` | Database name |
| `COSMOS_DB_CONTAINER` | Container name |

## License

MIT License
