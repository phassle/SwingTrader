# 12 - .NET Aspire for Local Development Orchestration

> Research date: 2026-03-08
> Goal: Evaluate .NET Aspire as a local development orchestrator for the SwingTrader project — a Python-based scanner with Cosmos DB and a Streamlit dashboard. Covers what Aspire does, how it handles non-.NET services, comparison with docker-compose, and a clear recommendation.
> Prerequisite: Read [11-azure-cosmos-db-evaluation.md](11-azure-cosmos-db-evaluation.md) for the Cosmos DB context, and [08-docker-compose-hosting-alternatives.md](08-docker-compose-hosting-alternatives.md) for the docker-compose baseline.

---

## Table of Contents

1. [What .NET Aspire Does](#1-what-net-aspire-does)
2. [Can Aspire Orchestrate Non-.NET Services?](#2-can-aspire-orchestrate-non-net-services)
3. [Aspire + Cosmos DB Emulator](#3-aspire--cosmos-db-emulator)
4. [Architecture with Aspire](#4-architecture-with-aspire)
5. [What the Aspire Dashboard Gives You](#5-what-the-aspire-dashboard-gives-you)
6. [Local Development Workflow](#6-local-development-workflow)
7. [Aspire for Azure Deployment](#7-aspire-for-azure-deployment)
8. [Project Structure with Aspire](#8-project-structure-with-aspire)
9. [Aspire vs Docker Compose (Honest Comparison)](#9-aspire-vs-docker-compose-honest-comparison)
10. [Hybrid Approach](#10-hybrid-approach)
11. [Getting Started with Aspire](#11-getting-started-with-aspire)
12. [Potential Issues](#12-potential-issues)
13. [Recommendation](#13-recommendation)

---

## 1. What .NET Aspire Does

.NET Aspire is essentially a **smart docker-compose with a beautiful dashboard**. It is a local development orchestrator that knows how to spin up distributed applications — multiple services, databases, message queues, caches — and wire them together with minimal configuration.

### Core Capabilities

- **Service orchestration:** Starts all your services in the right order with dependency management.
- **Service discovery:** Services find each other by name, not by hardcoded ports.
- **Health checks:** Built-in liveness and readiness probes for every resource.
- **Centralized logging:** All service logs stream into a single dashboard.
- **Distributed tracing:** OpenTelemetry traces across services, visualized in the dashboard.
- **Metrics:** Resource metrics (CPU, memory) for every container and process.
- **Azure resource provisioning:** Built-in integrations for Cosmos DB, Service Bus, Storage, Redis, PostgreSQL, and more.

### What Makes It Different from Docker Compose

Docker Compose starts containers. That is it. Aspire starts containers AND gives you:

- A real-time dashboard with logs, traces, and metrics.
- Automatic connection string injection — no manually wiring environment variables.
- Native Azure resource emulators (Cosmos DB, Storage, Service Bus).
- A deployment path to Azure with `azd up`.

The trade-off: you need the .NET SDK installed. For a .NET developer, this is already on the machine. For a Python-only developer, it is extra baggage.

---

## 2. Can Aspire Orchestrate Non-.NET Services?

**Yes.** This is the key question for SwingTrader since the scanner is Python, not C#. Aspire supports three mechanisms for running non-.NET workloads:

### `AddDockerfile()`

Build and run a Dockerfile directly:

```csharp
var scanner = builder.AddDockerfile("scanner", "../src")
    .WithHttpEndpoint(port: 8080, targetPort: 8080);
```

Aspire builds the image from `../src/Dockerfile` and runs it as a container. This is the most common approach for non-.NET services.

### `AddContainer()`

Run a pre-built container image:

```csharp
var scanner = builder.AddContainer("scanner", "swingtrader-scanner", "latest")
    .WithHttpEndpoint(port: 8080, targetPort: 8080);
```

Use this when you already have a published image (e.g., from a CI build or a registry).

### `AddExecutable()`

Run any executable directly on the host — no Docker required:

```csharp
var scanner = builder.AddExecutable("scanner", "python", "../src", "main.py")
    .WithEnvironment("COSMOS_CONNECTION_STRING", cosmos);
```

This runs `python main.py` in the `../src` directory. Useful for quick iteration without rebuilding a Docker image every time. The downside: it assumes Python is installed on the host.

### Bottom Line

A Python scanner works fine under Aspire. You have options ranging from "run the executable directly" to "build the Dockerfile." The connection strings and environment variables are injected the same way regardless of the service language.

---

## 3. Aspire + Cosmos DB Emulator

This is where Aspire really shines compared to docker-compose. The Cosmos DB emulator integration is a one-liner.

### With Aspire

```csharp
var cosmos = builder.AddAzureCosmosDB("cosmos")
    .RunAsEmulator();
```

That is it. Aspire:

1. Pulls and starts the Cosmos DB emulator container.
2. Waits for it to be healthy (the emulator takes 30-60 seconds to start).
3. Generates the connection string.
4. Makes it available to any service that references `cosmos`.

No manual container configuration. No hunting for the right emulator image tag. No self-signed certificate nonsense. No hardcoded connection strings in `.env` files.

### With Docker Compose (for Comparison)

```yaml
services:
  cosmos-emulator:
    image: mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest
    ports:
      - "8081:8081"
      - "10250-10255:10250-10255"
    environment:
      - AZURE_COSMOS_EMULATOR_PARTITION_COUNT=10
      - AZURE_COSMOS_EMULATOR_ENABLE_DATA_PERSISTENCE=true
      - AZURE_COSMOS_EMULATOR_IP_ADDRESS_OVERRIDE=127.0.0.1
    volumes:
      - cosmos-data:/tmp/cosmos/appdata
```

Then you manually set the connection string in every service that needs it:

```yaml
  scanner:
    environment:
      - COSMOS_CONNECTION_STRING=AccountEndpoint=https://localhost:8081/;AccountKey=C2y6yDj...
```

Aspire eliminates this entire class of "wiring" work.

### Emulator Limitations (Same Regardless of Orchestrator)

- The Cosmos DB Linux emulator requires ~2 GB RAM.
- It only supports the NoSQL API.
- Performance is not representative of production.
- Data persistence depends on volume mounts (Aspire handles this).

---

## 4. Architecture with Aspire

### AppHost Project (C# — The Orchestrator)

This is the only .NET code in the entire project. It is purely an orchestration manifest — no business logic.

```
SwingTrader.AppHost/
├── Program.cs                          # Defines all services and resources
├── SwingTrader.AppHost.csproj          # References Aspire packages
```

### Python Scanner (Unchanged)

```
src/
├── main.py
├── scanner/
│   ├── data_fetcher.py
│   ├── signal_engine.py
│   └── cosmos_repository.py
├── requirements.txt
└── Dockerfile
```

The Python code does not change. It reads connection strings from environment variables, which is what it would do in any deployment model.

### Streamlit Dashboard (Unchanged)

```
dashboard/
├── app.py
├── requirements.txt
└── Dockerfile
```

### Program.cs — The Complete Orchestrator

```csharp
var builder = DistributedApplication.CreateBuilder(args);

// --- Cosmos DB Emulator ---
// Starts the emulator container automatically.
// In production (azd up), this becomes a real Azure Cosmos DB account.
var cosmos = builder.AddAzureCosmosDB("cosmos")
    .RunAsEmulator(config =>
    {
        config.WithLifetime(ContainerLifetime.Persistent); // Survives restarts
    });

// Get a reference to a specific database
var cosmosDb = cosmos.AddDatabase("swingtrader-db");

// --- Python Scanner ---
// Built from src/Dockerfile. Connection string injected as env var.
var scanner = builder.AddDockerfile("scanner", "../src")
    .WithReference(cosmosDb)
    .WithEnvironment("COSMOS_DATABASE_NAME", "swingtrader-db")
    .WithEnvironment("SCAN_INTERVAL_MINUTES", "60")
    .WithEnvironment("MARKET", "OMXS")
    .WaitFor(cosmos); // Don't start until Cosmos is ready

// --- Streamlit Dashboard ---
// Built from dashboard/Dockerfile. Reads from the same Cosmos DB.
var dashboard = builder.AddDockerfile("dashboard", "../dashboard")
    .WithReference(cosmosDb)
    .WithEnvironment("COSMOS_DATABASE_NAME", "swingtrader-db")
    .WithHttpEndpoint(port: 8501, targetPort: 8501, name: "dashboard-ui")
    .WaitFor(cosmos);

builder.Build().Run();
```

### How Connection Strings Reach Python

When you call `.WithReference(cosmosDb)`, Aspire injects an environment variable into the container. The exact variable name follows the convention:

```
ConnectionStrings__cosmos=AccountEndpoint=https://...;AccountKey=...
```

In your Python code, you read it:

```python
import os

connection_string = os.environ.get("ConnectionStrings__cosmos")
# or if you prefer a custom name:
# connection_string = os.environ.get("COSMOS_CONNECTION_STRING")
```

If you want a custom environment variable name instead:

```csharp
var scanner = builder.AddDockerfile("scanner", "../src")
    .WithEnvironment("COSMOS_CONNECTION_STRING", cosmos.Resource.ConnectionStringExpression)
    .WithEnvironment("COSMOS_DATABASE_NAME", "swingtrader-db");
```

### Alternative: Scanner as Executable (No Docker)

For faster iteration during development, skip the Docker build:

```csharp
var scanner = builder.AddExecutable("scanner", "python", "../src", "main.py")
    .WithReference(cosmosDb)
    .WithEnvironment("COSMOS_DATABASE_NAME", "swingtrader-db")
    .WaitFor(cosmos);
```

This runs `python main.py` directly on the host. Faster startup, but requires Python and dependencies to be installed locally.

---

## 5. What the Aspire Dashboard Gives You

The Aspire dashboard is the single biggest reason to use Aspire over docker-compose. It runs at `https://localhost:15888` and provides:

### Structured Logs

All services stream their stdout/stderr into the dashboard. You see logs from the scanner, dashboard, and Cosmos emulator in one view. You can filter by service, severity, and search for text.

Compare to docker-compose: `docker compose logs -f` gives you interleaved output with no filtering. Aspire gives you a real log viewer.

### Distributed Tracing

If your Python services emit OpenTelemetry traces (using `opentelemetry-sdk`), they appear as waterfall diagrams in the dashboard. You can see a request flow from the dashboard → Cosmos DB and identify bottlenecks.

This requires adding OpenTelemetry instrumentation to the Python code — it is not automatic for non-.NET services. But the Aspire dashboard is ready to receive the traces.

### Resource Health

Each service shows its status: Starting, Running, Healthy, Unhealthy, Stopped. You see at a glance if the Cosmos emulator is still initializing or if the scanner crashed.

### Environment Variables

Click on any service and see its environment variables. Useful for verifying that connection strings were injected correctly.

### Resource Metrics

CPU, memory, and network metrics for each container. Not as detailed as Prometheus/Grafana, but enough for local development.

### Console Output

Raw console output for each service, with color support. Essentially a multi-tab terminal view.

---

## 6. Local Development Workflow

### With Aspire

```bash
# One command starts everything
dotnet run --project SwingTrader.AppHost
```

What happens:

1. Aspire starts the Cosmos DB emulator (pulls image on first run).
2. Waits for Cosmos to be healthy (~30-60 seconds first time).
3. Builds and starts the Python scanner container.
4. Builds and starts the Streamlit dashboard container.
5. Opens the Aspire dashboard at `https://localhost:15888`.

Your development loop:

1. Open `https://localhost:15888` — see all services running.
2. Click on "scanner" to see its logs in real-time.
3. Scanner writes signals to Cosmos emulator.
4. Open `http://localhost:8501` — Streamlit dashboard shows signals.
5. Make a code change to the scanner.
6. Stop with Ctrl+C, re-run `dotnet run --project SwingTrader.AppHost`.
7. Everything restarts cleanly. Cosmos data persists (if using persistent lifetime).

### With Docker Compose (for Comparison)

```bash
docker compose up --build
```

Your development loop:

1. Check `docker compose logs -f scanner` for scanner output.
2. Check `docker compose logs -f dashboard` for dashboard output.
3. Open `http://localhost:8501` for the dashboard.
4. No centralized log viewer. No health dashboard. No trace viewer.
5. Stop with Ctrl+C, re-run `docker compose up --build`.
6. Cosmos connection string is hardcoded in `.env`.

### The Difference

Aspire's workflow is marginally slower on first start (downloading emulator image, building containers), but the dashboard experience is significantly better for ongoing development. You get a single pane of glass instead of multiple terminal tabs.

---

## 7. Aspire for Azure Deployment

This is where Aspire goes from "nice to have" to "significant advantage." The same `Program.cs` that defines your local environment can deploy to Azure.

### How It Works

```bash
# Initialize Azure Developer CLI
azd init

# Deploy everything
azd up
```

Aspire translates your local resources to Azure services:

| Local (Aspire) | Azure (azd up) |
|----------------|-----------------|
| `AddAzureCosmosDB().RunAsEmulator()` | Azure Cosmos DB account (serverless) |
| `AddDockerfile("scanner", ...)` | Azure Container Apps (scanner) |
| `AddDockerfile("dashboard", ...)` | Azure Container Apps (dashboard) |

### What `azd up` Does

1. Generates Bicep/ARM templates from your Aspire manifest.
2. Creates an Azure Container Registry (ACR).
3. Builds and pushes your Docker images to ACR.
4. Provisions Cosmos DB (serverless mode by default).
5. Creates Container Apps for each service.
6. Wires connection strings automatically.
7. Sets up managed identities for secure access.

### No Separate IaC Needed

This is the killer feature. Without Aspire, you would need to:

- Write Bicep/Terraform for Cosmos DB.
- Write Bicep/Terraform for Container Apps.
- Configure container registry.
- Wire connection strings manually.
- Set up managed identities.

With Aspire, all of that is derived from `Program.cs`. One source of truth for local and cloud.

### Customizing the Azure Deployment

You can fine-tune the Azure resources in `Program.cs`:

```csharp
var cosmos = builder.AddAzureCosmosDB("cosmos")
    .RunAsEmulator() // Local: use emulator
    .ConfigureInfrastructure(infra =>
    {
        var cosmosAccount = infra.GetProvisionableResources()
            .OfType<CosmosDBAccount>()
            .Single();
        cosmosAccount.ConsistencyPolicy = new ConsistencyPolicy
        {
            DefaultConsistencyLevel = DefaultConsistencyLevel.Session
        };
    });
```

---

## 8. Project Structure with Aspire

```
SwingTrader/
├── research/                           # Research files (you are here)
│   └── technical-implementation/
├── SwingTrader.AppHost/                # Aspire orchestrator (C#)
│   ├── Program.cs                      # Service definitions
│   └── SwingTrader.AppHost.csproj      # Aspire NuGet packages
├── src/                                # Python scanner (unchanged)
│   ├── main.py
│   ├── scanner/
│   │   ├── data_fetcher.py
│   │   ├── signal_engine.py
│   │   └── cosmos_repository.py
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard/                          # Streamlit dashboard (unchanged)
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── data/                               # Local data (gitignored)
├── docker-compose.yml                  # Fallback: run without .NET SDK
├── .env.example                        # Env vars documentation
├── SwingTrader.sln                     # Solution file (only AppHost)
└── .gitignore
```

### The AppHost .csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <IsAspireHost>true</IsAspireHost>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Aspire.Hosting.AppHost" Version="9.1.0" />
    <PackageReference Include="Aspire.Hosting.Azure.CosmosDB" Version="9.1.0" />
  </ItemGroup>

</Project>
```

### The Solution File

```
SwingTrader.sln
└── SwingTrader.AppHost/
```

That is the entire .NET footprint. One project, one `.sln`, two NuGet packages.

---

## 9. Aspire vs Docker Compose (Honest Comparison)

| Factor | Aspire | Docker Compose |
|--------|--------|----------------|
| **Setup effort** | Need .NET 9 SDK + Aspire workload | Just `docker-compose.yml` |
| **Dashboard** | Beautiful built-in (logs, traces, metrics) | None (or add Portainer/Dozzle) |
| **Cosmos emulator** | One line: `RunAsEmulator()` | Manual container config + env vars |
| **Service discovery** | Automatic by resource name | Manual environment variables |
| **Connection strings** | Automatically injected | Hardcoded in `.env` |
| **Health checks** | Built-in, visible in dashboard | Manual `healthcheck:` config |
| **Azure deployment** | `azd up` — generates IaC from manifest | Need separate Bicep/Terraform |
| **Non-.NET services** | Supported but less ergonomic | Native — it is all containers |
| **Startup time** | Slightly slower (Aspire overhead) | Faster for simple setups |
| **Learning curve** | Familiar if you know Aspire | Everyone knows docker-compose |
| **Runs without .NET** | No — requires .NET 9 SDK | Yes — just Docker |
| **Hot reload** | Not automatic for Dockerfiles | Not automatic either |
| **Documentation** | Good for .NET, sparse for non-.NET | Extensive, battle-tested |
| **Maturity** | GA since .NET 9 but still young | Decade of production use |
| **Cost** | Free (open source) | Free (open source) |

### Where Aspire Wins Clearly

- **Cosmos DB emulator integration.** This alone saves 30+ minutes of setup and ongoing headaches with connection strings.
- **The dashboard.** Having logs, health, and traces in one view is a genuine productivity improvement.
- **Azure deployment path.** If you are deploying to Azure anyway, `azd up` is dramatically simpler than writing IaC.

### Where Docker Compose Wins Clearly

- **No .NET dependency.** A Python project that requires .NET SDK just for orchestration feels wrong to some developers.
- **Portability.** Any developer on any OS with Docker can run `docker compose up`. No workload installs needed.
- **Documentation quality.** Docker Compose has been around for 10+ years. Every problem has a Stack Overflow answer.

---

## 10. Hybrid Approach

The pragmatic answer is: use both.

### Aspire for Local Development

- Better developer experience with the dashboard.
- Cosmos emulator "just works."
- Service discovery and connection string injection.
- You already know Aspire from other projects.

### Docker Compose as Portable Fallback

- Works without .NET SDK (anyone can run it).
- Useful for CI/CD pipelines that do not have .NET installed.
- Keeps the project accessible to Python-only contributors.

### `azd` for Azure Deployment

- Generates infrastructure from the Aspire manifest.
- Single command deployment.
- Consistent between local and cloud.

### The Python Code Does Not Change

This is the critical point. The Python scanner reads its configuration from environment variables:

```python
import os

COSMOS_CONNECTION_STRING = os.environ["ConnectionStrings__cosmos"]
COSMOS_DATABASE_NAME = os.environ.get("COSMOS_DATABASE_NAME", "swingtrader-db")
SCAN_INTERVAL = int(os.environ.get("SCAN_INTERVAL_MINUTES", "60"))
```

Whether those environment variables come from Aspire, docker-compose, or Azure Container Apps — the Python code does not care. The orchestration layer is completely decoupled from the application code.

---

## 11. Getting Started with Aspire

### Step 1: Install Prerequisites

```bash
# Install .NET 9 SDK (if not already installed)
# macOS:
brew install dotnet-sdk

# Verify version
dotnet --version  # Should be 9.0.x or later

# Install Aspire workload
dotnet workload install aspire

# Verify Aspire
dotnet workload list  # Should show "aspire"
```

### Step 2: Create the Solution and AppHost

```bash
cd /path/to/SwingTrader

# Create solution file
dotnet new sln -n SwingTrader

# Create AppHost project
mkdir SwingTrader.AppHost
cd SwingTrader.AppHost
dotnet new aspire-apphost -n SwingTrader.AppHost

# Add Cosmos DB hosting package
dotnet add package Aspire.Hosting.Azure.CosmosDB

# Add project to solution
cd ..
dotnet sln add SwingTrader.AppHost/SwingTrader.AppHost.csproj
```

### Step 3: Write Program.cs

Replace the generated `Program.cs` with:

```csharp
var builder = DistributedApplication.CreateBuilder(args);

// Cosmos DB — emulator locally, real Cosmos DB in Azure
var cosmos = builder.AddAzureCosmosDB("cosmos")
    .RunAsEmulator(config =>
    {
        config.WithLifetime(ContainerLifetime.Persistent);
    });

var cosmosDb = cosmos.AddDatabase("swingtrader-db");

// Python scanner — built from src/Dockerfile
var scanner = builder.AddDockerfile("scanner", "../src")
    .WithReference(cosmosDb)
    .WithEnvironment("COSMOS_DATABASE_NAME", "swingtrader-db")
    .WithEnvironment("SCAN_INTERVAL_MINUTES", "60")
    .WithEnvironment("MARKET", "OMXS")
    .WaitFor(cosmos);

// Streamlit dashboard — built from dashboard/Dockerfile
var dashboard = builder.AddDockerfile("dashboard", "../dashboard")
    .WithReference(cosmosDb)
    .WithEnvironment("COSMOS_DATABASE_NAME", "swingtrader-db")
    .WithHttpEndpoint(port: 8501, targetPort: 8501, name: "dashboard-ui")
    .WaitFor(cosmos);

builder.Build().Run();
```

### Step 4: Verify Project Structure

```
SwingTrader/
├── SwingTrader.sln
├── SwingTrader.AppHost/
│   ├── Program.cs
│   └── SwingTrader.AppHost.csproj
├── src/
│   ├── Dockerfile    # Must exist
│   └── ...
└── dashboard/
    ├── Dockerfile    # Must exist
    └── ...
```

### Step 5: Ensure Dockerfiles Exist

The scanner and dashboard need Dockerfiles. Aspire builds them.

**`src/Dockerfile`** (example):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

**`dashboard/Dockerfile`** (example):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Step 6: Run It

```bash
dotnet run --project SwingTrader.AppHost
```

First run will:

1. Pull the Cosmos DB emulator image (~2 GB).
2. Build the scanner and dashboard Docker images.
3. Start everything.
4. Print the Aspire dashboard URL.

Open `https://localhost:15888` to see the dashboard.

### Step 7: Verify

- Aspire dashboard shows three resources: `cosmos`, `scanner`, `dashboard`.
- Scanner logs show it connecting to the Cosmos emulator.
- Dashboard at `http://localhost:8501` loads and reads from Cosmos.
- All logs visible in the Aspire dashboard.

---

## 12. Potential Issues

### .NET SDK Required for Orchestration

The Python scanner has zero .NET code. Adding a .NET SDK dependency purely for orchestration feels disproportionate. If you are the only developer and you already have .NET installed, this is a non-issue. If others need to contribute, it raises the barrier.

### Aspire Is Still Evolving

Aspire went GA with .NET 9, but the non-.NET container support (`AddDockerfile`, `AddContainer`) is newer and less battle-tested. Breaking changes between minor versions are possible. The Aspire team ships updates frequently — this is both good (fast fixes) and bad (things move).

### Cosmos DB Emulator Is Resource-Heavy

The Linux Cosmos DB emulator uses approximately 2 GB of RAM. If you are running this on a Hetzner CX22 (4 GB RAM) that is also running Coolify, you will be tight on resources. For local development on a MacBook, this is fine.

### Non-.NET Container Documentation Is Sparse

Most Aspire documentation assumes you are orchestrating .NET services. The `AddDockerfile()` and `AddExecutable()` APIs are documented, but examples are overwhelmingly .NET-centric. Expect to do some experimentation for edge cases (volume mounts, custom networking, multi-stage builds).

### No Hot Reload for Dockerfiles

When you change Python code, you need to stop and restart `dotnet run --project SwingTrader.AppHost` to rebuild the Docker image. This is the same limitation as docker-compose. For faster iteration, use `AddExecutable()` during development and switch to `AddDockerfile()` when you want the full containerized experience.

### First Run Is Slow

Pulling the Cosmos emulator image and building Docker images takes time on the first run. Subsequent runs are fast because images are cached. Expect 5-10 minutes for the initial setup.

---

## 13. Recommendation

### If You Already Know Aspire: Use It

You are a .NET developer. You have the SDK installed. You know how Aspire works from other projects. The Cosmos DB emulator integration alone justifies it — one line of C# instead of manually configuring the emulator container and wiring connection strings.

The Aspire dashboard is a genuine improvement over `docker compose logs`. And the `azd up` deployment path means your local setup translates directly to Azure infrastructure without writing a single line of Bicep.

### Keep Docker Compose as Fallback

Maintain a `docker-compose.yml` that does the same thing without Aspire. This ensures:

- Anyone without .NET SDK can still run the project.
- CI/CD pipelines can use docker-compose for integration tests.
- You are not locked into Aspire if it does not work out.

### Do Not Over-Engineer

The AppHost is ~20 lines of C#. It should stay that way. Aspire is the orchestrator, not the application. If you find yourself writing business logic in C# or adding .NET service projects, you have gone too far. The scanner is Python, the dashboard is Python, and the orchestration is a thin C# shell.

### Summary Decision Matrix

| Scenario | Use |
|----------|-----|
| Daily local development | Aspire (better DX, Cosmos emulator) |
| CI/CD integration tests | Docker Compose (no .NET dependency) |
| Deploy to Azure | `azd up` from Aspire manifest |
| Quick demo for someone without .NET | Docker Compose |
| Production on Hetzner/Coolify | Docker Compose |

The two approaches are not mutually exclusive. Use Aspire where it adds value (local dev, Azure deploy) and docker-compose where it is simpler (CI, portability).
