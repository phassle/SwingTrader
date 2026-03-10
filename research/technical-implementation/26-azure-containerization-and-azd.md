# 26 - Azure Containerization and azd

> Research date: 2026-03-10
> Goal: Define the implementation approach for containerizing the Python scanner with Docker, creating Aspire-compatible azd deployment configuration, and deploying to Azure Container Apps with managed Cosmos DB. This completes the local-to-production transition.
> Prerequisites: [09-azure-container-apps-deep-dive.md](09-azure-container-apps-deep-dive.md), [18-aspire-apphost-implementation.md](18-aspire-apphost-implementation.md), [25-local-development-workflow.md](25-local-development-workflow.md)

## Table of Contents

1. [Overview](#overview)
2. [Dockerfile Design](#dockerfile-design)
3. [Local Container Testing](#local-container-testing)
4. [Aspire Container Mode](#aspire-container-mode)
5. [azd Project Structure](#azd-project-structure)
6. [Azure Resource Provisioning](#azure-resource-provisioning)
7. [Deployment Process](#deployment-process)
8. [Configuration Differences](#configuration-differences)
9. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
10. [Cost Management](#cost-management)

---

## Overview

Phase 1 local development uses **Aspire with AddExecutable()** (direct Python process). For Azure deployment, we need:

1. **Dockerfile** — containerize Python scanner
2. **Aspire AppHost update** — switch from AddExecutable() to AddDockerfile()
3. **azd configuration** — azure.yaml + Bicep templates for infrastructure
4. **Azure resources** — Container Apps, Cosmos DB, Key Vault, Log Analytics

**Design principle:** Same config contract locally and in Azure (environment variables).

**Goal:** `azd up` provisions and deploys everything.

---

## Dockerfile Design

### Multi-Stage Build

**Why multi-stage:**
- Smaller final image (no build tools)
- Faster deployment (fewer layers)
- Security (minimal attack surface)

### Dockerfile

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 scanner && \
    mkdir -p /app && \
    chown -R scanner:scanner /app

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/scanner/.local

# Copy application code
COPY --chown=scanner:scanner . .

# Set PATH for user-installed packages
ENV PATH=/home/scanner/.local/bin:$PATH

# Switch to non-root user
USER scanner

# Entrypoint
CMD ["python", "main.py"]
```

**Key design choices:**

1. **Multi-stage:** Build stage has gcc (for compiling Python packages), runtime doesn't
2. **Slim base:** python:3.11-slim (~140MB) vs full (~1GB)
3. **Non-root user:** Security best practice (UID 1000)
4. **User-installed packages:** `--user` flag installs to ~/.local (non-root compatible)
5. **Explicit entrypoint:** `python main.py` (no shell, faster startup)

### .dockerignore

```
# .dockerignore
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
.env
*.log
.DS_Store
tests/
.pytest_cache/
```

**Why:** Reduce image size, avoid copying local artifacts.

---

## Local Container Testing

### Build and Test Locally

**1. Build image:**
```bash
cd src/Scanner

docker build -t swingtrader-scanner:local .

# Verify image size
docker images swingtrader-scanner:local
# Should be ~200-250MB
```

**2. Run container with emulator:**
```bash
# Start Cosmos emulator first (if not running)
docker run -d --name cosmos-emulator \
  -p 8081:8081 \
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest

# Run scanner container
docker run --rm \
  --network host \
  -e COSMOS_CONNECTION_STRING="AccountEndpoint=https://localhost:8081/;AccountKey=C2y6..." \
  -e COSMOS_DATABASE_NAME="SwingTraderDB" \
  -e LOG_LEVEL="INFO" \
  -e LOG_FORMAT="json" \
  -e TELEGRAM_BOT_TOKEN="123456:ABC..." \
  -e TELEGRAM_CHAT_ID="987654321" \
  -e SCAN_MODE="daily" \
  -e TICKER_UNIVERSE="omx_large_cap" \
  -e DRY_RUN="false" \
  swingtrader-scanner:local
```

**Expected output:**
- Container starts
- Logs in JSON format (stdout)
- Connects to emulator (localhost:8081)
- Executes scan
- Exits with code 0

**3. Verify containerized behavior matches native:**
```bash
# Check exit code
echo $?  # Should be 0

# Check Cosmos data
curl -k https://localhost:8081/_explorer/index.html

# Check Telegram notification
# (Message should appear in Telegram app)
```

---

## Aspire Container Mode

### Switch to AddDockerfile()

**Update AppHost Program.cs:**

```csharp
var builder = DistributedApplication.CreateBuilder(args);

// Cosmos DB (same as before)
var cosmos = builder.AddAzureCosmosDB("cosmos")
    .AddDatabase("SwingTraderDB");

// Python scanner (container mode)
var scanner = builder.AddDockerfile("scanner", "../Scanner")
    .WithEnvironment("COSMOS_CONNECTION_STRING", cosmos.Resource.ConnectionStringExpression)
    .WithEnvironment("COSMOS_DATABASE_NAME", "SwingTraderDB")
    .WithEnvironment("LOG_LEVEL", "INFO")
    .WithEnvironment("LOG_FORMAT", "json")
    .WithEnvironment("TELEGRAM_BOT_TOKEN", builder.Configuration["TelegramBotToken"] ?? "")
    .WithEnvironment("TELEGRAM_CHAT_ID", builder.Configuration["TelegramChatId"] ?? "")
    .WithEnvironment("SCAN_MODE", "daily")
    .WithEnvironment("TICKER_UNIVERSE", "omx_large_cap")
    .WithEnvironment("DRY_RUN", "false")
    .WaitFor(cosmos);

builder.Build().Run();
```

**Changes:**
- `AddExecutable()` → `AddDockerfile()`
- Path: `"../Scanner"` (context directory containing Dockerfile)
- Environment variables: Same as before (config contract unchanged)

**Test locally:**
```bash
dotnet run --project src/AppHost

# First run builds Docker image (takes 2-3 minutes)
# Subsequent runs use cached image (fast)
```

**Why test locally:**
- Verify Dockerfile works before deploying to Azure
- Catch configuration issues early
- Validate container networking with Cosmos emulator

---

## azd Project Structure

### azure.yaml

**Location:** Repository root

```yaml
# azure.yaml
name: swingtrader
metadata:
  template: swingtrader@0.0.1-beta

services:
  apphost:
    project: ./src/AppHost
    language: csharp
    host: containerapp

hooks:
  postprovision:
    shell: sh
    run: |
      echo "Azure resources provisioned successfully"
      echo "Cosmos DB endpoint: $(azd env get-values | grep COSMOS_ENDPOINT)"
```

**Key fields:**
- `name`: Project name (used as prefix for Azure resources)
- `services.apphost`: Points to Aspire AppHost project
- `host: containerapp`: Deploy to Azure Container Apps

---

### infra/ Directory

**Structure:**
```
infra/
├── main.bicep              # Root Bicep template
├── main.parameters.json    # Parameter file (dev environment)
├── modules/
│   ├── containerapp.bicep  # Container Apps definition
│   ├── cosmos.bicep        # Cosmos DB definition
│   ├── keyvault.bicep      # Key Vault definition
│   └── logs.bicep          # Log Analytics definition
```

### infra/main.bicep

```bicep
targetScope = 'resourceGroup'

@description('Primary location for resources')
param location string = resourceGroup().location

@description('Environment name (dev, staging, prod)')
param environmentName string = 'dev'

@description('Application name')
param appName string = 'swingtrader'

// Key Vault for secrets
module keyVault 'modules/keyvault.bicep' = {
  name: 'keyVault'
  params: {
    location: location
    keyVaultName: '${appName}-kv-${environmentName}'
  }
}

// Log Analytics for monitoring
module logs 'modules/logs.bicep' = {
  name: 'logs'
  params: {
    location: location
    logAnalyticsName: '${appName}-logs-${environmentName}'
  }
}

// Cosmos DB
module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos'
  params: {
    location: location
    accountName: '${appName}-cosmos-${environmentName}'
    databaseName: 'SwingTraderDB'
  }
}

// Container App Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${appName}-env-${environmentName}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.outputs.workspaceId
        sharedKey: logs.outputs.workspaceKey
      }
    }
  }
}

// Scanner Container App
module scanner 'modules/containerapp.bicep' = {
  name: 'scanner'
  params: {
    location: location
    containerAppName: '${appName}-scanner-${environmentName}'
    containerAppEnvId: containerAppEnv.id
    cosmosConnectionString: cosmos.outputs.connectionString
    keyVaultName: keyVault.outputs.keyVaultName
  }
}

// Outputs
output cosmosEndpoint string = cosmos.outputs.endpoint
output scannerUrl string = scanner.outputs.fqdn
```

### infra/modules/containerapp.bicep

```bicep
param location string
param containerAppName string
param containerAppEnvId string
param cosmosConnectionString string
param keyVaultName string

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnvId
    configuration: {
      secrets: [
        {
          name: 'cosmos-connection-string'
          value: cosmosConnectionString
        }
        {
          name: 'telegram-bot-token'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/TelegramBotToken'
          identity: 'system'
        }
        {
          name: 'telegram-chat-id'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/TelegramChatId'
          identity: 'system'
        }
      ]
      activeRevisionsMode: 'Single'
    }
    template: {
      containers: [
        {
          name: 'scanner'
          image: 'swingtrader-scanner:latest'  // Replaced by azd during deployment
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'COSMOS_CONNECTION_STRING'
              secretRef: 'cosmos-connection-string'
            }
            {
              name: 'COSMOS_DATABASE_NAME'
              value: 'SwingTraderDB'
            }
            {
              name: 'LOG_LEVEL'
              value: 'INFO'
            }
            {
              name: 'LOG_FORMAT'
              value: 'json'
            }
            {
              name: 'TELEGRAM_BOT_TOKEN'
              secretRef: 'telegram-bot-token'
            }
            {
              name: 'TELEGRAM_CHAT_ID'
              secretRef: 'telegram-chat-id'
            }
            {
              name: 'SCAN_MODE'
              value: 'daily'
            }
            {
              name: 'TICKER_UNIVERSE'
              value: 'omx_large_cap'
            }
            {
              name: 'DRY_RUN'
              value: 'false'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
        rules: [
          {
            name: 'schedule'
            custom: {
              type: 'cron'
              metadata: {
                timezone: 'Europe/Stockholm'
                start: '0 15 * * 1-5'  // 3 PM CET, Mon-Fri
                end: '0 16 * * 1-5'
                desiredReplicas: '1'
              }
            }
          }
        ]
      }
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

output fqdn string = containerApp.properties.configuration.ingress.fqdn
```

**Key patterns:**

1. **Secrets from Key Vault:** Telegram credentials stored in Key Vault, referenced in Container App
2. **Scheduled scaling:** Container scales to 1 replica at 3 PM CET (Mon-Fri), scales to 0 after completion
3. **System-assigned identity:** Container App has managed identity to access Key Vault
4. **Resource limits:** 0.25 CPU, 0.5GB RAM (sufficient for Phase 1)

---

## Azure Resource Provisioning

### azd init

```bash
# Initialize azd (first time only)
azd init

# Follow prompts:
# - Select: "Use code in the current directory"
# - Environment name: dev
# - Azure subscription: [Select subscription]
# - Azure location: northeurope
```

**Creates:**
- `.azure/` directory (environment config)
- `azure.yaml` (if not exists)

### Set Secrets in Key Vault

```bash
# After azd provision completes, set secrets
az keyvault secret set \
  --vault-name swingtrader-kv-dev \
  --name TelegramBotToken \
  --value "123456:ABC..."

az keyvault secret set \
  --vault-name swingtrader-kv-dev \
  --name TelegramChatId \
  --value "987654321"
```

---

## Deployment Process

### Full Deployment

```bash
# Provision infrastructure + deploy code
azd up

# Expected steps:
# 1. Build Docker image for scanner
# 2. Push image to Azure Container Registry (auto-created by azd)
# 3. Provision Azure resources (Cosmos DB, Container Apps, Key Vault, Log Analytics)
# 4. Deploy scanner container to Container Apps
# 5. Configure scheduled scaling

# First deployment: ~10-15 minutes
# Subsequent deployments: ~3-5 minutes (infrastructure cached)
```

### Deployment Only (Skip Provisioning)

```bash
# Deploy code changes without re-provisioning
azd deploy

# Use when:
# - Code changed, infrastructure unchanged
# - Faster than full azd up
# - ~2-3 minutes
```

### Verify Deployment

```bash
# List resources
azd env get-values

# Output:
# COSMOS_ENDPOINT=https://swingtrader-cosmos-dev.documents.azure.com:443/
# SCANNER_URL=https://swingtrader-scanner-dev.northeurope.azurecontainerapps.io

# Check Container App status
az containerapp show \
  --name swingtrader-scanner-dev \
  --resource-group rg-swingtrader-dev \
  --query "properties.runningStatus"

# Expected: "Running" (during scan) or "Stopped" (between scans)
```

---

## Configuration Differences

### Local vs Azure

| Aspect | Local (Aspire) | Azure (Container Apps) |
|--------|----------------|------------------------|
| **Cosmos** | Emulator (localhost:8081) | Managed Cosmos DB |
| **Secrets** | User Secrets (.NET) | Azure Key Vault |
| **Networking** | localhost | Azure VNet |
| **Scaling** | N/A (manual start) | Scheduled (cron) |
| **Logs** | Aspire Dashboard | Azure Log Analytics |
| **Monitoring** | Aspire Dashboard | Azure Monitor |

**Config contract:** Unchanged (same environment variables).

**Cosmos connection string:**
- Local: `AccountEndpoint=https://localhost:8081/;AccountKey=...`
- Azure: `AccountEndpoint=https://swingtrader-cosmos-dev.documents.azure.com:443/;AccountKey=...`

**Scanner code:** Zero changes (connection string injected via environment).

---

## Monitoring and Troubleshooting

### View Logs in Azure

**Azure Portal:**
1. Navigate to Container App: `swingtrader-scanner-dev`
2. Click "Log stream" (live logs)
3. Or "Logs" → Query Log Analytics

**Azure CLI:**
```bash
# Stream logs
az containerapp logs show \
  --name swingtrader-scanner-dev \
  --resource-group rg-swingtrader-dev \
  --follow

# Query recent errors
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "ContainerAppConsoleLogs_CL | where Log_s contains 'ERROR' | order by TimeGenerated desc | take 10"
```

### View Cosmos Data

**Azure Portal:**
1. Navigate to Cosmos DB: `swingtrader-cosmos-dev`
2. Click "Data Explorer"
3. Browse containers: signals, scan_runs, etc.

**Azure CLI:**
```bash
# Query signals
az cosmosdb sql query \
  --account-name swingtrader-cosmos-dev \
  --database-name SwingTraderDB \
  --container-name signals \
  --query-text "SELECT * FROM signals WHERE signals.date = '2026-03-10' ORDER BY signals.total_score DESC"
```

### Troubleshooting Failed Deployment

**Common issues:**

1. **Image build fails:**
   - Check Dockerfile syntax
   - Test build locally: `docker build -t test .`
   - Check azd logs: `azd deploy --debug`

2. **Container won't start:**
   - Check environment variables in Container App (Azure Portal → Configuration)
   - Verify secrets in Key Vault: `az keyvault secret list --vault-name swingtrader-kv-dev`
   - Check container logs: `az containerapp logs show ...`

3. **Cosmos connection fails:**
   - Verify connection string: `az cosmosdb keys list --name swingtrader-cosmos-dev --resource-group rg-swingtrader-dev`
   - Check firewall rules: Cosmos DB → Firewall → Allow Azure services

---

## Cost Management

### Phase 1 Estimated Costs

| Resource | Pricing Tier | Monthly Cost (EUR) |
|----------|--------------|-------------------|
| Cosmos DB | Serverless (400 RU/s min) | ~€5-10 |
| Container Apps | Consumption (0.25 CPU, 0.5GB RAM, 22 runs/month) | ~€2-5 |
| Key Vault | Standard | ~€0.50 |
| Log Analytics | Pay-as-you-go (5GB free) | €0 (under free tier) |
| Container Registry | Basic | ~€4 |
| **Total** | | **~€11-20/month** |

**Cost optimization tips:**

1. **Use Cosmos DB serverless** (not provisioned throughput)
2. **Scale Container Apps to 0 between scans** (configured in Bicep)
3. **Use Basic tier for non-critical resources** (Key Vault, Container Registry)
4. **Set up cost alerts** (Azure Cost Management)

### Set Cost Alert

```bash
# Create budget (€25/month threshold)
az consumption budget create \
  --budget-name swingtrader-monthly-budget \
  --amount 25 \
  --time-grain Monthly \
  --start-date 2026-03-01 \
  --end-date 2027-03-01 \
  --resource-group rg-swingtrader-dev
```

---

## Summary

### Key Decisions

1. **Multi-stage Dockerfile** — smaller image, faster deployment
2. **AddDockerfile() in Aspire** — consistent local/Azure experience
3. **azd for infrastructure** — declarative Bicep templates
4. **Scheduled scaling** — run daily at 3 PM CET, scale to 0 after
5. **Key Vault for secrets** — never hardcode Telegram credentials
6. **Serverless Cosmos DB** — pay only for actual usage

### What This Enables

- **One-command deployment:** `azd up` provisions and deploys everything
- **Production-ready:** Managed services, scheduled runs, centralized logging
- **Cost-effective:** ~€15/month, scales to 0 between scans
- **Observable:** Azure Monitor, Log Analytics, Cosmos DB metrics

### Complete Workflow

**Local development:**
```bash
dotnet run --project src/AppHost  # Aspire + emulator
```

**Deploy to Azure:**
```bash
azd up  # Provision + deploy
```

**Monitor production:**
```bash
az containerapp logs show --name swingtrader-scanner-dev --follow
```

### Next Steps

1. **Deploy to production:** `azd up --environment prod`
2. **Set up CI/CD:** GitHub Actions with `azd deploy` (file 09 covers this)
3. **Add monitoring alerts:** Azure Monitor alerts for scan failures

---

## References

- [Azure Container Apps documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [azd (Azure Developer CLI)](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/)
- [Dockerfile best practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [09-azure-container-apps-deep-dive.md](09-azure-container-apps-deep-dive.md) — Container Apps guide
- [18-aspire-apphost-implementation.md](18-aspire-apphost-implementation.md) — AppHost architecture
- [25-local-development-workflow.md](25-local-development-workflow.md) — Local setup
