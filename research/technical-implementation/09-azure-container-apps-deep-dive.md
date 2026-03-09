# 09 - Azure Container Apps Deep Dive

> Research date: 2026-03-08
> Goal: Complete implementation guide for running the SwingTrader Python scanner on Azure Container Apps using Docker. Covers every step from Dockerfile to CI/CD to monitoring.
> Prerequisite: Read [07-azure-hosting.md](07-azure-hosting.md) for the general Azure overview. This document goes deeper on the Container Apps path specifically.

---

## Table of Contents

1. [Azure Container Apps Overview](#1-azure-container-apps-overview)
2. [Prerequisites](#2-prerequisites)
3. [Project Structure for Azure Container Apps](#3-project-structure-for-azure-container-apps)
4. [Dockerfile (Production-Ready)](#4-dockerfile-production-ready)
5. [Persistent Storage for SQLite](#5-persistent-storage-for-sqlite)
6. [Container Apps Job Configuration](#6-container-apps-job-configuration)
7. [Environment Variables and Secrets](#7-environment-variables-and-secrets)
8. [Container Registry Setup](#8-container-registry-setup)
9. [CI/CD with GitHub Actions](#9-cicd-with-github-actions)
10. [Adding a Dashboard Later](#10-adding-a-dashboard-later)
11. [Monitoring and Logging](#11-monitoring-and-logging)
12. [Cost Analysis (Detailed)](#12-cost-analysis-detailed)
13. [Complete Step-by-Step Deployment](#13-complete-step-by-step-deployment)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Azure Container Apps Overview

Azure Container Apps is a managed serverless container platform built on top of Kubernetes (specifically Azure Kubernetes Service with KEDA and Dapr). You never see or manage the underlying Kubernetes cluster. You give it a Docker image and configuration, and it runs your container.

### Key Concepts

**Container Apps Environment:** A shared boundary for a group of container apps. All apps in the same environment share a virtual network and Log Analytics workspace. Think of it as a lightweight cluster. You typically create one environment per project or per environment (dev/prod).

**Container Apps (Apps):** Long-running services. Web servers, APIs, dashboards. They can scale to zero when there is no traffic (you pay nothing when scaled to zero) and scale up automatically when requests come in. Ingress (HTTP traffic) is built in with automatic HTTPS.

**Container Apps Jobs:** Run-to-completion tasks. They start, do their work, and exit. Three trigger types:
- **Schedule:** CRON-based, like a cron job. This is what the SwingTrader scanner uses.
- **Event-driven:** Triggered by messages in a queue, new blobs, etc.
- **Manual:** Triggered via API or CLI on demand.

### Why Container Apps Jobs for SwingTrader

The scanner workload is a perfect fit for a Container Apps Job with a scheduled trigger:

- Runs once daily after market close (18:15 CET)
- Takes 1-5 minutes to complete
- Needs no inbound HTTP traffic (it sends outbound Telegram messages)
- Should not run at all the other 23 hours and 55 minutes of the day
- Pay only for the seconds it actually runs (consumption billing)

A Container Apps App (not Job) would also work but is designed for long-running services. Using a Job is semantically correct and gives you built-in scheduling, retry policies, and execution history.

### Consumption vs Dedicated Plans

**Consumption plan (recommended for SwingTrader):**
- Pay per vCPU-second and GiB-second of actual usage
- No minimum charge when nothing runs
- Jobs only incur cost during execution
- Free grants: 180,000 vCPU-seconds and 360,000 GiB-seconds per month (per subscription)
- A 5-minute daily job uses ~6,600 vCPU-seconds/month — well within the free grant

**Dedicated plan:**
- Reserved compute (D4/D8/D16 workload profiles)
- Makes sense for always-on workloads with predictable load
- Minimum cost even when idle
- Not needed for SwingTrader

### docker-compose and Container Apps

Azure Container Apps does not natively run `docker-compose.yml` files in production. Docker Compose is for local development. For Azure deployment, you:

1. Use `docker-compose.yml` locally for development and testing
2. Deploy individual containers to Container Apps using Azure CLI, Bicep, or GitHub Actions
3. Each service in docker-compose becomes either a Container Apps Job or a Container Apps App

The mental model: docker-compose is your local runtime, Azure Container Apps is your production runtime. Same Docker images, different orchestration.

---

## 2. Prerequisites

### Required Tools

```bash
# Azure CLI (macOS)
brew install azure-cli

# Docker Desktop (macOS)
brew install --cask docker

# Verify installations
az --version    # Should be 2.60+ (2026)
docker --version
docker compose version
```

### Azure Subscription

If you do not have one:

```bash
# Create a free Azure account (includes $200 credit for 30 days)
# Go to: https://azure.microsoft.com/free/

# Or if you have Visual Studio / MSDN, you may already have monthly credits
```

### Login and Set Defaults

```bash
# Login to Azure
az login

# List subscriptions and set the one you want
az account list --output table
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Install the Container Apps extension (if not already installed)
az extension add --name containerapp --upgrade

# Register required providers (one-time, may take a minute)
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
```

---

## 3. Project Structure for Azure Container Apps

```
SwingTrader/
├── src/                        # Python source code
│   ├── main.py                 # Entry point (works locally: python src/main.py)
│   ├── scanner.py              # Core scanning logic
│   ├── notifier.py             # Telegram notifications
│   └── db.py                   # SQLite database access
├── data/                       # Local SQLite database directory
│   └── swingtrader.db          # SQLite file (git-ignored)
├── Dockerfile                  # Production Docker image
├── docker-compose.yml          # Local development with Docker
├── requirements.txt            # Python dependencies
├── .env                        # Local secrets (git-ignored)
├── .env.example                # Template for .env (committed)
├── .github/
│   └── workflows/
│       └── deploy-azure.yml    # CI/CD pipeline
└── infra/
    └── azure/
        ├── deploy.sh           # One-shot deployment script
        └── job.bicep            # Infrastructure as Code (optional)
```

### docker-compose.yml (Local Development)

```yaml
services:
  scanner:
    build: .
    volumes:
      - ./data:/app/data       # Mount local data directory for SQLite
    env_file: .env              # Load secrets from .env file
    # No ports needed — scanner is a batch job, not a web server
```

### .env.example

```bash
# Copy to .env and fill in real values
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
DATABASE_PATH=/app/data/swingtrader.db
```

### Running Locally Without Docker

The app must work without Docker for quick development:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (or source .env)
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id
export DATABASE_PATH=./data/swingtrader.db

# Run
python src/main.py
```

### Running Locally With Docker

```bash
# Build and run
docker compose up --build

# Or run in detached mode
docker compose up --build -d
docker compose logs -f scanner
```

---

## 4. Dockerfile (Production-Ready)

```dockerfile
# =============================================================================
# Stage 1: Build stage — install dependencies in a clean environment
# =============================================================================
FROM python:3.12-slim AS builder

# Prevents Python from writing .pyc files and enables unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies that some Python packages need (e.g., numpy, pandas)
# These are only needed during pip install, not at runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements first — Docker layer caching means this layer
# is only rebuilt when requirements.txt changes, not on every code change
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# =============================================================================
# Stage 2: Runtime stage — slim image with only what we need
# =============================================================================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /install /usr/local

# Create a non-root user for security
# Running as root in a container is a security risk — if someone exploits
# a vulnerability, they get root access to the container
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser src/ ./src/

# Switch to non-root user
USER appuser

# Default database path (can be overridden by environment variable)
ENV DATABASE_PATH=/app/data/swingtrader.db

# Health check — verifies the Python environment is working
# For a batch job this is less critical than for a web server, but
# it helps catch broken images early
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import yfinance; import pandas; print('ok')" || exit 1

# Entry point — run the scanner
CMD ["python", "src/main.py"]
```

### Why Multi-Stage Build

The builder stage installs gcc and compiles native extensions (numpy, pandas). The runtime stage only contains the compiled packages and Python runtime. This reduces the final image size significantly:

- Single-stage with gcc: ~800 MB
- Multi-stage without gcc: ~350-400 MB

### Build and Test Locally

```bash
# Build the image
docker build -t swingtrader:latest .

# Test it runs correctly
docker run --rm \
    --env-file .env \
    -v "$(pwd)/data:/app/data" \
    swingtrader:latest

# Check image size
docker images swingtrader
```

---

## 5. Persistent Storage for SQLite

The scanner writes to a SQLite database (~15 MB). Container Apps Jobs are ephemeral — the container filesystem is destroyed after each run. The SQLite file must persist between runs.

### Option A: Azure Files Volume Mount (Recommended)

Azure Files is a managed file share service. You create a file share and mount it into the container as a volume. The container sees it as a normal directory. Files persist across container restarts and job executions.

#### Step 1: Create a Storage Account

```bash
# Variables — set these once
RESOURCE_GROUP="swingtrader-rg"
LOCATION="swedencentral"          # Closest Azure region to Stockholm
STORAGE_ACCOUNT="swingtraderst"   # Must be globally unique, 3-24 chars, lowercase+numbers only
FILE_SHARE="scanner-data"

# Create resource group (if not already created)
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION

# Create storage account
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2 \
    --min-tls-version TLS1_2

# Get the storage account key
STORAGE_KEY=$(az storage account keys list \
    --resource-group $RESOURCE_GROUP \
    --account-name $STORAGE_ACCOUNT \
    --query '[0].value' \
    --output tsv)

# Create the file share
az storage share create \
    --name $FILE_SHARE \
    --account-name $STORAGE_ACCOUNT \
    --account-key $STORAGE_KEY \
    --quota 1    # 1 GB quota (more than enough for a 15 MB SQLite file)
```

#### Step 2: Add Storage to the Container Apps Environment

```bash
ENVIRONMENT="swingtrader-env"

# Add the Azure Files storage to the Container Apps Environment
az containerapp env storage set \
    --name $ENVIRONMENT \
    --resource-group $RESOURCE_GROUP \
    --storage-name "scannerdata" \
    --azure-file-account-name $STORAGE_ACCOUNT \
    --azure-file-account-key $STORAGE_KEY \
    --azure-file-share-name $FILE_SHARE \
    --access-mode ReadWrite
```

#### Step 3: Mount in the Container Apps Job

When creating the job (Section 6), you add the volume mount to the container configuration. The mount maps the Azure Files share to `/app/data` inside the container — exactly the same path as in docker-compose.

The key YAML/JSON for the job template:

```json
{
    "volumes": [
        {
            "name": "scanner-data-volume",
            "storageName": "scannerdata",
            "storageType": "AzureFile"
        }
    ],
    "containers": [
        {
            "name": "scanner",
            "image": "your-registry/swingtrader:latest",
            "volumeMounts": [
                {
                    "volumeName": "scanner-data-volume",
                    "mountPath": "/app/data"
                }
            ]
        }
    ]
}
```

#### How It Works in Practice

1. Job triggers at 18:15 CET
2. Azure starts a container
3. Azure Files share is mounted at `/app/data`
4. The container reads `/app/data/swingtrader.db` (the SQLite file from yesterday's run)
5. Scanner runs, updates the database, writes new signals
6. Container exits
7. The Azure Files share retains the updated `swingtrader.db`
8. Tomorrow, step 1-7 repeats — the database grows over time

#### Performance Note

Azure Files uses SMB protocol over the network. For SQLite, which does frequent small reads and writes, this adds latency compared to local disk. However, for a scanner that runs once daily and does a modest number of database operations, the performance impact is negligible — you might add 1-2 seconds to the total runtime.

If performance ever becomes an issue (it will not for this workload), you could download the file to local disk at start, work on it locally, and upload it back at the end — which is Option B.

### Option B: Azure Blob Storage Download/Upload

Instead of mounting a volume, download the SQLite file from Blob Storage at the start of the job, work on it locally (in the container's ephemeral filesystem), and upload it back when done.

#### Python Wrapper Code

```python
"""
blob_storage.py — Download/upload SQLite from Azure Blob Storage.
Used when Azure Files volume mount is not available or not desired.
"""

import os
import shutil
from azure.storage.blob import BlobServiceClient


BLOB_CONNECTION_STRING = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
CONTAINER_NAME = "scanner-data"
BLOB_NAME = "swingtrader.db"
LOCAL_DB_PATH = "/app/data/swingtrader.db"


def download_db():
    """Download SQLite file from Blob Storage before the scan."""
    blob_service = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
    blob_client = blob_service.get_blob_client(
        container=CONTAINER_NAME, blob=BLOB_NAME
    )

    os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)

    try:
        with open(LOCAL_DB_PATH, "wb") as f:
            stream = blob_client.download_blob()
            stream.readinto(f)
        print(f"Downloaded {BLOB_NAME} from Blob Storage ({os.path.getsize(LOCAL_DB_PATH)} bytes)")
    except Exception as e:
        if "BlobNotFound" in str(e):
            print(f"No existing database found in Blob Storage — starting fresh")
        else:
            raise


def upload_db():
    """Upload SQLite file back to Blob Storage after the scan."""
    blob_service = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
    blob_client = blob_service.get_blob_client(
        container=CONTAINER_NAME, blob=BLOB_NAME
    )

    with open(LOCAL_DB_PATH, "rb") as f:
        blob_client.upload_blob(f, overwrite=True)

    print(f"Uploaded {BLOB_NAME} to Blob Storage ({os.path.getsize(LOCAL_DB_PATH)} bytes)")
```

Then wrap your main function:

```python
from blob_storage import download_db, upload_db

def main():
    download_db()
    try:
        run_scanner()   # Your existing scanner logic
    finally:
        upload_db()     # Always upload, even if scanner fails partway through
```

This approach requires the `azure-storage-blob` package in your `requirements.txt`:

```
azure-storage-blob>=12.0.0
```

### Comparison

| Aspect | Azure Files (Option A) | Blob Download/Upload (Option B) |
|--------|----------------------|-------------------------------|
| **Setup complexity** | Medium (storage + mount config) | Medium (code + connection string) |
| **Code changes** | None — same file path as local | Need download/upload wrapper |
| **Performance** | SMB over network (slight latency) | Local disk during scan (faster) |
| **Reliability** | Azure manages mount/unmount | Must handle upload failure |
| **Multi-container read** | Both containers can mount same share | Need to coordinate blob access |
| **Dashboard sharing** | Dashboard mounts same share, reads SQLite | Dashboard needs its own download logic |
| **Cost** | ~$0.10/month (Azure Files, 1 GB) | ~$0.02/month (Blob Storage, 1 GB) |

### Recommendation

**Use Option A (Azure Files volume mount).** It requires zero code changes — your container reads and writes `/app/data/swingtrader.db` exactly as it does locally. When you add a Streamlit dashboard later, it mounts the same share and reads the same file. The slight performance overhead is irrelevant for a daily batch job.

Option B is better if you are deploying to a platform that does not support volume mounts (like Azure Functions or Google Cloud Run). Since Container Apps supports volume mounts natively, there is no reason to add the complexity of download/upload.

---

## 6. Container Apps Job Configuration

### Trigger Type: Schedule

A scheduled Container Apps Job uses a CRON expression to define when it runs. The job creates a container execution at each scheduled time, runs to completion, and exits.

### CRON Expression and Timezone

Container Apps uses UTC for CRON expressions. Stockholm is in the CET/CEST timezone:

- **CET (Central European Time):** UTC+1 (November through March)
- **CEST (Central European Summer Time):** UTC+2 (March through October)

To run at 18:15 Stockholm time:
- During CET (winter): 18:15 CET = 16:15 UTC → CRON: `15 16 * * 1-5`
- During CEST (summer): 18:15 CEST = 16:15 UTC → CRON: `15 16 * * 1-5`

Wait — that is the same? No. Let me be precise:

- **CET (UTC+1):** 18:15 local = **17:15 UTC** → CRON: `15 17 * * 1-5`
- **CEST (UTC+2):** 18:15 local = **16:15 UTC** → CRON: `15 16 * * 1-5`

So the UTC offset changes between winter and summer. You have three options:

**Option 1: Pick one UTC time and accept the 1-hour shift (recommended)**

Set the CRON to `15 16 * * 1-5` (16:15 UTC). This means:
- Summer (CEST): runs at 18:15 Stockholm time (perfect)
- Winter (CET): runs at 17:15 Stockholm time (1 hour early)

Stockholm market closes at 17:30 CET in winter, so 17:15 is actually too early in winter. Better to use `15 17 * * 1-5` (17:15 UTC):
- Summer (CEST): runs at 19:15 Stockholm time (45 minutes after close, fine)
- Winter (CET): runs at 18:15 Stockholm time (45 minutes after close, fine)

This is the simplest approach and works well.

**Option 2: Update the CRON twice a year**

Change the schedule when DST switches. Tedious and error-prone.

**Option 3: Handle it in your Python code**

Set the CRON to run at 16:00 UTC (early enough for both seasons). In your Python code, check the current Stockholm time and sleep until 18:15 if needed:

```python
from datetime import datetime
import pytz
import time

def wait_for_market_close():
    stockholm_tz = pytz.timezone("Europe/Stockholm")
    now = datetime.now(stockholm_tz)
    target = now.replace(hour=18, minute=15, second=0, microsecond=0)

    if now < target:
        wait_seconds = (target - now).total_seconds()
        print(f"Waiting {wait_seconds:.0f} seconds until 18:15 Stockholm time...")
        time.sleep(wait_seconds)
```

This wastes a few minutes of container runtime (and billable seconds), but keeps the schedule timezone-correct year-round.

**Recommendation:** Use Option 1 with `15 17 * * 1-5`. Running 45 minutes after market close in both seasons is perfectly fine for a daily scanner — the data does not change after close.

### Creating the Container Apps Job

```bash
# Variables
RESOURCE_GROUP="swingtrader-rg"
ENVIRONMENT="swingtrader-env"
JOB_NAME="swingtrader-scanner"
REGISTRY="swingtraderacr.azurecr.io"    # Your ACR login server
IMAGE="${REGISTRY}/swingtrader:latest"

# Create the Container Apps Environment (if not already created)
az containerapp env create \
    --name $ENVIRONMENT \
    --resource-group $RESOURCE_GROUP \
    --location swedencentral

# Create the scheduled job
az containerapp job create \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT \
    --trigger-type "Schedule" \
    --cron-expression "15 17 * * 1-5" \
    --replica-timeout 600 \
    --replica-retry-limit 1 \
    --replica-completion-count 1 \
    --parallelism 1 \
    --image $IMAGE \
    --cpu 0.5 \
    --memory 1Gi \
    --registry-server $REGISTRY \
    --registry-username $(az acr credential show --name swingtraderacr --query username -o tsv) \
    --registry-password $(az acr credential show --name swingtraderacr --query "passwords[0].value" -o tsv)
```

### Configuration Options Explained

| Option | Value | Why |
|--------|-------|-----|
| `--trigger-type Schedule` | Schedule | CRON-triggered job |
| `--cron-expression "15 17 * * 1-5"` | 17:15 UTC, Mon-Fri | ~18:15 Stockholm time (see DST notes above) |
| `--replica-timeout 600` | 600 seconds (10 min) | Max time the container can run before it is killed. The scanner takes 1-5 minutes, so 10 minutes gives generous headroom. Increase if your scan grows. |
| `--replica-retry-limit 1` | 1 retry | If the job fails (non-zero exit code), retry once. Handles transient network errors (yfinance API flaky, Telegram timeout). Set to 0 for no retries. |
| `--replica-completion-count 1` | 1 | Number of successful completions needed. Always 1 for a simple job. |
| `--parallelism 1` | 1 | Number of replicas to run in parallel. Always 1 for this workload — you do not want two scanners running simultaneously and writing to the same SQLite file. |
| `--cpu 0.5` | 0.5 vCPU | Half a CPU core. Pandas and indicator calculations are not CPU-intensive for 100-200 stocks. 0.25 would also work but 0.5 gives comfort margin. |
| `--memory 1Gi` | 1 GB RAM | Pandas DataFrames for 200 stocks with 6 months of daily data fit comfortably in 200-300 MB. 1 GB gives generous headroom. |

### Adding the Volume Mount After Creation

If you created the storage mount on the environment (Section 5), add it to the job:

```bash
# Update the job to mount the Azure Files volume
az containerapp job update \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --yaml job-config.yaml
```

Where `job-config.yaml` contains:

```yaml
properties:
  template:
    volumes:
      - name: scanner-data-volume
        storageName: scannerdata
        storageType: AzureFile
    containers:
      - name: scanner
        image: swingtraderacr.azurecr.io/swingtrader:latest
        resources:
          cpu: 0.5
          memory: 1Gi
        volumeMounts:
          - volumeName: scanner-data-volume
            mountPath: /app/data
```

### Trigger a Manual Test Run

```bash
# Start the job manually (does not wait for the CRON schedule)
az containerapp job start \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP

# List recent executions
az containerapp job execution list \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --output table
```

---

## 7. Environment Variables and Secrets

### How Container Apps Secrets Work

Container Apps has a built-in secrets store. You define secrets at the app/job level, and reference them as environment variables in the container. Secrets are encrypted at rest and never exposed in logs or the Azure portal.

### Setting Secrets via Azure CLI

```bash
JOB_NAME="swingtrader-scanner"
RESOURCE_GROUP="swingtrader-rg"

# Set secrets (these are stored encrypted in Azure)
az containerapp job secret set \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --secrets \
        telegram-bot-token="your_actual_bot_token_here" \
        telegram-chat-id="your_actual_chat_id_here"
```

### Mapping Secrets to Environment Variables

When creating or updating the job, map secrets to environment variables:

```bash
az containerapp job update \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --set-env-vars \
        TELEGRAM_BOT_TOKEN=secretref:telegram-bot-token \
        TELEGRAM_CHAT_ID=secretref:telegram-chat-id \
        DATABASE_PATH=/app/data/swingtrader.db
```

The `secretref:` prefix tells Container Apps to inject the value from the named secret. Non-secret environment variables (like `DATABASE_PATH`) are set as plain text.

### Mapping from Local .env to Azure Secrets

| Local .env Variable | Azure Secret Name | Azure Env Var |
|---------------------|-------------------|---------------|
| `TELEGRAM_BOT_TOKEN=abc123` | `telegram-bot-token` | `TELEGRAM_BOT_TOKEN=secretref:telegram-bot-token` |
| `TELEGRAM_CHAT_ID=456` | `telegram-chat-id` | `TELEGRAM_CHAT_ID=secretref:telegram-chat-id` |
| `DATABASE_PATH=./data/swingtrader.db` | (not a secret) | `DATABASE_PATH=/app/data/swingtrader.db` |

### Listing and Updating Secrets

```bash
# List all secrets (shows names only, not values — values are never exposed)
az containerapp job secret list \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --output table

# Update a secret value
az containerapp job secret set \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --secrets telegram-bot-token="new_token_value"

# Remove a secret
az containerapp job secret remove \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --secret-names telegram-bot-token
```

### Important: Secrets Require a New Revision

After updating a secret value, the running job already references the secret by name. The new value takes effect on the next job execution — no need to restart anything for a scheduled job. The container is created fresh each time, and it pulls the latest secret values.

---

## 8. Container Registry Setup

You need a container registry to store your Docker image. Azure Container Apps pulls the image from the registry each time the job runs.

### Option 1: Azure Container Registry (ACR)

ACR is Azure's native container registry. It integrates seamlessly with Container Apps (no extra authentication configuration needed when using managed identity).

#### Create ACR

```bash
ACR_NAME="swingtraderacr"   # Must be globally unique, 5-50 chars, alphanumeric only

# Create ACR (Basic tier)
az acr create \
    --name $ACR_NAME \
    --resource-group $RESOURCE_GROUP \
    --location swedencentral \
    --sku Basic \
    --admin-enabled true
```

**ACR Tiers:**

| Tier | Storage | Price | Notes |
|------|---------|-------|-------|
| Basic | 10 GB | ~$5/month | Enough for personal projects |
| Standard | 100 GB | ~$20/month | More storage, higher throughput |
| Premium | 500 GB | ~$50/month | Geo-replication, private endpoints |

Basic is more than enough. A single SwingTrader image is ~350-400 MB. With 10 GB storage, you can keep 25+ versions.

#### Build and Push Image

```bash
# Login to ACR
az acr login --name $ACR_NAME

# Get the ACR login server address
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
# Returns: swingtraderacr.azurecr.io

# Tag your local image for ACR
docker tag swingtrader:latest ${ACR_LOGIN_SERVER}/swingtrader:latest

# Push to ACR
docker push ${ACR_LOGIN_SERVER}/swingtrader:latest

# Verify the image is in ACR
az acr repository list --name $ACR_NAME --output table
az acr repository show-tags --name $ACR_NAME --repository swingtrader --output table
```

#### Alternative: Build in ACR (No Local Docker Needed)

ACR can build images from your source code directly. Useful in CI/CD or if you do not have Docker Desktop:

```bash
# Build directly in ACR from local source
az acr build \
    --registry $ACR_NAME \
    --image swingtrader:latest \
    --file Dockerfile \
    .
```

This uploads your source code to ACR, builds the image in Azure, and stores it in the registry. No local Docker required.

#### Connect ACR to Container Apps

When creating the job, you pass the registry credentials:

```bash
# Using admin credentials (simplest for personal projects)
az containerapp job create \
    ... \
    --registry-server ${ACR_LOGIN_SERVER} \
    --registry-username $(az acr credential show --name $ACR_NAME --query username -o tsv) \
    --registry-password $(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)
```

Or, for better security, use managed identity (no passwords):

```bash
# Enable system-assigned managed identity on the Container Apps Environment
# and grant it AcrPull role on the ACR
ACR_ID=$(az acr show --name $ACR_NAME --query id -o tsv)

az containerapp job create \
    ... \
    --registry-server ${ACR_LOGIN_SERVER} \
    --registry-identity system
```

### Option 2: Docker Hub (Free)

Docker Hub is the default public registry. Free tier includes 1 private repository.

```bash
# Login to Docker Hub
docker login

# Tag and push
docker tag swingtrader:latest yourusername/swingtrader:latest
docker push yourusername/swingtrader:latest
```

When creating the Container Apps Job:

```bash
az containerapp job create \
    ... \
    --image docker.io/yourusername/swingtrader:latest \
    --registry-server docker.io \
    --registry-username yourusername \
    --registry-password "your_docker_hub_access_token"
```

**Pros:** Free for 1 private repo. No Azure-specific setup.
**Cons:** Public images are visible to everyone (unless you use the 1 free private repo). Docker Hub rate limits pulls (100/6hr for anonymous, 200/6hr for free accounts). For a daily job doing 1 pull/day, this is not an issue.

### Option 3: GitHub Container Registry (GHCR)

GHCR is free for public repositories and has generous limits for private repos.

```bash
# Login to GHCR (use a GitHub Personal Access Token with packages:write scope)
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Tag and push
docker tag swingtrader:latest ghcr.io/yourusername/swingtrader:latest
docker push ghcr.io/yourusername/swingtrader:latest
```

When creating the Container Apps Job:

```bash
az containerapp job create \
    ... \
    --image ghcr.io/yourusername/swingtrader:latest \
    --registry-server ghcr.io \
    --registry-username yourusername \
    --registry-password "$GITHUB_TOKEN"
```

**Pros:** Free for public repos. Good GitHub Actions integration (same ecosystem). No extra service to manage.
**Cons:** Need a GitHub Personal Access Token. Less integrated with Azure than ACR.

### Registry Comparison

| Registry | Cost | Best For | Integration with Azure |
|----------|------|----------|----------------------|
| **ACR Basic** | ~$5/month | Seamless Azure integration | Native (managed identity) |
| **Docker Hub** | Free (1 private) | Quick start | Manual credentials |
| **GHCR** | Free (public repos) | GitHub-centric workflow | Manual credentials |

**Recommendation:** If you want the lowest cost, use GHCR (free). If you want the smoothest Azure experience, use ACR Basic ($5/month). The $5/month difference is the only meaningful cost in the whole stack.

---

## 9. CI/CD with GitHub Actions

A GitHub Actions workflow that automatically builds and deploys the scanner when you push to main.

### Prerequisites: GitHub Secrets

In your GitHub repository, go to Settings > Secrets and variables > Actions, and add:

| Secret Name | Value | Where to Find It |
|------------|-------|-------------------|
| `AZURE_CREDENTIALS` | Service principal JSON | See below |
| `ACR_LOGIN_SERVER` | `swingtraderacr.azurecr.io` | `az acr show --name swingtraderacr --query loginServer -o tsv` |
| `ACR_USERNAME` | ACR admin username | `az acr credential show --name swingtraderacr --query username -o tsv` |
| `ACR_PASSWORD` | ACR admin password | `az acr credential show --name swingtraderacr --query "passwords[0].value" -o tsv` |

#### Create the Azure Service Principal

```bash
# Create a service principal with Contributor access to your resource group
az ad sp create-for-rbac \
    --name "swingtrader-github-actions" \
    --role contributor \
    --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/swingtrader-rg \
    --json-auth

# This outputs a JSON object like:
# {
#   "clientId": "...",
#   "clientSecret": "...",
#   "subscriptionId": "...",
#   "tenantId": "...",
#   ...
# }
# Copy the ENTIRE JSON output and save it as the AZURE_CREDENTIALS GitHub secret
```

### Complete Workflow: `.github/workflows/deploy-azure.yml`

```yaml
name: Build and Deploy to Azure Container Apps

on:
  push:
    branches: [main]
  workflow_dispatch:           # Allow manual trigger from GitHub UI

env:
  JOB_NAME: swingtrader-scanner
  RESOURCE_GROUP: swingtrader-rg

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      # 1. Check out the repository
      - name: Checkout code
        uses: actions/checkout@v4

      # 2. Login to Azure
      - name: Login to Azure
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      # 3. Login to ACR
      - name: Login to ACR
        uses: docker/login-action@v3
        with:
          registry: ${{ secrets.ACR_LOGIN_SERVER }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}

      # 4. Build and push Docker image
      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.ACR_LOGIN_SERVER }}/swingtrader:latest
            ${{ secrets.ACR_LOGIN_SERVER }}/swingtrader:${{ github.sha }}

      # 5. Update the Container Apps Job with the new image
      - name: Deploy to Container Apps Job
        run: |
          az containerapp job update \
            --name ${{ env.JOB_NAME }} \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --image ${{ secrets.ACR_LOGIN_SERVER }}/swingtrader:${{ github.sha }}

      # 6. Verify deployment
      - name: Verify deployment
        run: |
          az containerapp job show \
            --name ${{ env.JOB_NAME }} \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --query "properties.template.containers[0].image" \
            --output tsv
```

### Alternative: Using GHCR Instead of ACR

If you use GHCR instead of ACR, the workflow is simpler (no ACR secrets needed):

```yaml
name: Build and Deploy to Azure Container Apps

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  JOB_NAME: swingtrader-scanner
  RESOURCE_GROUP: swingtrader-rg
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository_owner }}/swingtrader

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Login to Azure
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy to Container Apps Job
        run: |
          az containerapp job update \
            --name ${{ env.JOB_NAME }} \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --image ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
```

### How It Works

1. You push code to the `main` branch
2. GitHub Actions triggers the workflow
3. The workflow builds a new Docker image from your Dockerfile
4. It pushes the image to the registry (ACR or GHCR), tagged with both `latest` and the git commit SHA
5. It updates the Container Apps Job to use the new image (by commit SHA for traceability)
6. The next scheduled run of the job uses the new image

The entire pipeline takes 2-4 minutes. The job does not restart — it is a scheduled job, so the new image takes effect on the next scheduled execution.

---

## 10. Adding a Dashboard Later

When you want a Streamlit web dashboard to visualize signals, you add a second container as a Container Apps **App** (not Job).

### Architecture

```
┌─────────────────────────────────────────────────────┐
│          Azure Container Apps Environment           │
│                                                     │
│  ┌──────────────────┐    ┌───────────────────────┐  │
│  │  Container Apps   │    │  Container Apps       │  │
│  │  JOB (scanner)    │    │  APP (dashboard)      │  │
│  │  - Scheduled      │    │  - Scale to zero      │  │
│  │  - Runs 5 min/day │    │  - HTTPS ingress      │  │
│  │  - Writes SQLite  │    │  - Reads SQLite       │  │
│  └────────┬─────────┘    └────────┬──────────────┘  │
│           │                       │                  │
│           └───────────┬───────────┘                  │
│                       │                              │
│              ┌────────▼────────┐                     │
│              │   Azure Files   │                     │
│              │  (shared mount) │                     │
│              │ swingtrader.db  │                     │
│              └─────────────────┘                     │
└─────────────────────────────────────────────────────┘
```

Both the scanner job and the dashboard app mount the same Azure Files share. The scanner writes to `swingtrader.db`, and the dashboard reads from it.

### Dashboard Dockerfile

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-dashboard.txt .
RUN pip install --no-cache-dir -r requirements-dashboard.txt

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser
COPY --chown=appuser:appuser src/dashboard/ ./src/dashboard/

USER appuser

# Streamlit runs on port 8501 by default
EXPOSE 8501

CMD ["streamlit", "run", "src/dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

### Create the Dashboard App

```bash
DASHBOARD_NAME="swingtrader-dashboard"
REGISTRY="swingtraderacr.azurecr.io"

# Build and push the dashboard image
docker build -t ${REGISTRY}/swingtrader-dashboard:latest -f Dockerfile.dashboard .
docker push ${REGISTRY}/swingtrader-dashboard:latest

# Create the Container App (not Job)
az containerapp create \
    --name $DASHBOARD_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT \
    --image ${REGISTRY}/swingtrader-dashboard:latest \
    --target-port 8501 \
    --ingress external \
    --min-replicas 0 \
    --max-replicas 1 \
    --cpu 0.25 \
    --memory 0.5Gi \
    --registry-server $REGISTRY \
    --registry-username $(az acr credential show --name swingtraderacr --query username -o tsv) \
    --registry-password $(az acr credential show --name swingtraderacr --query "passwords[0].value" -o tsv)
```

### Key Configuration

**`--min-replicas 0`**: Scale to zero when no one is accessing the dashboard. You pay nothing when it is not running. When someone visits the URL, Azure starts the container (cold start takes 10-30 seconds).

**`--max-replicas 1`**: Only one instance. This is a personal tool, not a high-traffic website.

**`--ingress external`**: Makes the dashboard accessible from the internet via a generated HTTPS URL like `https://swingtrader-dashboard.happysky-abc123.swedencentral.azurecontainerapps.io`.

**`--target-port 8501`**: Streamlit's default port.

### Mounting the Shared Volume

```bash
# Update the dashboard app to mount the same Azure Files share
az containerapp update \
    --name $DASHBOARD_NAME \
    --resource-group $RESOURCE_GROUP \
    --yaml dashboard-config.yaml
```

Where `dashboard-config.yaml` includes the same volume mount as the job:

```yaml
properties:
  template:
    volumes:
      - name: scanner-data-volume
        storageName: scannerdata
        storageType: AzureFile
    containers:
      - name: dashboard
        image: swingtraderacr.azurecr.io/swingtrader-dashboard:latest
        resources:
          cpu: 0.25
          memory: 0.5Gi
        volumeMounts:
          - volumeName: scanner-data-volume
            mountPath: /app/data
```

### SQLite Concurrency Note

SQLite supports multiple concurrent readers but only one writer. Since the scanner writes for ~5 minutes once per day, and the dashboard only reads, there is virtually no conflict. If the dashboard happens to read while the scanner is writing, SQLite handles this gracefully with its WAL mode — reads do not block writes and vice versa.

Enable WAL mode in your Python code:

```python
import sqlite3
conn = sqlite3.connect("/app/data/swingtrader.db")
conn.execute("PRAGMA journal_mode=WAL;")
```

### Authentication Options

The dashboard URL is public by default. To restrict access:

**Option 1: Azure AD authentication (built-in)**

```bash
# Enable Azure AD authentication on the dashboard
az containerapp auth update \
    --name $DASHBOARD_NAME \
    --resource-group $RESOURCE_GROUP \
    --unauthenticated-client-action RedirectToLoginPage \
    --set-string identityProviders.azureActiveDirectory.registration.clientId="YOUR_APP_REGISTRATION_CLIENT_ID" \
    --set-string identityProviders.azureActiveDirectory.registration.openIdIssuer="https://login.microsoftonline.com/YOUR_TENANT_ID/v2.0"
```

This redirects unauthenticated users to a Microsoft login page. Only users in your Azure AD tenant can access the dashboard.

**Option 2: Simple password in Streamlit**

Add password protection directly in your Streamlit app:

```python
import streamlit as st

def check_password():
    """Simple password gate for the dashboard."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        password = st.text_input("Password", type="password")
        if password == st.secrets["DASHBOARD_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        elif password:
            st.error("Incorrect password")
        st.stop()

check_password()
# ... rest of your dashboard code
```

This is simpler but less secure (password in environment variable, no 2FA). Fine for a personal project.

---

## 11. Monitoring and Logging

### Container Apps Job Execution Logs

Every Container Apps Environment has a Log Analytics workspace. All container stdout/stderr output is captured automatically.

#### View Logs via Azure CLI

```bash
# List recent job executions
az containerapp job execution list \
    --name swingtrader-scanner \
    --resource-group swingtrader-rg \
    --output table

# Output:
# Name                                  Status     StartTime                 Duration
# ------------------------------------  ---------  ------------------------  ----------
# swingtrader-scanner-abcd1234          Succeeded  2026-03-08T17:15:00Z      180s
# swingtrader-scanner-efgh5678          Failed     2026-03-07T17:15:00Z      45s

# View logs for a specific execution
az containerapp job logs show \
    --name swingtrader-scanner \
    --resource-group swingtrader-rg \
    --execution swingtrader-scanner-abcd1234 \
    --follow
```

#### View Logs via Log Analytics (KQL Queries)

Log Analytics lets you query logs using Kusto Query Language (KQL). Go to the Azure portal > your Container Apps Environment > Logs, or use the CLI.

**Check if today's job ran successfully:**

```kql
ContainerAppConsoleLogs_CL
| where ContainerGroupName_s startswith "swingtrader-scanner"
| where TimeGenerated > ago(24h)
| order by TimeGenerated desc
| project TimeGenerated, Log_s
```

**Find all failed executions in the last 7 days:**

```kql
ContainerAppSystemLogs_CL
| where ContainerGroupName_s startswith "swingtrader-scanner"
| where TimeGenerated > ago(7d)
| where Log_s contains "failed" or Log_s contains "error"
| order by TimeGenerated desc
```

**Show execution duration over time:**

```kql
ContainerAppSystemLogs_CL
| where ContainerGroupName_s startswith "swingtrader-scanner"
| where Log_s contains "completed"
| where TimeGenerated > ago(30d)
| project TimeGenerated, Log_s
| order by TimeGenerated asc
```

### Setting Up Alerts

Get notified when the job fails. You can set up alerts via Azure Monitor.

```bash
# Get the Log Analytics workspace ID
WORKSPACE_ID=$(az containerapp env show \
    --name swingtrader-env \
    --resource-group swingtrader-rg \
    --query "properties.appLogsConfiguration.logAnalyticsConfiguration.customerId" \
    --output tsv)

# Create an action group (where to send alerts)
az monitor action-group create \
    --name "swingtrader-alerts" \
    --resource-group swingtrader-rg \
    --short-name "st-alerts" \
    --action email admin your-email@example.com
```

You can also send alerts to Telegram by using a webhook action that calls the Telegram API. Or, simpler: add a "heartbeat" to your Python scanner that sends a Telegram message when it starts and when it finishes. If you do not receive the "finished" message by 19:00, something went wrong.

### Application Insights (Optional)

Application Insights provides deeper telemetry: request tracing, dependency tracking, custom metrics. For a batch job, this is optional — the built-in Log Analytics is usually sufficient.

If you want it:

```bash
# Create Application Insights
az monitor app-insights component create \
    --app swingtrader-insights \
    --location swedencentral \
    --resource-group swingtrader-rg \
    --application-type other

# Get the instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
    --app swingtrader-insights \
    --resource-group swingtrader-rg \
    --query instrumentationKey \
    --output tsv)

# Add as environment variable on the job
az containerapp job update \
    --name swingtrader-scanner \
    --resource-group swingtrader-rg \
    --set-env-vars APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

Then in your Python code:

```python
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging
import os

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string=f"InstrumentationKey={os.environ.get('APPINSIGHTS_INSTRUMENTATIONKEY')}"
))
logger.setLevel(logging.INFO)

logger.info("Scanner started")
# ... scanning logic ...
logger.info("Scanner completed: %d signals found", signal_count)
```

---

## 12. Cost Analysis (Detailed)

### Container Apps Job (Consumption Plan)

Billing is based on vCPU-seconds and GiB-seconds of actual execution time.

**Rates (2026, Sweden Central region):**
- vCPU: $0.000024/second (~$0.0864/hour)
- Memory: $0.000003/GiB/second (~$0.0108/GiB-hour)

**Free monthly grants (per subscription):**
- 180,000 vCPU-seconds (= 50 vCPU-hours)
- 360,000 GiB-seconds (= 100 GiB-hours)

**SwingTrader usage:**
- Job configuration: 0.5 vCPU, 1 GiB
- Runs ~22 days/month (weekdays), ~5 minutes each = 110 minutes/month = 6,600 seconds/month
- vCPU-seconds: 0.5 * 6,600 = 3,300 (free grant: 180,000) -> **$0.00**
- GiB-seconds: 1.0 * 6,600 = 6,600 (free grant: 360,000) -> **$0.00**

The scanner's usage is less than 2% of the free monthly grant. **Container Apps Job cost: $0.00/month.**

### Azure Container Registry (Basic Tier)

- Fixed price: **~$5/month**
- Includes 10 GB storage
- Can be avoided by using GHCR (free) instead

### Azure Storage Account (Azure Files)

- File storage: $0.10/GiB/month (Hot tier, LRS)
- Transaction costs: $0.015 per 10,000 transactions
- SwingTrader usage: 1 GB share, ~1,000 transactions/month
- **Cost: ~$0.10/month**

### Log Analytics

- Free tier: 5 GB ingestion per month, 31-day retention
- SwingTrader generates maybe 1-5 MB of logs per month
- **Cost: $0.00/month**

### Total Monthly Cost

| Component | With ACR | With GHCR |
|-----------|----------|-----------|
| Container Apps Job | $0.00 | $0.00 |
| Container Registry | $5.00 (ACR Basic) | $0.00 (GHCR free) |
| Storage Account (Azure Files) | $0.10 | $0.10 |
| Log Analytics | $0.00 | $0.00 |
| **Total** | **~$5.10/month** | **~$0.10/month** |

### Cost Comparison with Alternatives

| Option | Monthly Cost | Notes |
|--------|-------------|-------|
| **Azure Container Apps + GHCR** | ~$0.10 | Cheapest Azure option with Docker |
| **Azure Container Apps + ACR** | ~$5.10 | Native Azure integration |
| **Azure Functions** | ~$0.00 | No Docker, no persistent SQLite on disk |
| **Hetzner CX22** | €4.35 (~$4.80) | Full VPS, native docker-compose |
| **Hetzner CAX11 (ARM)** | €3.89 (~$4.30) | Cheapest VPS |
| **Google Cloud Run** | ~$0.00 | No persistent storage (need blob workaround) |
| **Oracle Free Tier** | $0.00 | If you can get an instance |

**Bottom line:** Azure Container Apps with GHCR is one of the cheapest options at ~$0.10/month. The only meaningful cost is if you choose ACR ($5/month). If you already have Azure credits (MSDN, student, etc.), the entire stack is effectively free.

---

## 13. Complete Step-by-Step Deployment

Every command from zero to a running scheduled scanner on Azure Container Apps. Copy-paste in order.

### Step 0: Set Variables

```bash
# Set these once — used throughout all subsequent commands
export RESOURCE_GROUP="swingtrader-rg"
export LOCATION="swedencentral"
export ENVIRONMENT="swingtrader-env"
export JOB_NAME="swingtrader-scanner"
export STORAGE_ACCOUNT="swingtraderst$(openssl rand -hex 3)"  # Append random suffix for uniqueness
export FILE_SHARE="scanner-data"
export ACR_NAME="swingtraderacr$(openssl rand -hex 3)"        # Append random suffix for uniqueness

echo "Resource Group: $RESOURCE_GROUP"
echo "Storage Account: $STORAGE_ACCOUNT"
echo "ACR Name: $ACR_NAME"
# Write these down — you will need them later
```

### Step 1: Login to Azure

```bash
az login
az account show --output table   # Verify correct subscription
```

### Step 2: Create Resource Group

```bash
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION
```

### Step 3: Create Container Apps Environment

```bash
az containerapp env create \
    --name $ENVIRONMENT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION
```

This also creates a Log Analytics workspace automatically.

### Step 4: Create Storage Account and File Share

```bash
# Create storage account
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2 \
    --min-tls-version TLS1_2

# Get storage key
STORAGE_KEY=$(az storage account keys list \
    --resource-group $RESOURCE_GROUP \
    --account-name $STORAGE_ACCOUNT \
    --query '[0].value' \
    --output tsv)

# Create file share
az storage share create \
    --name $FILE_SHARE \
    --account-name $STORAGE_ACCOUNT \
    --account-key $STORAGE_KEY \
    --quota 1

# Mount the file share in the Container Apps Environment
az containerapp env storage set \
    --name $ENVIRONMENT \
    --resource-group $RESOURCE_GROUP \
    --storage-name "scannerdata" \
    --azure-file-account-name $STORAGE_ACCOUNT \
    --azure-file-account-key $STORAGE_KEY \
    --azure-file-share-name $FILE_SHARE \
    --access-mode ReadWrite
```

### Step 5: Build Docker Image Locally and Test

```bash
cd /path/to/SwingTrader

# Build the image
docker build -t swingtrader:latest .

# Test locally with your .env file
docker run --rm \
    --env-file .env \
    -v "$(pwd)/data:/app/data" \
    swingtrader:latest

# Verify it ran successfully and check the SQLite database
ls -la data/swingtrader.db
```

### Step 6: Create Container Registry

**Option A: ACR ($5/month, best Azure integration)**

```bash
az acr create \
    --name $ACR_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Basic \
    --admin-enabled true

ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
```

**Option B: GHCR (free)**

No Azure CLI commands needed. You push from your local machine or GitHub Actions.

```bash
# Just set the variable for later use
ACR_LOGIN_SERVER="ghcr.io/yourgithubusername"
```

### Step 7: Push Image to Registry

**If using ACR:**

```bash
az acr login --name $ACR_NAME

docker tag swingtrader:latest ${ACR_LOGIN_SERVER}/swingtrader:latest
docker push ${ACR_LOGIN_SERVER}/swingtrader:latest
```

**If using GHCR:**

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

docker tag swingtrader:latest ghcr.io/yourgithubusername/swingtrader:latest
docker push ghcr.io/yourgithubusername/swingtrader:latest
```

### Step 8: Create Container Apps Job

**If using ACR:**

```bash
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

az containerapp job create \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT \
    --trigger-type "Schedule" \
    --cron-expression "15 17 * * 1-5" \
    --replica-timeout 600 \
    --replica-retry-limit 1 \
    --replica-completion-count 1 \
    --parallelism 1 \
    --image "${ACR_LOGIN_SERVER}/swingtrader:latest" \
    --cpu 0.5 \
    --memory 1Gi \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD
```

**If using GHCR:**

```bash
az containerapp job create \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT \
    --trigger-type "Schedule" \
    --cron-expression "15 17 * * 1-5" \
    --replica-timeout 600 \
    --replica-retry-limit 1 \
    --replica-completion-count 1 \
    --parallelism 1 \
    --image "ghcr.io/yourgithubusername/swingtrader:latest" \
    --cpu 0.5 \
    --memory 1Gi \
    --registry-server ghcr.io \
    --registry-username yourgithubusername \
    --registry-password $GITHUB_TOKEN
```

### Step 9: Set Secrets and Environment Variables

```bash
# Set secrets
az containerapp job secret set \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --secrets \
        telegram-bot-token="YOUR_ACTUAL_TOKEN" \
        telegram-chat-id="YOUR_ACTUAL_CHAT_ID"

# Set environment variables (map secrets + set plain vars)
az containerapp job update \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --set-env-vars \
        TELEGRAM_BOT_TOKEN=secretref:telegram-bot-token \
        TELEGRAM_CHAT_ID=secretref:telegram-chat-id \
        DATABASE_PATH=/app/data/swingtrader.db
```

### Step 9b: Add Volume Mount

Create a YAML file for the volume configuration:

```bash
cat > /tmp/job-volume-config.yaml << 'EOF'
properties:
  template:
    volumes:
      - name: scanner-data-volume
        storageName: scannerdata
        storageType: AzureFile
    containers:
      - name: scanner
        image: PLACEHOLDER_IMAGE
        resources:
          cpu: 0.5
          memory: 1Gi
        volumeMounts:
          - volumeName: scanner-data-volume
            mountPath: /app/data
        env:
          - name: TELEGRAM_BOT_TOKEN
            secretRef: telegram-bot-token
          - name: TELEGRAM_CHAT_ID
            secretRef: telegram-chat-id
          - name: DATABASE_PATH
            value: /app/data/swingtrader.db
EOF
```

Replace `PLACEHOLDER_IMAGE` with your actual image path, then apply:

```bash
# Replace the placeholder with your actual image
sed -i '' "s|PLACEHOLDER_IMAGE|${ACR_LOGIN_SERVER}/swingtrader:latest|" /tmp/job-volume-config.yaml

az containerapp job update \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --yaml /tmp/job-volume-config.yaml
```

### Step 10: Trigger a Manual Test Run

```bash
# Start the job manually
az containerapp job start \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP

# Wait a moment, then check the execution status
az containerapp job execution list \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --output table
```

### Step 11: Verify Logs

```bash
# Get the name of the latest execution
EXECUTION_NAME=$(az containerapp job execution list \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[0].name" \
    --output tsv)

# View the logs
az containerapp job logs show \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --execution $EXECUTION_NAME

# Or check via Log Analytics (may take a few minutes for logs to appear)
WORKSPACE_ID=$(az containerapp env show \
    --name $ENVIRONMENT \
    --resource-group $RESOURCE_GROUP \
    --query "properties.appLogsConfiguration.logAnalyticsConfiguration.customerId" \
    --output tsv)

az monitor log-analytics query \
    --workspace $WORKSPACE_ID \
    --analytics-query "ContainerAppConsoleLogs_CL | where ContainerGroupName_s startswith 'swingtrader-scanner' | where TimeGenerated > ago(1h) | order by TimeGenerated desc | take 50" \
    --output table
```

### Step 12: Set Up GitHub Actions for Auto-Deploy

```bash
# Create the service principal for GitHub Actions
SUBSCRIPTION_ID=$(az account show --query id --output tsv)

az ad sp create-for-rbac \
    --name "swingtrader-github-actions" \
    --role contributor \
    --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
    --json-auth

# Copy the JSON output
# In GitHub: Settings > Secrets > Actions > New repository secret
# Name: AZURE_CREDENTIALS, Value: the entire JSON

# Also add these secrets:
# ACR_LOGIN_SERVER: the value of $ACR_LOGIN_SERVER
# ACR_USERNAME: the value of $ACR_USERNAME
# ACR_PASSWORD: the value of $ACR_PASSWORD

# Create the workflow file (see Section 9 for the complete YAML)
mkdir -p .github/workflows
# Copy the deploy-azure.yml from Section 9
```

After pushing the workflow file to your `main` branch, every subsequent push to `main` will automatically build, push, and deploy the new image.

### Verification Checklist

After completing all steps, verify:

```bash
# 1. Job exists and has correct schedule
az containerapp job show \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "{schedule: properties.configuration.scheduleTriggerConfig.cronExpression, image: properties.template.containers[0].image, status: properties.provisioningState}" \
    --output table

# 2. Secrets are configured
az containerapp job secret list \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --output table

# 3. Storage is mounted
az containerapp env storage list \
    --name $ENVIRONMENT \
    --resource-group $RESOURCE_GROUP \
    --output table

# 4. Last execution succeeded
az containerapp job execution list \
    --name $JOB_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[0].{name:name, status:properties.status, startTime:properties.startTime}" \
    --output table
```

---

## 14. Troubleshooting

### Job Runs but No Telegram Message

**Symptom:** Execution shows "Succeeded" but you did not receive a Telegram notification.

**Check:**
1. Verify secrets are set correctly:
   ```bash
   az containerapp job secret list \
       --name swingtrader-scanner \
       --resource-group swingtrader-rg \
       --output table
   ```
   You cannot see the values, only the names. If the names are correct, the values might be wrong.

2. Check the logs for Telegram-related errors:
   ```bash
   az containerapp job logs show \
       --name swingtrader-scanner \
       --resource-group swingtrader-rg \
       --execution EXECUTION_NAME | grep -i telegram
   ```

3. Test the Telegram token manually:
   ```bash
   curl "https://api.telegram.org/botYOUR_TOKEN/getMe"
   ```

4. Common issues:
   - Secret value has leading/trailing whitespace (trim it)
   - Bot was not added to the chat (send `/start` to the bot)
   - Chat ID is for a group but the bot is not in the group
   - Environment variable name mismatch (check uppercase/lowercase)

### Image Pull Failures

**Symptom:** Execution shows "Failed" with an image pull error.

**Check:**
```bash
# View system logs for pull errors
az containerapp job logs show \
    --name swingtrader-scanner \
    --resource-group swingtrader-rg \
    --execution EXECUTION_NAME \
    --type system
```

**Common causes:**
- ACR credentials expired. Regenerate:
  ```bash
  az acr credential renew --name swingtraderacr --password-id password
  ```
  Then update the job's registry password.

- Image tag does not exist. Verify:
  ```bash
  az acr repository show-tags --name swingtraderacr --repository swingtrader
  ```

- GHCR token expired. Generate a new Personal Access Token with `packages:read` scope.

### SQLite Locked Errors

**Symptom:** `database is locked` error in logs.

This should not happen with a single job running at a time (`parallelism: 1`). If it does:

1. Check that only one execution is running:
   ```bash
   az containerapp job execution list \
       --name swingtrader-scanner \
       --resource-group swingtrader-rg \
       --query "[?properties.status=='Running']"
   ```

2. If a previous execution timed out and left a lock file, the lock is released when the container exits. But Azure Files may retain a stale lock if the container was killed abruptly. Wait for the stale lock to expire (usually 30-60 seconds) or delete the SQLite journal/WAL files from the file share.

3. Enable WAL mode in your code to reduce lock contention:
   ```python
   conn = sqlite3.connect(db_path)
   conn.execute("PRAGMA journal_mode=WAL;")
   ```

### Timezone / DST Issues with CRON

**Symptom:** Job runs at the wrong time after a DST switch.

Container Apps CRON is always UTC. If you used `15 16 * * 1-5` thinking it was 18:15 CET, it is actually 17:15 CET in winter (UTC+1) and 18:15 CEST in summer (UTC+2).

**Fix:** Use `15 17 * * 1-5` (17:15 UTC) which gives:
- Summer (CEST/UTC+2): 19:15 Stockholm time
- Winter (CET/UTC+1): 18:15 Stockholm time

Both are after market close (17:30). The summer time is later than strictly necessary, but the data does not change after close, so it does not matter.

### Job Timeout

**Symptom:** Execution shows "Failed" with a timeout.

**Check:** The default `replica-timeout` is 600 seconds (10 minutes). If your scanner takes longer:

```bash
# Increase timeout to 1800 seconds (30 minutes)
az containerapp job update \
    --name swingtrader-scanner \
    --resource-group swingtrader-rg \
    --replica-timeout 1800
```

**Why it might be slow:**
- Scanning more stocks (200+ with yfinance takes longer due to rate limiting)
- Network issues (yfinance calls are slow from the Azure datacenter)
- Azure Files is slow (unlikely for this workload, but check if SQLite operations are the bottleneck)

### Container Exits with Non-Zero Code

**Symptom:** Execution shows "Failed" but no obvious error in stdout logs.

**Check:**
1. Look at system logs, not just console logs:
   ```bash
   az containerapp job logs show \
       --name swingtrader-scanner \
       --resource-group swingtrader-rg \
       --execution EXECUTION_NAME \
       --type system
   ```

2. Common causes:
   - Out of memory (increase `--memory` from 1Gi to 2Gi)
   - Python unhandled exception (add try/except with logging in your main function)
   - Missing environment variable (your code crashes before printing anything)

3. Add a catch-all exception handler:
   ```python
   import sys
   import traceback

   def main():
       try:
           run_scanner()
       except Exception as e:
           print(f"FATAL ERROR: {e}", file=sys.stderr)
           traceback.print_exc()
           sys.exit(1)
   ```

### Cleaning Up (If You Want to Start Over)

```bash
# Delete everything in the resource group
az group delete --name swingtrader-rg --yes --no-wait

# This deletes: Container Apps Environment, Job, Storage Account, ACR,
# Log Analytics workspace — everything in the resource group.
# The --no-wait flag returns immediately while deletion happens in the background.
```

---

## Summary

Azure Container Apps Jobs is a strong choice for the SwingTrader scanner. The key advantages:

1. **True pay-per-use:** A 5-minute daily job costs effectively $0/month on the consumption plan (well within free grants).
2. **Docker-native:** Your local Dockerfile works unchanged in production.
3. **Built-in scheduling:** CRON trigger, retry policies, execution history — no external scheduler needed.
4. **Persistent storage:** Azure Files volume mounts work like local Docker volumes.
5. **Easy extension:** Adding a Streamlit dashboard later is one more `az containerapp create` command with the same environment and storage.
6. **Total cost:** ~$0.10/month with GHCR, ~$5.10/month with ACR.

The main trade-off versus a VPS (Hetzner at $4.35/month) is complexity. Container Apps requires Azure CLI knowledge, understanding of environments/jobs/registries, and more configuration steps. A VPS is simpler: SSH in, `docker compose up`. But Container Apps requires zero server maintenance — no OS updates, no security patches, no SSH keys to manage, no server that can go down.

For a developer who is comfortable with Azure or wants to learn it, Container Apps is the more modern, lower-maintenance choice. For someone who just wants to get something running with minimal fuss, a VPS with docker-compose is simpler.
