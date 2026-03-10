# 18 - Aspire AppHost Implementation

> Research date: 2026-03-10
> Goal: Define the architecture and implementation approach for the C# Aspire AppHost that orchestrates the SwingTrader Python scanner, Cosmos DB emulator, and supporting services for local development.
> Prerequisites: [12-dotnet-aspire-orchestration.md](12-dotnet-aspire-orchestration.md), [13-data-model-design.md](13-data-model-design.md), [15-security-and-secrets-management.md](15-security-and-secrets-management.md)

## Table of Contents

1. [Overview](#overview)
2. [AppHost Project Structure](#apphost-project-structure)
3. [Cosmos DB Emulator Integration](#cosmos-db-emulator-integration)
4. [Python Scanner Resource Registration](#python-scanner-resource-registration)
5. [Environment Variable Contract](#environment-variable-contract)
6. [Service Dependencies and Startup Order](#service-dependencies-and-startup-order)
7. [Health Checks and Readiness](#health-checks-and-readiness)
8. [Local Development Experience](#local-development-experience)
9. [Troubleshooting Patterns](#troubleshooting-patterns)
10. [Transition to Production](#transition-to-production)

---

## Overview

The Aspire AppHost is a **thin C# orchestration layer** that:
- Starts and configures the Cosmos DB emulator with persistent local storage
- Registers the Python scanner as an executable resource with injected environment variables
- Provides the Aspire dashboard for observability (logs, metrics, health checks)
- Defines service dependencies to ensure correct startup order
- Enables one-command local development: `dotnet run --project src/AppHost`

**Design principle:** The AppHost contains **zero business logic**. It is pure infrastructure orchestration. All scanner logic lives in Python.

**Key decision:** Use `AddExecutable()` for Python in local development, with a clear path to `AddDockerfile()` or `AddContainer()` for Azure deployment (covered in [26-azure-containerization-and-azd.md](26-azure-containerization-and-azd.md)).

---

## AppHost Project Structure

### Recommended Layout

```
SwingTrader/
├── src/
│   ├── AppHost/
│   │   ├── AppHost.csproj          # Aspire.Hosting SDK reference
│   │   ├── Program.cs              # AppHost entry point
│   │   ├── appsettings.json        # Optional: Aspire config overrides
│   │   └── Properties/
│   │       └── launchSettings.json # Launch profile for `dotnet run`
│   └── Scanner/                    # Python scanner (separate project)
│       ├── main.py
│       ├── requirements.txt
│       └── ...
├── SwingTrader.sln                 # Solution file
└── .env.example                    # Template for local secrets
```

### AppHost.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <Nullable>enable</Nullable>
    <IsAspireHost>true</IsAspireHost>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Aspire.Hosting" Version="9.0.0" />
    <PackageReference Include="Aspire.Hosting.Azure.CosmosDB" Version="9.0.0" />
  </ItemGroup>

</Project>
```

**Key points:**
- `IsAspireHost=true`: Enables Aspire-specific tooling
- `Aspire.Hosting`: Core orchestration SDK
- `Aspire.Hosting.Azure.CosmosDB`: Cosmos emulator support

---

## Cosmos DB Emulator Integration

### Design Goals

1. **Persistent data** across AppHost restarts (no data loss during development)
2. **Automatic initialization** of database and containers on first run
3. **Emulator lifecycle** managed by Aspire (start/stop with AppHost)
4. **Connection string** automatically injected into Python scanner

### Implementation Pattern

```csharp
// Program.cs
var builder = DistributedApplication.CreateBuilder(args);

// Add Cosmos DB emulator with persistent volume
var cosmos = builder.AddAzureCosmosDB("cosmos")
    .RunAsEmulator(emulator =>
    {
        // Persistent volume for emulator data
        emulator.WithDataVolume("swingtrader-cosmos-data");
        
        // Consistent ports for local development
        emulator.WithEndpoint(port: 8081, targetPort: 8081, scheme: "https", name: "emulator");
        emulator.WithEndpoint(port: 10255, targetPort: 10255, scheme: "https", name: "direct");
    })
    .AddDatabase("SwingTraderDB");

// Build and run
builder.Build().Run();
```

### Key Design Decisions

**Volume persistence:**
- `WithDataVolume("swingtrader-cosmos-data")` creates a Docker named volume
- Data survives AppHost restarts and container recreation
- Located at: `~/.aspire/volumes/swingtrader-cosmos-data` (or equivalent)
- **Trade-off:** Data persists, but requires manual cleanup if schema changes significantly

**Port mapping:**
- Port 8081: Emulator HTTPS endpoint (default)
- Port 10255: Direct mode endpoint (optional, for SDK optimizations)
- **Recommendation:** Stick with 8081 only unless performance testing shows benefit from direct mode

**Database naming:**
- Database name: `SwingTraderDB` (referenced by Python scanner)
- **Alternative:** Use environment variable for database name to support multiple environments
- Container creation happens in Python bootstrap (see [20-cosmos-repository-implementation.md](20-cosmos-repository-implementation.md))

### Emulator Startup Time

**Expected behavior:**
- First start: 15-30 seconds (image download + initialization)
- Subsequent starts: 5-10 seconds
- Aspire dashboard shows "Starting" → "Running" status

**Health check pattern:**
- Emulator exposes `https://localhost:8081/_explorer/index.html` (Data Explorer)
- Python scanner should retry connection 3-5 times with exponential backoff
- Scanner startup depends on Cosmos readiness (covered below)

---

## Python Scanner Resource Registration

### AddExecutable() Pattern

```csharp
var scanner = builder.AddExecutable("scanner", "python", "../Scanner", "main.py")
    .WithEnvironment("COSMOS_CONNECTION_STRING", cosmos.Resource.ConnectionStringExpression)
    .WithEnvironment("COSMOS_DATABASE_NAME", "SwingTraderDB")
    .WithEnvironment("LOG_LEVEL", "INFO")
    .WithEnvironment("TELEGRAM_BOT_TOKEN", builder.Configuration["TelegramBotToken"] ?? "")
    .WithEnvironment("TELEGRAM_CHAT_ID", builder.Configuration["TelegramChatId"] ?? "")
    .WaitFor(cosmos); // Ensure Cosmos is ready before starting scanner
```

### Design Rationale

**Why AddExecutable():**
- No Docker build required during development (faster iteration)
- Python source changes reflect immediately (edit → restart)
- Native debugging in IDE (VS Code, PyCharm)
- Aligns with "Aspire-first local development" principle

**When to switch to AddDockerfile():**
- Testing production-like environment locally
- Validating containerization before Azure deployment
- See [26-azure-containerization-and-azd.md](26-azure-containerization-and-azd.md) for migration path

**Working directory:**
- `"../Scanner"`: Relative to AppHost project directory
- Assumes `src/AppHost/` and `src/Scanner/` are siblings
- **Alternative:** Use absolute path via `Path.Combine(builder.Environment.ContentRootPath, "../../Scanner")`

**Arguments:**
- `"main.py"`: Scanner entry point
- Additional args: `"--mode", "daily"` for batch vs continuous modes
- Pass as array: `.WithArgs("main.py", "--mode", "daily")`

---

## Environment Variable Contract

### Contract Definition

The Python scanner expects these environment variables (defined in AppHost, validated in scanner bootstrap):

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `COSMOS_CONNECTION_STRING` | string | Yes | - | Full Cosmos connection string (AccountEndpoint + AccountKey) |
| `COSMOS_DATABASE_NAME` | string | Yes | - | Database name: `SwingTraderDB` |
| `LOG_LEVEL` | string | No | INFO | Python logging level: DEBUG, INFO, WARNING, ERROR |
| `TELEGRAM_BOT_TOKEN` | string | Yes | - | Bot token from BotFather |
| `TELEGRAM_CHAT_ID` | string | Yes | - | Target chat ID for notifications |
| `SCAN_MODE` | string | No | daily | `daily` (one-shot) or `continuous` (scheduler) |
| `TICKER_UNIVERSE` | string | No | omx_large_cap | Universe: `omx_large_cap`, `omx_all`, `custom` |

### Secrets Management Integration

**Local development:**
- Secrets stored in User Secrets: `dotnet user-secrets set TelegramBotToken "123:ABC..."`
- Read in AppHost: `builder.Configuration["TelegramBotToken"]`
- Never commit secrets to git (.env should be gitignored)

**Azure production:**
- Use Azure Key Vault integration: `builder.AddAzureKeyVault("swingtrader-kv")`
- Reference secrets: `cosmos.Resource.ConnectionStringExpression` becomes Key Vault reference
- See [15-security-and-secrets-management.md](15-security-and-secrets-management.md) for full strategy

### Connection String Expression

**Key pattern:**
```csharp
.WithEnvironment("COSMOS_CONNECTION_STRING", cosmos.Resource.ConnectionStringExpression)
```

**What this does:**
- In local mode: Resolves to emulator connection string (`AccountEndpoint=https://localhost:8081/;AccountKey=...`)
- In Azure mode (azd): Resolves to actual Cosmos DB connection string from deployment
- **Benefit:** Same code works locally and in production

**Emulator connection string format:**
```
AccountEndpoint=https://localhost:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
```

Note: This key is well-known and safe to use (it's the public emulator key).

---

## Service Dependencies and Startup Order

### Dependency Graph

```
Cosmos DB Emulator (root)
    ↓ WaitFor()
Python Scanner (depends on Cosmos)
```

**Why this matters:**
- Scanner cannot start until Cosmos is ready (connection will fail)
- Aspire respects `WaitFor()` and delays scanner startup
- Dashboard visualizes dependencies clearly

### WaitFor() Implementation

```csharp
var scanner = builder.AddExecutable("scanner", ...)
    .WaitFor(cosmos);
```

**Behavior:**
- Aspire starts Cosmos first
- Polls Cosmos health endpoint until ready
- Only then starts scanner executable
- **Timeout:** Default 60s (configurable via `WithTimeout()`)

### Health Check Strategy

**Cosmos emulator:**
- Health check: TCP port 8081 reachable
- Aspire built-in check (no custom code needed)

**Python scanner:**
- Expose `/health` endpoint via Flask or FastAPI (optional for Phase 1)
- Report status: `{"status": "healthy", "cosmos_connected": true, "last_scan": "2026-03-10T14:00:00Z"}`
- Aspire polls this endpoint and shows status in dashboard

**Phase 1 decision:** Health endpoint is optional. Scanner logs startup success, Aspire monitors process exit code.

---

## Health Checks and Readiness

### Scanner Readiness Pattern

The scanner should follow this startup sequence:

1. **Load and validate config** (environment variables)
2. **Connect to Cosmos** (retry 3x with backoff)
3. **Bootstrap containers** (create if missing)
4. **Log "Scanner ready"** (INFO level)
5. **Execute scan or enter scheduler loop**

**Failure modes:**
- Config validation fails → exit code 1 (Aspire shows as "Exited")
- Cosmos connection fails after retries → exit code 2 (Aspire shows as "Exited")
- Scan execution error → log error, exit code 3 or continue (depending on mode)

### Aspire Dashboard Visualization

**What you'll see:**
- Resources panel: `cosmos` (Running, green), `scanner` (Running, green)
- Logs panel: Interleaved logs from both resources
- Traces panel: Distributed traces if OpenTelemetry added (Phase 2)
- Metrics panel: CPU, memory, custom metrics (Phase 2)

**Key dashboard features:**
- Restart resource: Right-click scanner → Restart
- View logs: Click scanner → Logs tab → filter by level
- Environment variables: Click scanner → Environment tab → see injected vars (secrets hidden)

---

## Local Development Experience

### One-Command Startup

```bash
# From repository root
dotnet run --project src/AppHost
```

**What happens:**
1. AppHost compiles (fast, just orchestration code)
2. Cosmos emulator starts (Docker container)
3. Python scanner starts (after Cosmos ready)
4. Aspire dashboard opens: `http://localhost:15888` (or auto-assigned port)

**Expected timeline:**
- T+0s: AppHost starts
- T+5s: Cosmos emulator running
- T+8s: Scanner validates config
- T+10s: Scanner connects to Cosmos
- T+12s: Scanner executes first scan
- T+15s: Scan complete, results in Cosmos, Telegram notification sent

### Iteration Workflow

**Code change in Python scanner:**
1. Edit `src/Scanner/main.py`
2. In Aspire dashboard: Right-click `scanner` → Restart
3. Scanner restarts with new code (no rebuild needed)
4. Check logs in dashboard

**Config change:**
1. Update User Secrets: `dotnet user-secrets set LOG_LEVEL DEBUG --project src/AppHost`
2. Restart AppHost: `Ctrl+C` and `dotnet run` again
3. New config takes effect

**Data reset:**
1. Stop AppHost (`Ctrl+C`)
2. Delete Cosmos volume: `docker volume rm swingtrader-cosmos-data`
3. Restart AppHost (containers recreated automatically)

### Debug Workflow

**Python debugging:**
- Option 1: Add `import pdb; pdb.set_trace()` in Python code, attach to process
- Option 2: Run scanner outside Aspire with same env vars: `export COSMOS_CONNECTION_STRING=...; python main.py`
- Option 3: Use VS Code launch.json with env vars from `.env` file

**Aspire debugging:**
- Set breakpoint in `Program.cs` (e.g., to inspect connection string expression)
- Run AppHost with debugger: F5 in VS / Rider
- Step through resource configuration

---

## Troubleshooting Patterns

### Common Issues

| Problem | Symptoms | Cause | Solution |
|---------|----------|-------|----------|
| Cosmos emulator won't start | Dashboard shows "Starting" indefinitely | Docker not running, port 8081 in use | Check `docker ps`, kill process on port 8081 |
| Scanner exits immediately | "Exited" status in dashboard, exit code 1 | Config validation failed | Check logs for missing env vars |
| Scanner can't connect to Cosmos | "Connection refused" in logs | Emulator not ready, firewall blocking localhost | Increase retry count, check Windows firewall |
| Data disappears between runs | Empty database after restart | Volume not configured | Add `WithDataVolume()` to Cosmos config |
| Telegram notifications not sending | Scan completes but no message | Invalid bot token or chat ID | Verify secrets with `dotnet user-secrets list` |

### Diagnostic Commands

**Check Cosmos emulator:**
```bash
# Verify container running
docker ps | grep cosmos

# Test emulator endpoint
curl -k https://localhost:8081/_explorer/index.html

# View emulator logs
docker logs $(docker ps -q --filter "ancestor=mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator")
```

**Check scanner process:**
```bash
# If running as executable (not in container)
ps aux | grep python | grep main.py

# Check Python dependencies installed
cd src/Scanner && python -c "import azure.cosmos; print('OK')"
```

**Check secrets:**
```bash
# List all secrets (values hidden)
dotnet user-secrets list --project src/AppHost

# Verify specific secret
dotnet user-secrets set TelegramBotToken "test" --project src/AppHost
dotnet user-secrets list --project src/AppHost | grep Telegram
```

---

## Transition to Production

### What Changes for Azure Deployment

**Local (current design):**
- Cosmos: Emulator (Docker container)
- Scanner: Executable (direct Python process)
- Secrets: User Secrets
- Networking: localhost

**Azure (future, see file 26):**
- Cosmos: Azure Cosmos DB (managed service)
- Scanner: Azure Container Apps (Docker container)
- Secrets: Azure Key Vault
- Networking: VNet integration (optional)

### Code Changes Required

**None in Python scanner** — config contract remains identical.

**AppHost changes:**
```csharp
// Before (local)
var cosmos = builder.AddAzureCosmosDB("cosmos")
    .RunAsEmulator(...)
    .AddDatabase("SwingTraderDB");

// After (Azure, with azd)
var cosmos = builder.AddAzureCosmosDB("cosmos")
    .AddDatabase("SwingTraderDB");

// Before (local)
var scanner = builder.AddExecutable("scanner", "python", ...)

// After (Azure)
var scanner = builder.AddDockerfile("scanner", "../Scanner")
    .WithEnvironment("COSMOS_CONNECTION_STRING", cosmos.Resource.ConnectionStringExpression)
    // ... same env vars as before
```

**Key insight:** `cosmos.Resource.ConnectionStringExpression` resolves correctly in both modes. Aspire abstracts the difference.

### Deployment Command

```bash
# With azd CLI (requires azure.yaml and main.bicep)
azd up

# Aspire generates Azure resources via Bicep
# Scanner deployed as Azure Container App
# Cosmos DB provisioned as managed service
```

See [26-azure-containerization-and-azd.md](26-azure-containerization-and-azd.md) for complete deployment guide.

---

## Summary

### Key Decisions

1. **Aspire AppHost is pure orchestration** — zero business logic
2. **AddExecutable() for local Python scanner** — fast iteration, no Docker build
3. **Cosmos emulator with persistent volume** — data survives restarts
4. **WaitFor() enforces startup order** — scanner waits for Cosmos readiness
5. **Environment variable contract** — same variables locally and in Azure
6. **User Secrets for local development** — never commit secrets
7. **One-command startup** — `dotnet run --project src/AppHost`

### What This Enables

- **Developer productivity:** Edit Python code, restart scanner, see results in seconds
- **Production parity:** Same config contract locally and in Azure
- **Observability:** Aspire dashboard shows logs, health, dependencies
- **Easy onboarding:** Clone repo, set secrets, run command, start coding

### Next Steps

1. **Implement Python scanner bootstrap** → [19-python-scanner-bootstrap-implementation.md](19-python-scanner-bootstrap-implementation.md)
2. **Build Cosmos repository layer** → [20-cosmos-repository-implementation.md](20-cosmos-repository-implementation.md)
3. **Test local workflow end-to-end** → [25-local-development-workflow.md](25-local-development-workflow.md)

---

## References

- [.NET Aspire documentation](https://learn.microsoft.com/en-us/dotnet/aspire/)
- [Aspire.Hosting.Azure.CosmosDB package](https://www.nuget.org/packages/Aspire.Hosting.Azure.CosmosDB)
- [Cosmos DB Emulator](https://learn.microsoft.com/en-us/azure/cosmos-db/docker-emulator-linux)
- [12-dotnet-aspire-orchestration.md](12-dotnet-aspire-orchestration.md) — Aspire concepts and capabilities
- [15-security-and-secrets-management.md](15-security-and-secrets-management.md) — Secrets strategy
- [26-azure-containerization-and-azd.md](26-azure-containerization-and-azd.md) — Production deployment
