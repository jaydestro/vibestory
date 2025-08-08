#Requires -Module Az

param(
    [Parameter(Mandatory = $true)]
    [string]$ManagedIdentityName,
    
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory = $true)]
    [string]$OpenAIResourceName,
    
    [Parameter(Mandatory = $true)]
    [string]$CosmosAccountName,
    
    [Parameter(Mandatory = $true)]
    [string]$SubscriptionId
)

Write-Host "Setting Azure subscription context..." -ForegroundColor Green
Set-AzContext -SubscriptionId $SubscriptionId

Write-Host "Getting managed identity..." -ForegroundColor Green
$managedIdentity = Get-AzUserAssignedIdentity -ResourceGroupName $ResourceGroupName -Name $ManagedIdentityName
$principalId = $managedIdentity.PrincipalId

Write-Host "Managed Identity Principal ID: $principalId" -ForegroundColor Yellow

# Assign Cognitive Services OpenAI User role to existing OpenAI resource
Write-Host "Assigning Cognitive Services OpenAI User role..." -ForegroundColor Green
$openAiRoleId = "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"
$openAiScope = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.CognitiveServices/accounts/$OpenAIResourceName"

try {
    New-AzRoleAssignment -ObjectId $principalId -RoleDefinitionId $openAiRoleId -Scope $openAiScope
    Write-Host "✓ OpenAI role assignment completed" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*already exists*") {
        Write-Host "✓ OpenAI role assignment already exists" -ForegroundColor Yellow
    } else {
        Write-Error "Failed to assign OpenAI role: $($_.Exception.Message)"
    }
}

# Assign Cosmos DB Built-in Data Contributor role to existing Cosmos DB
Write-Host "Assigning Cosmos DB Built-in Data Contributor role..." -ForegroundColor Green
$cosmosRoleId = "00000000-0000-0000-0000-000000000002"
$cosmosScope = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.DocumentDB/databaseAccounts/$CosmosAccountName"

try {
    New-AzRoleAssignment -ObjectId $principalId -RoleDefinitionId $cosmosRoleId -Scope $cosmosScope
    Write-Host "✓ Cosmos DB role assignment completed" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*already exists*") {
        Write-Host "✓ Cosmos DB role assignment already exists" -ForegroundColor Yellow
    } else {
        Write-Error "Failed to assign Cosmos DB role: $($_.Exception.Message)"
    }
}

Write-Host "Permission assignment completed!" -ForegroundColor Green
Write-Host "The managed identity '$ManagedIdentityName' now has access to:" -ForegroundColor Cyan
Write-Host "  - Azure OpenAI: $OpenAIResourceName" -ForegroundColor Cyan
Write-Host "  - Cosmos DB: $CosmosAccountName" -ForegroundColor Cyan
