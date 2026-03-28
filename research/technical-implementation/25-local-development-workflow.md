# 25 - Local Development Workflow

> Research date: 2026-03-10
> Goal: Define the complete local development workflow for SwingTrader — from initial setup to running daily scans, viewing results, debugging issues, and iterating on code changes. This is the "getting started" guide for new developers.
> Prerequisites: [18-aspire-apphost-implementation.md](18-aspire-apphost-implementation.md), [19-python-scanner-bootstrap-implementation.md](19-python-scanner-bootstrap-implementation.md), [06-project-structure-and-setup.md](06-project-structure-and-setup.md)

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites and Installation](#prerequisites-and-installation)
3. [Initial Project Setup](#initial-project-setup)
4. [Configuration Setup](#configuration-setup)
5. [First Run](#first-run)
6. [Viewing Results](#viewing-results)
7. [Development Iteration Cycle](#development-iteration-cycle)
8. [Debugging](#debugging)
9. [Troubleshooting Common Issues](#troubleshooting-common-issues)
10. [Data Management](#data-management)

---

## Overview

This guide walks through the **complete local development workflow** from zero to running scanner. Target audience:

- New developers joining the project
- Existing developers setting up on new machine
- Anyone wanting to contribute or experiment

**Goal:** Get from "clone repo" to "scan results in Telegram" in <15 minutes.

**Prerequisites:**
- macOS, Windows, or Linux
- Terminal/command line familiarity
- Basic understanding of .NET, Python, Docker

---

## Prerequisites and Installation

### Required Tools

| Tool | Version | Purpose | Installation |
|------|---------|---------|--------------|
| .NET SDK | 9.0+ | Aspire AppHost | [dotnet.microsoft.com](https://dotnet.microsoft.com/download) |
| Python | 3.11+ | Scanner application | [python.org](https://www.python.org/downloads/) |
| Docker Desktop | Latest | Cosmos DB emulator | [docker.com](https://www.docker.com/products/docker-desktop/) |
| Git | Any | Repository management | [git-scm.com](https://git-scm.com/downloads) |

### Installation Steps

**1. Install .NET SDK:**
```bash
# macOS (Homebrew)
brew install --cask dotnet-sdk

# Windows (winget)
winget install Microsoft.DotNet.SDK.9

# Verify
dotnet --version  # Should show 9.x.x
```

**2. Install Python:**
```bash
# macOS (Homebrew)
brew install python@3.11

# Windows (winget)
winget install Python.Python.3.11

# Verify
python --version  # Should show 3.11+
```

**3. Install Docker Desktop:**
- Download from [docker.com](https://www.docker.com/products/docker-desktop/)
- Run installer
- Start Docker Desktop
- Verify: `docker ps` (should show no errors)

**4. Verify all tools:**
```bash
dotnet --version   # 9.x.x
python --version   # 3.11.x
docker --version   # 27.x.x
git --version      # 2.x.x
```

---

## Initial Project Setup

### Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/YOUR_ORG/SwingTrader.git
cd SwingTrader

# Verify structure
ls -la
# Should see: src/, research/, README.md, .gitignore, etc.
```

### Install Python Dependencies

```bash
# Navigate to Scanner directory
cd src/Scanner

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Verify key packages installed
pip list | grep -E "azure-cosmos|pandas-ta|yfinance|requests"
```

**Expected packages:**
- azure-cosmos==4.6.0
- pandas-ta==0.3.14b
- yfinance==0.2.37
- requests==2.31.0
- pandas==2.2.0
- numpy==1.26.4

### Restore .NET Projects

```bash
# Navigate back to repository root
cd ../..

# Restore .NET projects
dotnet restore

# Build AppHost (verifies no compilation errors)
dotnet build src/AppHost/AppHost.csproj

# Expected output: "Build succeeded."
```

---

## Configuration Setup

### User Secrets Setup

**Why User Secrets:**
- Never commit secrets to git
- Per-machine configuration
- Seamless Aspire integration

**Setup steps:**

```bash
# Initialize User Secrets for AppHost
dotnet user-secrets init --project src/AppHost

# Set Telegram bot token (from BotFather)
dotnet user-secrets set "TelegramBotToken" "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ" --project src/AppHost

# Set Telegram chat ID
# Get your chat ID: Message @userinfobot on Telegram, it will reply with your chat ID
dotnet user-secrets set "TelegramChatId" "987654321" --project src/AppHost

# Verify secrets set
dotnet user-secrets list --project src/AppHost
```

**Expected output:**
```
TelegramBotToken = 123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ
TelegramChatId = 987654321
```

### Create .env.example (Optional)

**For non-Aspire runs** (direct Python execution):

```bash
# Create .env.example in src/Scanner/
cat > src/Scanner/.env.example <<EOF
# Cosmos DB (Emulator defaults)
COSMOS_CONNECTION_STRING=AccountEndpoint=https://localhost:8081/;AccountKey=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
COSMOS_DATABASE_NAME=SwingTraderDB

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=human

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ
TELEGRAM_CHAT_ID=987654321

# Scan behavior
SCAN_MODE=daily
TICKER_UNIVERSE=omx_large_cap
DRY_RUN=false
EOF
```

**Note:** Copy `.env.example` to `.env` and fill in real values if running Python directly (without Aspire).

---

## First Run

### Start AppHost

```bash
# From repository root
dotnet run --project src/AppHost
```

**Expected output:**
```
info: Aspire.Hosting[0]
      Aspire version: 9.0.0
info: Aspire.Hosting[0]
      Dashboard URL: http://localhost:15888
info: Aspire.Hosting[0]
      Starting resource: cosmos
info: Aspire.Hosting[0]
      Starting resource: scanner
info: Aspire.Hosting[0]
      All resources started successfully
```

**Timeline:**
- T+0s: AppHost starts
- T+5s: Cosmos emulator container starting
- T+10s: Cosmos emulator ready
- T+12s: Python scanner starts
- T+15s: Scanner validates config
- T+20s: Scanner connects to Cosmos
- T+25s: Scanner bootstraps containers
- T+30s: Scanner fetches market data (150 tickers × 0.2s = 30s)
- T+60s: Indicators calculated
- T+65s: Signals generated
- T+70s: Telegram notification sent
- T+75s: Scan complete

**What to watch:**
1. **Aspire Dashboard opens automatically:** http://localhost:15888
2. **Cosmos emulator status:** Should show "Running" (green)
3. **Scanner status:** Should show "Running" (green) then "Exited (0)" (success)
4. **Telegram notification:** Check Telegram app for scan results

---

## Viewing Results

### Aspire Dashboard

**URL:** http://localhost:15888

**Key panels:**

1. **Resources tab:**
   - Shows `cosmos` and `scanner` status
   - Green = running, Gray = exited successfully, Red = failed

2. **Logs tab:**
   - Click `scanner` resource
   - View logs in real-time
   - Filter by log level (DEBUG, INFO, WARNING, ERROR)
   - Search logs (e.g., "Fetching data for")

3. **Environment tab:**
   - Click `scanner` resource
   - View injected environment variables (secrets hidden)

4. **Traces tab (Phase 2):**
   - Distributed tracing (if OpenTelemetry added)

### Cosmos DB Data Explorer

**URL:** https://localhost:8081/_explorer/index.html

**Note:** Accept browser security warning (emulator uses self-signed cert).

**Navigation:**
1. Expand `SwingTraderDB` database
2. Expand containers: `stocks`, `daily_prices`, `indicators`, `signals`, `scan_runs`
3. Click `signals` container → Items → Browse documents
4. View signal documents (ticker, strategy, scores, price levels)

**Example query:**
```sql
SELECT * FROM signals s WHERE s.date = "2026-03-10" ORDER BY s.total_score DESC
```

### Telegram App

**Check for notification:**
1. Open Telegram on phone or desktop
2. Find message from your bot (name from BotFather)
3. Review scan results (tickers, strategies, entry/stop/target)

**If no message:**
- Check Telegram bot token and chat ID correct (`dotnet user-secrets list`)
- Check scanner logs for "Telegram notification sent successfully"
- Check Telegram privacy settings (bot may be blocked)

---

## Development Iteration Cycle

### Typical Workflow

**1. Edit Python code:**
```bash
# Open src/Scanner/main.py in editor
# Make changes (e.g., adjust strategy logic)
```

**2. Restart scanner:**
- **Option A (via Aspire Dashboard):** Right-click `scanner` → Restart
- **Option B (via terminal):** Ctrl+C AppHost, run `dotnet run --project src/AppHost` again

**3. View logs:**
- Aspire Dashboard → Logs tab → Filter `scanner`

**4. Verify results:**
- Cosmos Data Explorer → Check updated documents
- Telegram → Check for new notification

**Typical iteration time:** 10-15 seconds (restart scanner, see results)

### Hot Reload (Future)

**Phase 1:** No hot reload (must restart scanner).

**Phase 2:** Add file watcher to auto-restart scanner on code changes:
```python
# In AppHost Program.cs
var scanner = builder.AddExecutable("scanner", "python", "../Scanner", "main.py")
    .WithEnvironment(...)
    .WaitFor(cosmos)
    .WithArgs("--watch");  # Hypothetical flag to enable file watching
```

---

## Debugging

### Python Debugging (VS Code)

**1. Create launch.json:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: SwingTrader Scanner",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/Scanner/main.py",
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/src/Scanner/.env",
      "cwd": "${workspaceFolder}/src/Scanner"
    }
  ]
}
```

**2. Set breakpoint in main.py**

**3. Press F5 to start debugging**

**Note:** Requires `.env` file with all environment variables (see Configuration Setup).

### C# Debugging (AppHost)

**1. Open src/AppHost/Program.cs in VS Code or Rider**

**2. Set breakpoint (e.g., where Cosmos connection string configured)**

**3. Press F5 to start debugging**

**4. Step through resource configuration**

**Use case:** Debug Aspire configuration (e.g., verify connection string expression resolves correctly).

### Cosmos Emulator Debugging

**Check emulator status:**
```bash
# List running containers
docker ps | grep cosmos

# View emulator logs
docker logs <container_id>

# Restart emulator (if stuck)
docker restart <container_id>
```

**Common issues:**
- Port 8081 already in use → Kill process or change port
- Emulator not starting → Check Docker Desktop running, sufficient resources (4GB RAM minimum)

---

## Troubleshooting Common Issues

### Issue 1: Scanner exits immediately with code 1

**Symptoms:**
- Aspire Dashboard shows `scanner` status "Exited (1)"
- No logs visible

**Cause:** Configuration validation failed.

**Solution:**
```bash
# Check User Secrets
dotnet user-secrets list --project src/AppHost

# Verify required secrets present:
# - TelegramBotToken
# - TelegramChatId

# If missing, set them:
dotnet user-secrets set "TelegramBotToken" "YOUR_TOKEN" --project src/AppHost
dotnet user-secrets set "TelegramChatId" "YOUR_CHAT_ID" --project src/AppHost

# Restart AppHost
```

---

### Issue 2: Scanner logs "Failed to connect to Cosmos DB"

**Symptoms:**
- Scanner exits with code 2
- Logs show "Connection refused" or "Connection timeout"

**Cause:** Cosmos emulator not ready or not running.

**Solution:**
```bash
# Check emulator status
docker ps | grep cosmos

# If not running, check Docker Desktop
open -a Docker  # macOS

# Verify emulator endpoint accessible
curl -k https://localhost:8081/_explorer/index.html
# Should return HTML (ignore SSL warning)

# If still failing, restart emulator
docker restart <cosmos_container_id>

# Wait 10 seconds, restart scanner
```

---

### Issue 3: No Telegram notification received

**Symptoms:**
- Scanner completes successfully (exit 0)
- Logs show "Telegram notification sent successfully"
- No message in Telegram app

**Cause:** Incorrect chat ID or bot blocked.

**Solution:**
```bash
# Verify chat ID
# Message @userinfobot on Telegram, get your chat ID

# Test bot manually
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "<YOUR_CHAT_ID>", "text": "Test message"}'

# If 403 error: Start conversation with bot (send /start)
# If 400 error: Chat ID incorrect

# Update chat ID
dotnet user-secrets set "TelegramChatId" "CORRECT_CHAT_ID" --project src/AppHost
```

---

### Issue 4: Indicators not calculated (insufficient history)

**Symptoms:**
- Logs show "Ticker X has only Y days of history (need 200), skipping"
- No signals generated for certain tickers

**Cause:** Newly listed stocks or data gaps.

**Solution:**
```bash
# This is expected behavior — ticker will be included once 200 days accumulated

# To verify data in Cosmos:
# 1. Open Data Explorer: https://localhost:8081/_explorer/index.html
# 2. Query daily_prices container:
#    SELECT COUNT(1) as count FROM daily_prices WHERE ticker = "TICKER.ST"
# 3. If count < 200, indicators will be skipped

# Phase 1: No action needed (by design)
# Phase 2: Add fallback to shorter lookback periods
```

---

### Issue 5: yfinance fetch timeout

**Symptoms:**
- Logs show "Failed to fetch TICKER.ST: ReadTimeout"
- Some tickers fail to fetch

**Cause:** Network issues or Yahoo Finance slow.

**Solution:**
- **Transient:** Re-run scan (fetcher retries automatically)
- **Persistent:** Check internet connection, try different network
- **Workaround:** Increase delay between requests (edit `src/Scanner/fetcher.py`, increase `time.sleep(0.2)` to `time.sleep(0.5)`)

---

## Data Management

### Reset All Data

**Use case:** Schema changed, want clean slate.

```bash
# Stop AppHost (Ctrl+C)

# Delete Cosmos emulator volume
docker volume ls | grep swingtrader
docker volume rm swingtrader-cosmos-data

# Restart AppHost
dotnet run --project src/AppHost

# Containers recreated automatically, database empty
```

---

### Seed Test Data

**Use case:** Want predictable data for testing.

```bash
# Create seed script
cat > src/Scanner/seed_data.py <<EOF
from repository import CosmosRepository
from datetime import date, timedelta

connection_string = "AccountEndpoint=https://localhost:8081/;..."
database_name = "SwingTraderDB"

repo = CosmosRepository(connection_string, database_name)
repo.bootstrap()

# Seed stocks
repo.stocks.upsert_stock("TEST.ST", "Test Corp", "Technology", 1000000000)

# Seed prices (last 250 days)
for i in range(250):
    calc_date = date.today() - timedelta(days=250-i)
    repo.daily_prices.upsert_price(
        ticker="TEST.ST",
        date=calc_date,
        open=100 + i*0.1,
        high=105 + i*0.1,
        low=95 + i*0.1,
        close=100 + i*0.1,
        volume=1000000,
    )

print("Seed data created!")
EOF

# Run seed script
python src/Scanner/seed_data.py
```

---

### Export Data for Analysis

**Use case:** Want to analyze scan results in Excel/Python.

```bash
# Query Cosmos, export to JSON
# 1. Open Data Explorer: https://localhost:8081/_explorer/index.html
# 2. Query signals container:
#    SELECT * FROM signals WHERE signals.date >= "2026-03-01"
# 3. Click "Download" button → Save as JSON

# Or use Python script:
cat > export_signals.py <<EOF
from repository import CosmosRepository
import json

connection_string = "..."
database_name = "SwingTraderDB"

repo = CosmosRepository(connection_string, database_name)
repo.bootstrap()

signals = repo.signals.query("SELECT * FROM signals WHERE signals.date >= '2026-03-01'")

with open("signals.json", "w") as f:
    json.dump(signals, f, indent=2)

print(f"Exported {len(signals)} signals to signals.json")
EOF

python export_signals.py
```

---

## Summary

### Key Commands

```bash
# Start scanner
dotnet run --project src/AppHost

# View dashboard
open http://localhost:15888

# View Cosmos data
open https://localhost:8081/_explorer/index.html

# Check secrets
dotnet user-secrets list --project src/AppHost

# Reset data
docker volume rm swingtrader-cosmos-data

# Install Python dependencies
pip install -r src/Scanner/requirements.txt
```

### Development Cycle

1. **Edit code:** `src/Scanner/main.py` or strategy files
2. **Restart scanner:** Right-click in Aspire Dashboard → Restart
3. **View logs:** Aspire Dashboard → Logs tab
4. **Verify results:** Cosmos Data Explorer + Telegram

**Iteration time:** ~10-15 seconds

### Getting Help

**If stuck:**
1. Check logs in Aspire Dashboard (Logs tab)
2. Verify secrets: `dotnet user-secrets list --project src/AppHost`
3. Check Cosmos emulator: `docker ps | grep cosmos`
4. Consult troubleshooting section above
5. Check [17-monitoring-and-alerting.md](17-monitoring-and-alerting.md) for common failure modes

---

## Next Steps

1. **Experiment with strategies:** Edit `src/Scanner/strategies/` files, tweak setup criteria
2. **Test backtesting:** Run scanner on historical dates, compare signals
3. **Deploy to Azure:** See [26-azure-containerization-and-azd.md](26-azure-containerization-and-azd.md)

---

## References

- [.NET Aspire local development](https://learn.microsoft.com/en-us/dotnet/aspire/fundamentals/setup-tooling)
- [Cosmos DB Emulator](https://learn.microsoft.com/en-us/azure/cosmos-db/docker-emulator-linux)
- [.NET User Secrets](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)
- [18-aspire-apphost-implementation.md](18-aspire-apphost-implementation.md) — AppHost architecture
- [19-python-scanner-bootstrap-implementation.md](19-python-scanner-bootstrap-implementation.md) — Config and logging
- [06-project-structure-and-setup.md](06-project-structure-and-setup.md) — Project layout
