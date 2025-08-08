#!/usr/bin/env bash
set -euo pipefail

RG=${AZD_ENVIRONMENT_AZURE_RESOURCE_GROUP}
PREFIX=vibestory

UAMI_ID=$(az identity show -g "$RG" -n "${PREFIX}-uami" --query id -o tsv)
UAMI_PRINCIPAL=$(az identity show -g "$RG" -n "${PREFIX}-uami" --query principalId -o tsv)
COSMOS_ID=$(az cosmosdb show -g "$RG" -n "${PREFIX}cosmos" --query id -o tsv)
AOAI_ID=$(az cognitiveservices account show -g "$RG" -n "${PREFIX}-aoai" --query id -o tsv)

# Roles
AOAI_ROLE="Cognitive Services OpenAI User"
COSMOS_ROLE="Cosmos DB Built-in Data Contributor"

az role assignment create --assignee-object-id "$UAMI_PRINCIPAL" --assignee-principal-type ServicePrincipal --role "$AOAI_ROLE" --scope "$AOAI_ID" || true
az role assignment create --assignee-object-id "$UAMI_PRINCIPAL" --assignee-principal-type ServicePrincipal --role "$COSMOS_ROLE" --scope "$COSMOS_ID" || true

echo "Assigned roles to UAMI."