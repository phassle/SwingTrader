# 07 - Azure Hosting for SwingTrader

> Research date: 2026-03-08
> Goal: Evaluate Azure-specific hosting options for the SwingTrader daily scanner, with practical setup guides and code examples.

---

## Table of Contents

1. [Azure Options Overview](#1-azure-options-overview)
2. [Storage Options on Azure](#2-storage-options-on-azure)
3. [Recommended Architecture](#3-recommended-architecture)
4. [Complete Azure Functions Setup Guide](#4-complete-azure-functions-setup-guide)
5. [Docker + Azure Container Apps Alternative](#5-docker--azure-container-apps-alternative)
6. [Local Development Without Docker](#6-local-development-without-docker)
7. [CI/CD with GitHub Actions](#7-cicd-with-github-actions)
8. [Cost Breakdown](#8-cost-breakdown)
9. [Comparison: Azure vs Hetzner vs Local](#9-comparison-azure-vs-hetzner-vs-local)

---

## 1. Azure Options Overview

The SwingTrader workload is simple: a Python job that runs once daily after Stockholm market close (~18:00 CET), takes 1-5 minutes, fetches data, calculates indicators, and sends a Telegram notification. Here is how each Azure service handles this.

### Azure Functions (Timer Trigger) — RECOMMENDED

Azure Functions is a serverless compute platform. You write a function, attach a timer trigger with a CRON expression, and Azure runs it on schedule. No VM, no container, no infrastructure to manage.

**How it works:**

1. You write a Python function in `function_app.py`
2. Define a timer trigger with CRON: `0 15 16 * * 1-5` (16:15 UTC = 18:15 CET, Mon-Fri)
3. Azure spins up a worker, runs your function, shuts it down
4. You pay only for execution time (Consumption plan)

**Key details:**

- **Python support:** Python 3.9-3.11 (V2 programming model). Full pip support via `requirements.txt`.
- **Consumption plan:** Pay per execution. 1 million free executions/month + 400,000 GB-seconds free. A single 3-minute daily execution uses ~30 executions/month and ~90 GB-seconds. This is **well within the free tier** — effectively $0/month.
- **Timeout:** 10 minutes on Consumption plan (plenty for a 1-5 minute scan).
- **Cold start:** Python functions take 5-15 seconds to cold start (loading the runtime + dependencies). This is perfectly acceptable for a daily batch job — you do not care if it starts at 18:15:00 or 18:15:12.
- **Package size:** The deployment package (your code + dependencies) can be up to 1 GB on Linux Consumption plan. yfinance + pandas + pandas-ta is roughly 150-200 MB — well within limits.
- **Storage:** The filesystem is ephemeral. You cannot keep a SQLite file on disk between runs. Use Azure Blob Storage to persist data (see Section 2).
- **Deployment options:** VS Code Azure Functions extension, Azure CLI (`func azure functionapp publish`), or GitHub Actions.
- **Monitoring:** Built-in Application Insights for logs, metrics, and alerts.

**Example `function_app.py`:**

```python
import azure.functions as func
import logging

app = func.FunctionApp()

@app.timer_trigger(
    schedule="0 15 16 * * 1-5",  # 16:15 UTC = 18:15 CET, Mon-Fri
    arg_name="myTimer",
    run_on_startup=False,
)
def daily_scan(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.warning("Timer is past due — running anyway")

    logging.info("Starting SwingTrader daily scan")
    # Your scanner logic here
    logging.info("Scan complete")
```

**Why recommended:** Zero infrastructure, zero cost for this workload, built-in scheduling, built-in monitoring. The only trade-off is no native SQLite support (solved with Blob Storage).

### Azure Container Apps

Azure Container Apps runs Docker containers with built-in support for scheduled jobs (cron). Think of it as "Azure's managed Kubernetes, but simple."

**How it works:**

1. Build a Docker image with your scanner
2. Push it to Azure Container Registry (or Docker Hub)
3. Create a Container Apps Job with a CRON schedule
4. Azure pulls the image and runs the container on schedule

**Key details:**

- **Cron jobs:** First-class support. Define schedule in the job configuration.
- **Consumption plan:** Pay per execution. vCPU-seconds and GiB-seconds pricing. A 3-minute job with 0.5 vCPU and 1 GiB RAM costs roughly $0.001 per run — about $0.02/month for daily weekday runs.
- **Persistent storage:** Azure Files volumes can be mounted, so **SQLite works natively** inside the container.
- **Timeout:** Configurable, up to 30 minutes.
- **Advantages over Functions:** SQLite works with mounted volumes. Full Docker flexibility. No cold start overhead (the container image has everything pre-loaded, though pull time still applies).
- **Container Registry:** Azure Container Registry Basic tier is ~$5/month. Alternatively, use Docker Hub free tier or GitHub Container Registry (free for public repos).

**Pricing estimate for daily weekday jobs:**

- Container Apps execution: ~$0.02/month
- Azure Container Registry (Basic): ~$5/month (or free with Docker Hub/GHCR)
- Azure Files (1 GB): ~$0.06/month
- **Total: ~$0-5/month** depending on registry choice

### Azure Container Instances (ACI)

ACI runs a single Docker container on demand. It is simpler than Container Apps but has no built-in scheduling.

**How it works:**

1. Build and push a Docker image
2. Create an ACI container group
3. Trigger it on a schedule using Azure Logic Apps or Azure Automation

**Key details:**

- **No built-in CRON.** You need an external scheduler (Logic Apps, Automation Account, or an Azure Function that starts the container).
- **Pricing:** Per-second billing. ~$0.0000125 per vCPU-second + ~$0.0000015 per GiB-second. A 3-minute job costs ~$0.003.
- **Volume mounts:** Azure Files can be mounted for persistent storage.
- **Simplicity:** Very straightforward — it is literally "run this container." But the lack of built-in scheduling makes it less convenient than Container Apps for this use case.

**When to choose ACI:** If you already have a Logic App or Automation Account and want the simplest possible container execution. Otherwise, Container Apps Jobs is a better fit since it has native CRON support.

### Azure App Service

App Service is designed for web applications. It can run scheduled tasks via the WebJobs feature, but it is not the natural fit for a cron job.

**How it works:**

1. Deploy your Python code to App Service
2. Create a Triggered WebJob with a CRON schedule
3. The WebJob runs your scanner script on schedule

**Key details:**

- **Pricing:** The Free and Shared tiers do not support WebJobs with schedules. The B1 (Basic) tier costs ~$13/month. This is expensive for a job that runs 3 minutes per day.
- **Always-on:** B1 includes an always-running instance. This is wasteful for a daily job but becomes useful if you later add a web dashboard (Streamlit, FastAPI) on the same plan.
- **SQLite:** Works fine — App Service has a persistent filesystem.
- **Deployment:** Git push, VS Code, Azure CLI, or GitHub Actions.

**When to choose App Service:** Only if you plan to run a web dashboard alongside the scanner. Then the ~$13/month gets you both the scheduled job and a web UI. For a scanner-only deployment, it is overkill and overpriced.

### Azure Virtual Machine

A VM on Azure is the closest equivalent to a Hetzner VPS. Full control, full responsibility.

**How it works:**

1. Create a Linux VM (Ubuntu 24.04)
2. SSH in, install Python, set up cron
3. Deploy your code, configure `.env`, done

**Key details:**

- **B1s VM:** 1 vCPU, 1 GiB RAM. ~$7.59/month (pay-as-you-go) or ~$3.80/month with 1-year reserved pricing.
- **B1ls VM:** 1 vCPU, 0.5 GiB RAM. ~$3.80/month (pay-as-you-go) or ~$2.28/month reserved. Enough for this workload.
- **Disk:** 30 GB OS disk included (Standard SSD).
- **SQLite:** Works perfectly. Persistent filesystem, just like any Linux box.
- **Maintenance:** You manage OS updates, security patches, firewall rules (NSG).
- **IP address:** Static public IP is ~$3.65/month extra. Or use a dynamic IP (free) since you do not need inbound connections for a cron job.

**Comparison to Hetzner:** Azure VMs are roughly 2x the price of Hetzner for equivalent specs. A Hetzner CX11 (2 GB, 1 vCPU) is ~$3.30/month. The Azure B1s (1 GiB, 1 vCPU) is ~$3.80/month reserved but with less RAM. If you want a VPS, Hetzner is the better deal. The Azure VM only makes sense if you want everything in one Azure subscription for organizational reasons.

---

## 2. Storage Options on Azure

### SQLite on Azure

SQLite is a file-based database. It requires a persistent, writable filesystem. Here is where it works and where it does not:

| Azure Service | SQLite Works? | Notes |
|---------------|--------------|-------|
| Azure VM | Yes | Regular filesystem, no issues |
| App Service | Yes | Persistent `/home` directory |
| Container Apps | Yes | With Azure Files volume mount |
| Container Instances | Yes | With Azure Files volume mount |
| Azure Functions | **No** (workaround exists) | Ephemeral filesystem; file is lost between runs |

**The Azure Functions workaround:**

```python
import os
import tempfile
from azure.storage.blob import BlobServiceClient

CONN_STR = os.environ["AzureWebJobsStorage"]
CONTAINER_NAME = "scanner-data"
BLOB_NAME = "swingtrader.db"

def download_db() -> str:
    """Download SQLite DB from Blob Storage to a temp file."""
    blob_service = BlobServiceClient.from_connection_string(CONN_STR)
    blob_client = blob_service.get_blob_client(CONTAINER_NAME, BLOB_NAME)

    local_path = os.path.join(tempfile.gettempdir(), "swingtrader.db")

    try:
        with open(local_path, "wb") as f:
            data = blob_client.download_blob()
            data.readinto(f)
    except Exception:
        # First run — no DB exists yet, that is fine
        pass

    return local_path


def upload_db(local_path: str) -> None:
    """Upload SQLite DB back to Blob Storage."""
    blob_service = BlobServiceClient.from_connection_string(CONN_STR)
    blob_client = blob_service.get_blob_client(CONTAINER_NAME, BLOB_NAME)

    with open(local_path, "rb") as f:
        blob_client.upload_blob(f, overwrite=True)
```

This pattern works well for a single-user daily job. The DB is small (< 10 MB), so download/upload takes < 1 second. The trade-off is that you must remember to upload after every write operation, and concurrent access is not safe (not a concern for a single daily job).

### Azure Blob Storage

Azure Blob Storage is the cheapest object storage on Azure. Use it to store the SQLite file (as described above) or any other data files.

**Pricing (LRS — locally redundant):**

- Storage: $0.018/GB/month (hot tier)
- Read operations: $0.004 per 10,000
- Write operations: $0.05 per 10,000

For a 10 MB SQLite file with 1 read + 1 write per day, the monthly cost is essentially $0.00.

**Setup:**

```bash
# Create storage account
az storage account create \
    --name swingtraderdata \
    --resource-group swingtrader-rg \
    --location northeurope \
    --sku Standard_LRS

# Create container
az storage container create \
    --name scanner-data \
    --account-name swingtraderdata
```

### Azure SQL Database

Azure SQL Database is a fully managed relational database. The serverless tier can auto-pause when not in use.

**Key details:**

- **Serverless tier (General Purpose):** Starts at ~$0.514/vCore-hour when active, auto-pauses after 1 hour of inactivity. For a 3-minute daily job, you would pay for approximately 1 hour of compute per day (minimum billing granularity).
- **Estimated cost:** ~$5-15/month depending on actual usage patterns.
- **Storage:** 5 GB included, ~$0.115/GB/month after that.
- **Code changes:** You would need to replace `sqlite3` with `pyodbc` or `sqlalchemy` with a SQL Server driver. The SQL syntax is mostly compatible but there are dialect differences.

**When to choose Azure SQL:** If you want zero storage management, automatic backups, and a database that is always accessible from any Azure service. For a personal scanner tool, this is overkill — the SQLite-on-Blob-Storage pattern is simpler and cheaper.

### Azure Table Storage / Cosmos DB

**Table Storage** is a NoSQL key-value store. Extremely cheap (~$0.045/GB/month) but requires a different data model — no SQL queries, no joins, partition-key-based access patterns.

**Cosmos DB** is Azure's premium NoSQL database. The serverless tier charges per request unit (RU). For a low-volume scanner, costs would be minimal (~$1-3/month), but the learning curve and code changes are not justified for this use case.

**When to choose:** Only if you are already using Cosmos DB for other projects. For a new project, stick with SQLite.

### Recommendation for This Project

**Azure Functions + Blob Storage for SQLite.** This gives you:

- Zero-cost compute (free tier)
- Near-zero storage cost ($0.00/month for < 1 GB)
- Minimal code changes (add download/upload wrapper around existing SQLite logic)
- No server to manage

If you later add a web dashboard, consider migrating to Azure SQL Database or moving to Container Apps with a mounted Azure Files volume.

---

## 3. Recommended Architecture

```
┌─────────────────────────────────────────────────────┐
│                Azure Functions (Consumption)         │
│                                                     │
│  Timer Trigger (CRON: 0 15 16 * * 1-5)             │
│                                                     │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Download   │  │ Fetch data │  │ Calculate    │  │
│  │ SQLite DB  │→ │ (yfinance) │→ │ indicators   │  │
│  │ from Blob  │  │            │  │ (pandas-ta)  │  │
│  └────────────┘  └────────────┘  └──────────────┘  │
│                                        │            │
│  ┌────────────┐  ┌────────────┐  ┌─────▼────────┐  │
│  │ Upload     │← │ Send       │← │ Generate     │  │
│  │ SQLite DB  │  │ Telegram   │  │ signals      │  │
│  │ to Blob    │  │ message    │  │              │  │
│  └────────────┘  └────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌──────────────┐    ┌──────────────────┐
│ Azure Blob   │    │ Telegram Bot API  │
│ Storage      │    │ (external)        │
│ (SQLite DB)  │    │                   │
└──────────────┘    └──────────────────┘
```

**Total estimated cost: $0-2/month**

| Component | Monthly Cost |
|-----------|-------------|
| Azure Functions (Consumption) | $0 (free tier: 1M executions, 400K GB-sec) |
| Azure Blob Storage (< 1 GB) | ~$0.02 |
| Telegram Bot API | Free |
| **Total** | **~$0.02** |

---

## 4. Complete Azure Functions Setup Guide

### Prerequisites

```bash
# Install Azure Functions Core Tools (macOS)
brew tap azure/functions
brew install azure-functions-core-tools@4

# Install Azure CLI
brew install azure-cli

# Login to Azure
az login
```

### Step 1: Create the Function App Project

```bash
# Create project directory
mkdir -p ~/source/SwingTrader/azure-function
cd ~/source/SwingTrader/azure-function

# Initialize Azure Functions project with Python
func init --python --model V2

# This creates:
# ├── function_app.py     # Your function code
# ├── host.json           # Function host configuration
# ├── local.settings.json # Local development settings
# └── requirements.txt    # Python dependencies
```

### Step 2: Configure Requirements

```bash
# requirements.txt
cat > requirements.txt << 'EOF'
azure-functions
azure-storage-blob
yfinance>=0.2.36
pandas>=2.2.0
pandas-ta>=0.3.14b1
requests>=2.31.0
python-dotenv>=1.0.0
EOF
```

### Step 3: Write the Function

```python
# function_app.py
"""
SwingTrader Azure Function — Daily Scanner

Runs Mon-Fri at 18:15 CET (16:15 UTC) after Stockholm market close.
Downloads SQLite DB from Blob Storage, runs scan, uploads DB, sends Telegram.
"""

import os
import logging
import tempfile
from datetime import datetime

import azure.functions as func
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()

# --- Configuration ---
TICKERS = [
    "ABB.ST", "ALFA.ST", "ASSA-B.ST", "ATCO-B.ST", "AZN.ST",
    "BOL.ST", "ELUX-B.ST", "ERIC-B.ST", "ESSITY-B.ST", "EVO.ST",
    "HEXA-B.ST", "HM-B.ST", "INVE-B.ST", "KINV-B.ST", "NIBE-B.ST",
    "SAND.ST", "SCA-B.ST", "SEB-A.ST", "SHB-A.ST", "SKF-B.ST",
    "SSAB-A.ST", "SWED-A.ST", "SWMA.ST", "TEL2-B.ST", "TELIA.ST",
    "VOLV-B.ST",
]

RSI_OVERSOLD = 35
BB_LENGTH = 20
BB_STD = 2.0
LOOKBACK = "8mo"


def get_blob_client(blob_name: str):
    """Get a blob client for the scanner-data container."""
    conn_str = os.environ["AzureWebJobsStorage"]
    service = BlobServiceClient.from_connection_string(conn_str)
    return service.get_blob_client("scanner-data", blob_name)


def download_db() -> str:
    """Download SQLite DB from Blob Storage. Returns local file path."""
    local_path = os.path.join(tempfile.gettempdir(), "swingtrader.db")
    blob_client = get_blob_client("swingtrader.db")

    try:
        with open(local_path, "wb") as f:
            data = blob_client.download_blob()
            data.readinto(f)
        logging.info("Downloaded existing database from Blob Storage")
    except Exception:
        logging.info("No existing database found — starting fresh")

    return local_path


def upload_db(local_path: str) -> None:
    """Upload SQLite DB back to Blob Storage."""
    blob_client = get_blob_client("swingtrader.db")
    with open(local_path, "rb") as f:
        blob_client.upload_blob(f, overwrite=True)
    logging.info("Uploaded database to Blob Storage")


def scan_stock(ticker: str) -> dict | None:
    """Scan a single stock for mean reversion buy signals."""
    try:
        df = yf.download(ticker, period=LOOKBACK, progress=False)

        if df.empty or len(df) < BB_LENGTH + 50:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.ta.rsi(length=14, append=True)
        df.ta.bbands(length=BB_LENGTH, std=BB_STD, append=True)
        df.ta.macd(append=True)

        latest = df.iloc[-1]
        rsi_val = latest.get("RSI_14")
        close = latest.get("Close")
        bb_lower = latest.get(f"BBL_{BB_LENGTH}_{BB_STD}")

        if pd.isna(rsi_val) or pd.isna(bb_lower):
            return None

        is_buy = rsi_val < RSI_OVERSOLD and close < bb_lower

        return {
            "ticker": ticker,
            "close": round(float(close), 2),
            "rsi": round(float(rsi_val), 1),
            "bb_lower": round(float(bb_lower), 2),
            "is_buy": is_buy,
            "date": df.index[-1].strftime("%Y-%m-%d"),
        }
    except Exception as e:
        logging.error("Failed to scan %s: %s", ticker, e)
        return None


def send_telegram(message: str) -> bool:
    """Send a message via Telegram Bot API."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logging.warning("Telegram credentials not configured")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except requests.RequestException as e:
        logging.error("Telegram send failed: %s", e)
        return False


@app.timer_trigger(
    schedule="0 15 16 * * 1-5",  # 16:15 UTC = 18:15 CET Mon-Fri
    arg_name="myTimer",
    run_on_startup=False,
)
def daily_scan(myTimer: func.TimerRequest) -> None:
    """Main entry point: scan all tickers and send results via Telegram."""
    if myTimer.past_due:
        logging.warning("Timer trigger is past due")

    logging.info("Starting SwingTrader daily scan for %d tickers", len(TICKERS))

    try:
        # Download database (for storing results)
        db_path = download_db()

        # Scan all stocks
        results = []
        for ticker in TICKERS:
            result = scan_stock(ticker)
            if result:
                results.append(result)

        buy_signals = [r for r in results if r["is_buy"]]

        # Store results in SQLite
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                close REAL,
                rsi REAL,
                bb_lower REAL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        for s in buy_signals:
            conn.execute(
                "INSERT INTO signals (ticker, date, close, rsi, bb_lower) VALUES (?, ?, ?, ?, ?)",
                (s["ticker"], s["date"], s["close"], s["rsi"], s["bb_lower"]),
            )
        conn.commit()
        conn.close()

        # Upload database back to Blob Storage
        upload_db(db_path)

        # Send Telegram notification
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if buy_signals:
            lines = [f"*SwingTrader Signals - {today}*\n"]
            for i, s in enumerate(buy_signals, 1):
                lines.append(
                    f"{i}. *{s['ticker']}*\n"
                    f"   Close: {s['close']} | RSI: {s['rsi']} | BB Lower: {s['bb_lower']}\n"
                )
            lines.append(f"_{len(buy_signals)} signal(s) total_")
            msg = "\n".join(lines)
        else:
            msg = f"SwingTrader {today}: No buy signals today. Scanned {len(results)} stocks."

        send_telegram(msg)
        logging.info("Scan complete: %d signals from %d stocks", len(buy_signals), len(results))

    except Exception as e:
        logging.critical("Scan failed: %s", e, exc_info=True)
        send_telegram(f"SwingTrader ERROR: {e}")
        raise
```

### Step 4: Configure Local Settings

```json
// local.settings.json (not committed to git)
{
    "IsEncrypted": false,
    "Values": {
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "AzureWebJobsStorage": "UseDevelopmentStorage=true",
        "TELEGRAM_BOT_TOKEN": "your-bot-token-here",
        "TELEGRAM_CHAT_ID": "your-chat-id-here"
    }
}
```

### Step 5: Test Locally

```bash
# Start the Azurite storage emulator (for local Blob Storage)
# Install: npm install -g azurite
azurite --silent &

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start the function locally
func start

# The function will not trigger immediately (it is on a timer).
# To test manually, set run_on_startup=True temporarily, or use:
curl -X POST http://localhost:7071/admin/functions/daily_scan \
    -H "Content-Type: application/json" \
    -d '{}'
```

### Step 6: Create Azure Resources

```bash
# Set variables
RESOURCE_GROUP="swingtrader-rg"
LOCATION="northeurope"  # Closest to Stockholm
STORAGE_ACCOUNT="swingtraderstore"  # Must be globally unique
FUNCTION_APP="swingtrader-scanner"  # Must be globally unique

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account (used by Functions runtime AND for your SQLite blob)
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS

# Create the blob container for scanner data
az storage container create \
    --name scanner-data \
    --account-name $STORAGE_ACCOUNT

# Create the Function App
az functionapp create \
    --name $FUNCTION_APP \
    --resource-group $RESOURCE_GROUP \
    --storage-account $STORAGE_ACCOUNT \
    --consumption-plan-location $LOCATION \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4 \
    --os-type Linux
```

### Step 7: Configure Application Settings

```bash
# Set Telegram credentials as app settings (encrypted at rest)
az functionapp config appsettings set \
    --name $FUNCTION_APP \
    --resource-group $RESOURCE_GROUP \
    --settings \
        TELEGRAM_BOT_TOKEN="your-real-bot-token" \
        TELEGRAM_CHAT_ID="your-real-chat-id"
```

### Step 8: Deploy

```bash
# Deploy from the azure-function directory
cd ~/source/SwingTrader/azure-function
func azure functionapp publish $FUNCTION_APP
```

Deployment takes 1-2 minutes. The output will show the function URL and trigger info.

### Step 9: Verify and Monitor

```bash
# Check function status
az functionapp show \
    --name $FUNCTION_APP \
    --resource-group $RESOURCE_GROUP \
    --query "state" -o tsv

# View recent function executions (requires Application Insights)
az monitor app-insights query \
    --app $FUNCTION_APP \
    --resource-group $RESOURCE_GROUP \
    --analytics-query "traces | order by timestamp desc | take 20"

# Stream live logs
func azure functionapp logstream $FUNCTION_APP

# Trigger the function manually for testing
az functionapp function invoke \
    --name $FUNCTION_APP \
    --resource-group $RESOURCE_GROUP \
    --function-name daily_scan
```

### CRON Expression Deep Dive

Azure Functions uses NCrontab (6-field CRON) with **UTC time**.

```
┌────────── second (0-59)
│ ┌──────── minute (0-59)
│ │ ┌────── hour (0-23)
│ │ │ ┌──── day of month (1-31)
│ │ │ │ ┌── month (1-12)
│ │ │ │ │ ┌ day of week (0-6, 0=Sunday)
│ │ │ │ │ │
0 15 16 * * 1-5    → 16:15:00 UTC, Mon-Fri
```

**Timezone note:** Azure Functions Consumption plan runs in UTC. Stockholm is UTC+1 (CET) or UTC+2 (CEST during summer). To run at 18:15 CET:

- **Winter (CET, UTC+1):** 17:15 UTC → `0 15 17 * * 1-5`
- **Summer (CEST, UTC+2):** 16:15 UTC → `0 15 16 * * 1-5`

**To handle DST automatically**, set the `WEBSITE_TIME_ZONE` application setting:

```bash
az functionapp config appsettings set \
    --name $FUNCTION_APP \
    --resource-group $RESOURCE_GROUP \
    --settings WEBSITE_TIME_ZONE="W. Europe Standard Time"
```

Then use CET time directly in the CRON expression:

```
0 15 18 * * 1-5    → 18:15 local time, Mon-Fri (auto-adjusts for DST)
```

**Important:** The timezone name must be a Windows timezone identifier. `W. Europe Standard Time` covers Stockholm/CET. This works on both Windows and Linux consumption plans.

---

## 5. Docker + Azure Container Apps Alternative

If you prefer Docker for deployment (consistent environments, local-to-cloud parity), Azure Container Apps with scheduled jobs is the best fit.

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY pyproject.toml .

# Data directory will be mounted as an Azure Files volume
RUN mkdir -p /data

ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/data/swingtrader.db

CMD ["python", "-m", "src.main"]
```

### requirements.txt

```
yfinance>=0.2.36
pandas>=2.2.0
pandas-ta>=0.3.14b1
requests>=2.31.0
python-dotenv>=1.0.0
```

### Step 1: Create Azure Container Registry

```bash
RESOURCE_GROUP="swingtrader-rg"
LOCATION="northeurope"
ACR_NAME="swingtraderacr"  # Must be globally unique, lowercase alphanumeric

# Create resource group (if not already created)
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Container Registry (Basic tier)
az acr create \
    --name $ACR_NAME \
    --resource-group $RESOURCE_GROUP \
    --sku Basic \
    --admin-enabled true
```

### Step 2: Build and Push Docker Image

```bash
# Build and push in one command using ACR Tasks (builds in the cloud)
az acr build \
    --registry $ACR_NAME \
    --image swingtrader:latest \
    --file Dockerfile \
    .

# Or build locally and push:
# docker build -t $ACR_NAME.azurecr.io/swingtrader:latest .
# az acr login --name $ACR_NAME
# docker push $ACR_NAME.azurecr.io/swingtrader:latest
```

### Step 3: Create Container Apps Environment

```bash
# Create Container Apps environment
az containerapp env create \
    --name swingtrader-env \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

# Create Azure Files share for persistent SQLite storage
STORAGE_ACCOUNT="swingtraderstorage"
SHARE_NAME="scanner-data"

az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS

az storage share create \
    --name $SHARE_NAME \
    --account-name $STORAGE_ACCOUNT

# Get storage account key
STORAGE_KEY=$(az storage account keys list \
    --account-name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query "[0].value" -o tsv)

# Add storage to Container Apps environment
az containerapp env storage set \
    --name swingtrader-env \
    --resource-group $RESOURCE_GROUP \
    --storage-name scannerdata \
    --azure-file-account-name $STORAGE_ACCOUNT \
    --azure-file-account-key $STORAGE_KEY \
    --azure-file-share-name $SHARE_NAME \
    --access-mode ReadWrite
```

### Step 4: Create the Scheduled Job

```bash
# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# Create the scheduled job
az containerapp job create \
    --name swingtrader-job \
    --resource-group $RESOURCE_GROUP \
    --environment swingtrader-env \
    --trigger-type Schedule \
    --cron-expression "15 18 * * 1-5" \
    --image "$ACR_NAME.azurecr.io/swingtrader:latest" \
    --registry-server "$ACR_NAME.azurecr.io" \
    --registry-username "$ACR_USERNAME" \
    --registry-password "$ACR_PASSWORD" \
    --cpu 0.5 \
    --memory 1.0Gi \
    --replica-timeout 600 \
    --replica-retry-limit 1 \
    --env-vars \
        TELEGRAM_BOT_TOKEN="your-bot-token" \
        TELEGRAM_CHAT_ID="your-chat-id" \
        DATABASE_PATH="/data/swingtrader.db"
```

**Note on CRON in Container Apps:** Container Apps CRON uses standard 5-field CRON (no seconds field) and supports the `WEBSITE_TIME_ZONE` setting. Check if timezone is configurable or if it defaults to UTC — if UTC, adjust accordingly: `15 16 * * 1-5` for 18:15 CET in winter.

### Step 5: Mount the Volume

Volume mounting requires a YAML config for the job. Create `job.yaml`:

```yaml
# job.yaml
properties:
  configuration:
    triggerType: Schedule
    scheduleTriggerConfig:
      cronExpression: "15 16 * * 1-5"  # UTC — adjust for DST
      parallelism: 1
      replicaCompletionCount: 1
    replicaTimeout: 600
    replicaRetryLimit: 1
    registries:
      - server: swingtraderacr.azurecr.io
        username: swingtraderacr
        passwordSecretRef: acr-password
    secrets:
      - name: acr-password
        value: "<your-acr-password>"
      - name: telegram-token
        value: "<your-telegram-token>"
      - name: telegram-chat-id
        value: "<your-chat-id>"
  template:
    containers:
      - name: scanner
        image: swingtraderacr.azurecr.io/swingtrader:latest
        resources:
          cpu: 0.5
          memory: 1Gi
        env:
          - name: TELEGRAM_BOT_TOKEN
            secretRef: telegram-token
          - name: TELEGRAM_CHAT_ID
            secretRef: telegram-chat-id
          - name: DATABASE_PATH
            value: /data/swingtrader.db
        volumeMounts:
          - volumeName: scanner-data
            mountPath: /data
    volumes:
      - name: scanner-data
        storageName: scannerdata
        storageType: AzureFile
```

Apply the configuration:

```bash
az containerapp job update \
    --name swingtrader-job \
    --resource-group $RESOURCE_GROUP \
    --yaml job.yaml
```

### Step 6: Test Manually

```bash
# Trigger the job manually
az containerapp job start \
    --name swingtrader-job \
    --resource-group $RESOURCE_GROUP

# Check execution history
az containerapp job execution list \
    --name swingtrader-job \
    --resource-group $RESOURCE_GROUP \
    --output table

# View logs
az containerapp job logs show \
    --name swingtrader-job \
    --resource-group $RESOURCE_GROUP
```

---

## 6. Local Development Without Docker

The same Python code that runs on Azure should run locally with zero changes. This is critical for fast iteration during development.

### The Pattern: Environment-Aware Configuration

The key insight is detecting whether the code is running on Azure or locally, and adjusting paths and secrets accordingly.

```python
# src/config.py
"""
Configuration that works both locally and on Azure.

Locally: reads .env file, uses local SQLite path.
On Azure Functions: reads Application Settings, uses Blob Storage for SQLite.
On Azure Container Apps: reads env vars, uses mounted volume path.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Detect environment
IS_AZURE_FUNCTIONS = bool(os.getenv("AZURE_FUNCTIONS_ENVIRONMENT"))
IS_AZURE_CONTAINER = bool(os.getenv("CONTAINER_APP_NAME"))
IS_AZURE = IS_AZURE_FUNCTIONS or IS_AZURE_CONTAINER

# Load .env only when running locally
if not IS_AZURE:
    load_dotenv()

# --- Paths ---
if IS_AZURE_FUNCTIONS:
    # Azure Functions: SQLite handled via Blob Storage (download/upload per run)
    import tempfile
    DATA_DIR = Path(tempfile.gettempdir())
elif IS_AZURE_CONTAINER:
    # Container Apps: mounted volume at /data
    DATA_DIR = Path(os.getenv("DATABASE_PATH", "/data")).parent
else:
    # Local development
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"

DB_PATH = DATA_DIR / "swingtrader.db"

# --- Secrets ---
# These come from .env locally, Application Settings on Azure
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Tickers ---
TICKERS = [
    "ABB.ST", "ALFA.ST", "ASSA-B.ST", "ATCO-B.ST", "AZN.ST",
    "BOL.ST", "ELUX-B.ST", "ERIC-B.ST", "ESSITY-B.ST", "EVO.ST",
    "HEXA-B.ST", "HM-B.ST", "INVE-B.ST", "KINV-B.ST", "NIBE-B.ST",
    "SAND.ST", "SCA-B.ST", "SEB-A.ST", "SHB-A.ST", "SKF-B.ST",
    "SSAB-A.ST", "SWED-A.ST", "SWMA.ST", "TEL2-B.ST", "TELIA.ST",
    "VOLV-B.ST",
]

# --- Strategy Parameters ---
RSI_OVERSOLD = 35
BB_LENGTH = 20
BB_STD = 2.0
LOOKBACK = "8mo"
```

### Local Workflow

```bash
# 1. Activate virtual environment
cd ~/source/SwingTrader
source .venv/bin/activate

# 2. Create data directory (first time only)
mkdir -p data

# 3. Set up environment
cp .env.example .env
# Edit .env with your Telegram credentials

# 4. Run the scanner
python -m src.main

# 5. Run tests
pytest -v

# 6. Lint
ruff check src/ tests/
```

### File Structure for Dual-Mode Operation

```
SwingTrader/
├── src/
│   ├── main.py                # Entry point (works locally AND as import for Azure Function)
│   ├── config.py              # Environment-aware configuration
│   ├── data/
│   │   ├── fetcher.py
│   │   └── store.py           # SQLite operations (path comes from config)
│   ├── strategies/
│   │   └── mean_reversion.py
│   └── notifications/
│       └── telegram.py
├── azure-function/
│   ├── function_app.py        # Azure Functions wrapper — imports from src/
│   ├── host.json
│   ├── local.settings.json    # Not committed
│   └── requirements.txt
├── data/                       # Local SQLite DB (gitignored)
│   └── swingtrader.db
├── .env                        # Local secrets (gitignored)
├── .env.example
├── pyproject.toml
└── Dockerfile                  # For Container Apps deployment
```

The `function_app.py` in the Azure Function wrapper imports from `src/` and adds the Blob Storage download/upload logic. The same `src/` code runs locally via `python -m src.main`.

### Key Principle

The core logic in `src/` should have **zero Azure dependencies**. All Azure-specific code (Blob Storage, Function trigger) lives in `azure-function/function_app.py`. This way:

- `python -m src.main` works on your Mac with no Azure SDK installed
- The Azure Function wraps the same code with Blob Storage and timer trigger
- Docker deployment uses the same `src/` with a mounted volume for SQLite

---

## 7. CI/CD with GitHub Actions

### Azure Functions Deployment

```yaml
# .github/workflows/deploy-function.yml
name: Deploy Azure Function

on:
  push:
    branches: [main]
    paths:
      - "src/**"
      - "azure-function/**"
      - "requirements.txt"

permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          cd azure-function
          python -m pip install --upgrade pip
          pip install -r requirements.txt --target=".python_packages/lib/site-packages"

      - name: Run tests
        run: |
          pip install pytest
          pytest tests/ -v --ignore=tests/test_integration.py

      - name: Deploy to Azure Functions
        uses: Azure/functions-action@v1
        with:
          app-name: swingtrader-scanner
          package: azure-function
          publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

**Setup steps:**

1. In the Azure Portal, go to your Function App > Deployment Center > Manage publish profile
2. Download the publish profile XML
3. In your GitHub repo, go to Settings > Secrets > Actions
4. Create a new secret `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` with the XML content

### Container Apps Deployment

```yaml
# .github/workflows/deploy-container.yml
name: Deploy Container App

on:
  push:
    branches: [main]
    paths:
      - "src/**"
      - "Dockerfile"
      - "requirements.txt"

permissions:
  contents: read

env:
  ACR_NAME: swingtraderacr
  IMAGE_NAME: swingtrader
  RESOURCE_GROUP: swingtrader-rg

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Run tests
        run: |
          pip install -r requirements.txt pytest
          pytest tests/ -v --ignore=tests/test_integration.py

      - name: Login to Azure
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Login to ACR
        run: az acr login --name ${{ env.ACR_NAME }}

      - name: Build and push Docker image
        run: |
          docker build -t ${{ env.ACR_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:${{ github.sha }} .
          docker build -t ${{ env.ACR_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:latest .
          docker push ${{ env.ACR_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:${{ github.sha }}
          docker push ${{ env.ACR_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:latest

      - name: Update Container App Job
        run: |
          az containerapp job update \
            --name swingtrader-job \
            --resource-group ${{ env.RESOURCE_GROUP }} \
            --image ${{ env.ACR_NAME }}.azurecr.io/${{ env.IMAGE_NAME }}:${{ github.sha }}
```

**Setup steps:**

1. Create an Azure Service Principal:
   ```bash
   az ad sp create-for-rbac \
       --name "swingtrader-github" \
       --role contributor \
       --scopes /subscriptions/<subscription-id>/resourceGroups/swingtrader-rg \
       --sdk-auth
   ```
2. Copy the JSON output
3. In GitHub repo Settings > Secrets > Actions, create `AZURE_CREDENTIALS` with the JSON

---

## 8. Cost Breakdown

| Service | Monthly Cost | Notes |
|---------|-------------|-------|
| **Azure Functions (Consumption)** | $0 | Free tier: 1M executions, 400K GB-sec |
| **Blob Storage (< 1 GB, LRS)** | ~$0.02 | Hot tier, minimal operations |
| **Container Apps Job** | ~$0.02 | Pay per execution, consumption plan |
| **Azure Container Registry (Basic)** | ~$5.00 | Only if using Container Apps |
| **Azure SQL Database (Serverless)** | ~$5-15 | Only if replacing SQLite |
| **Azure VM B1s** | ~$3.80 | 1-year reserved pricing |
| **Azure VM B1ls** | ~$2.28 | 1-year reserved, 0.5 GiB RAM |
| **App Service B1** | ~$13.00 | Overkill for cron-only workload |
| **Application Insights** | $0 | Free for < 5 GB/month ingest |

**Recommended setup (Azure Functions + Blob Storage):**

| Component | Cost |
|-----------|------|
| Azure Functions | $0.00 |
| Blob Storage | $0.02 |
| Application Insights | $0.00 |
| **Total** | **$0.02/month** |

**Container Apps setup:**

| Component | Cost |
|-----------|------|
| Container Apps Job | $0.02 |
| Azure Files | $0.06 |
| Azure Container Registry (Basic) | $5.00 |
| **Total** | **~$5.08/month** |

The $5 ACR cost dominates the Container Apps setup. You can reduce this to ~$0.08/month by using GitHub Container Registry (free) or Docker Hub (free) instead of ACR.

---

## 9. Comparison: Azure vs Hetzner vs Local

| Factor | Azure Functions | Azure Container Apps | Hetzner VPS (CX11) | Local Mac |
|--------|----------------|---------------------|---------------------|-----------|
| **Monthly cost** | ~$0 | ~$0-5 | ~$3.30 | $0 |
| **Server maintenance** | None | None | You (OS updates, SSH) | None |
| **Always-on** | No (scheduled) | No (scheduled) | Yes (24/7) | Must be on |
| **Docker support** | No | Yes | Yes | Yes |
| **SQLite native** | No (Blob workaround) | Yes (volume mount) | Yes | Yes |
| **Cold start** | 5-15 sec | Image pull ~10 sec | None (cron) | None |
| **Deployment** | `func publish` / GH Actions | `docker push` / GH Actions | `git pull` + cron | `python main.py` |
| **Monitoring** | Application Insights (built-in) | Container Apps logs | Manual (logs, cron) | Terminal output |
| **DST handling** | `WEBSITE_TIME_ZONE` setting | Manual CRON adjustment | `timedatectl` | System timezone |
| **Scales up** | Auto (if needed) | Auto (if needed) | Resize VPS | N/A |
| **Web dashboard later** | Separate resource needed | Add as second container | Same VPS | localhost |
| **Vendor lock-in** | Azure Functions SDK | Docker (portable) | None | None |
| **Setup time** | ~30 min | ~45 min | ~30 min | ~5 min |
| **EU data center** | North Europe (Ireland), West Europe (Netherlands) | Same | Falkenstein (DE), Helsinki (FI) | N/A |

### When to Choose What

**Azure Functions** is the best choice when:
- You want zero maintenance and zero cost
- You are already in the Azure ecosystem
- You do not need SQLite (or are fine with the Blob Storage workaround)
- You want built-in monitoring and alerting

**Azure Container Apps** is the best choice when:
- You want Docker for deployment consistency
- You need native SQLite with persistent volumes
- You plan to add more containers later (web dashboard, API)
- You want portability (same Docker image runs anywhere)

**Hetzner VPS** is the best choice when:
- You want a real server with full SSH access
- You prefer simplicity (cron + Python script, nothing more)
- You want the cheapest always-on option (useful if adding a web dashboard)
- You want to avoid cloud vendor complexity

**Local Mac** is the best choice when:
- You are still building and testing the strategy
- You want fastest possible iteration (edit, run, see results)
- You do not need reliable unattended execution yet

### Recommended Path

1. **Phase 1 (now):** Run locally on your Mac. Focus on strategy logic.
2. **Phase 2 (strategy works):** Deploy to Azure Functions (free, zero maintenance).
3. **Phase 3 (want dashboard):** Either add App Service for web UI, or move everything to Container Apps with Docker.

---

## Summary

For a personal swing trading scanner that runs once daily, **Azure Functions on the Consumption plan** is the optimal Azure choice. It costs nothing, requires no infrastructure management, and the timer trigger handles scheduling with DST-aware timezone support. The only wrinkle is SQLite — use the Blob Storage download/upload pattern to work around the ephemeral filesystem.

If you prefer Docker for deployment consistency (and plan to run the same image locally and in the cloud), **Azure Container Apps Jobs** is the cleaner solution. SQLite works natively with mounted volumes. The $5/month Azure Container Registry cost is the main expense, avoidable by using GitHub Container Registry instead.

Both approaches support the same local development workflow: `python -m src.main` runs the scanner on your Mac with zero Docker or Azure dependencies. Environment detection in `config.py` handles the differences automatically.
