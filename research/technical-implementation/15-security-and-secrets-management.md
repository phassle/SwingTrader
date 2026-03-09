# 15 - Security and Secrets Management

> Research date: 2026-03-09
> Goal: Define how SwingTrader manages secrets and sensitive configuration across all environments — local development, Docker, Azure, and CI/CD.
> Prerequisites: [06-project-structure-and-setup.md](06-project-structure-and-setup.md), [09-azure-container-apps-deep-dive.md](09-azure-container-apps-deep-dive.md), [12-dotnet-aspire-orchestration.md](12-dotnet-aspire-orchestration.md)

---

## Table of Contents

1. [Secrets Overview](#1-secrets-overview)
2. [Local Development: .env + python-dotenv](#2-local-development-env--python-dotenv)
3. [Docker: env-file](#3-docker-env-file)
4. [.NET Aspire: User Secrets](#4-net-aspire-user-secrets)
5. [Azure Container Apps Secrets](#5-azure-container-apps-secrets)
6. [Azure Key Vault](#6-azure-key-vault)
7. [GitHub Actions Secrets](#7-github-actions-secrets)
8. [Git Security](#8-git-security)
9. [Complete .env.example Template](#9-complete-envexample-template)
10. [Secret Rotation Procedures](#10-secret-rotation-procedures)

---

## 1. Secrets Overview

### What needs to be secret

| Secret | Used By | Environment(s) |
|--------|---------|-----------------|
| `TELEGRAM_BOT_TOKEN` | TelegramNotifier | All |
| `TELEGRAM_CHAT_ID` | TelegramNotifier | All |
| `COSMOS_DB_CONNECTION_STRING` | Data layer | Docker, Azure |
| `COSMOS_DB_KEY` | Data layer (alternative) | Docker, Azure |
| `HEALTHCHECKS_PING_URL` | Monitoring | All |
| `AZURE_CLIENT_ID` | Azure auth (if using managed identity) | Azure |

### Principle: Never hardcode secrets

Every secret must come from the environment. The application reads `os.environ[...]` or uses `python-dotenv` — never from a config file checked into git.

---

## 2. Local Development: .env + python-dotenv

### Setup

```bash
pip install python-dotenv
```

### .env file (never committed)

```bash
# .env — local development only
TELEGRAM_BOT_TOKEN=7123456789:AAH1bGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
TELEGRAM_CHAT_ID=123456789
COSMOS_DB_CONNECTION_STRING=AccountEndpoint=https://swingtrader-dev.documents.azure.com:443/;AccountKey=...
HEALTHCHECKS_PING_URL=https://hc-ping.com/your-uuid-here
```

### Loading in Python

```python
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env into os.environ

token = os.environ["TELEGRAM_BOT_TOKEN"]
```

### Where to call load_dotenv()

Call it once at the application entry point (e.g., `main.py` or the top of your pipeline script). Do not scatter `load_dotenv()` calls across modules — it should happen once before any module reads `os.environ`.

```python
# main.py
from dotenv import load_dotenv
load_dotenv()

# Now all modules can use os.environ safely
from scanner.pipeline import run_daily_scan
run_daily_scan()
```

### Best practice: fail fast on missing secrets

```python
import os
import sys

REQUIRED_SECRETS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
]

def validate_secrets():
    """Check all required secrets are set. Call at startup."""
    missing = [key for key in REQUIRED_SECRETS if not os.environ.get(key)]
    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in the values.")
        sys.exit(1)
```

---

## 3. Docker: env-file

### docker-compose.yml

```yaml
services:
  scanner:
    build: .
    env_file:
      - .env
```

This loads the same `.env` file into the container's environment. No code changes needed — `os.environ` works the same inside the container.

### Alternative: explicit environment block

For production or when you want to be explicit about which variables the container receives:

```yaml
services:
  scanner:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
      - COSMOS_DB_CONNECTION_STRING=${COSMOS_DB_CONNECTION_STRING}
```

### Docker secrets (Swarm only)

Docker secrets (`docker secret create`) are a Swarm feature. Since SwingTrader uses Docker Compose (not Swarm), use `env_file` instead.

---

## 4. .NET Aspire: User Secrets

If using .NET Aspire as the orchestrator (see [12-dotnet-aspire-orchestration.md](12-dotnet-aspire-orchestration.md)), secrets are managed via the .NET user-secrets tool.

### Setup

```bash
cd src/SwingTrader.AppHost
dotnet user-secrets init
dotnet user-secrets set "Parameters:telegram-bot-token" "7123456789:AAH..."
dotnet user-secrets set "Parameters:telegram-chat-id" "123456789"
```

### Passing to Python container

In `Program.cs`:

```csharp
var telegramToken = builder.AddParameter("telegram-bot-token", secret: true);
var telegramChatId = builder.AddParameter("telegram-chat-id", secret: true);

var scanner = builder.AddPythonProject("scanner", "../scanner")
    .WithEnvironment("TELEGRAM_BOT_TOKEN", telegramToken)
    .WithEnvironment("TELEGRAM_CHAT_ID", telegramChatId);
```

Aspire injects these as environment variables into the Python container. The Python code reads `os.environ["TELEGRAM_BOT_TOKEN"]` as normal — no awareness of Aspire needed.

### Where are user secrets stored?

- macOS: `~/.microsoft/usersecrets/<user-secrets-id>/secrets.json`
- Linux: `~/.microsoft/usersecrets/<user-secrets-id>/secrets.json`
- Windows: `%APPDATA%\Microsoft\UserSecrets\<user-secrets-id>\secrets.json`

These are plain JSON files, not encrypted. They provide isolation from source code, not security at rest.

---

## 5. Azure Container Apps Secrets

### Setting secrets via CLI

```bash
az containerapp secret set \
  --name swingtrader-scanner \
  --resource-group swingtrader-rg \
  --secrets \
    telegram-bot-token=7123456789:AAH... \
    telegram-chat-id=123456789 \
    cosmos-db-connection-string="AccountEndpoint=..."
```

### Referencing in environment variables

```bash
az containerapp update \
  --name swingtrader-scanner \
  --resource-group swingtrader-rg \
  --set-env-vars \
    TELEGRAM_BOT_TOKEN=secretref:telegram-bot-token \
    TELEGRAM_CHAT_ID=secretref:telegram-chat-id \
    COSMOS_DB_CONNECTION_STRING=secretref:cosmos-db-connection-string
```

### How it works

Azure Container Apps secrets are:
- Encrypted at rest
- Injected as environment variables at container startup
- Not visible in logs or the Azure portal after creation
- Scoped to the container app (not shared across apps)

### Updating a secret

```bash
# Update the value
az containerapp secret set --name swingtrader-scanner --resource-group swingtrader-rg \
  --secrets telegram-bot-token=NEW_TOKEN_VALUE

# Create a new revision to pick up the change
az containerapp update --name swingtrader-scanner --resource-group swingtrader-rg \
  --set-env-vars TELEGRAM_BOT_TOKEN=secretref:telegram-bot-token
```

---

## 6. Azure Key Vault

For production use beyond Phase 1, Key Vault provides centralized secret management with audit logging and access policies.

### When to use Key Vault vs Container Apps secrets

| Feature | Container Apps secrets | Key Vault |
|---------|----------------------|-----------|
| Complexity | Simple | More setup |
| Cost | Free | ~$0.03/10k operations |
| Audit logging | No | Yes |
| Secret rotation | Manual | Can automate |
| Access control | Per container app | RBAC policies |
| **Recommendation** | **Phase 1** | **Phase 2+** |

### Setup (Phase 2+)

```bash
# Create Key Vault
az keyvault create --name swingtrader-kv --resource-group swingtrader-rg --location swedencentral

# Add secrets
az keyvault secret set --vault-name swingtrader-kv --name telegram-bot-token --value "7123456789:AAH..."

# Grant access to Container App's managed identity
az keyvault set-policy --name swingtrader-kv \
  --object-id <managed-identity-object-id> \
  --secret-permissions get list
```

### Reading from Key Vault in Python

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://swingtrader-kv.vault.azure.net", credential=credential)

token = client.get_secret("telegram-bot-token").value
```

---

## 7. GitHub Actions Secrets

### Setting secrets

Go to: Repository → Settings → Secrets and variables → Actions → New repository secret

| Secret name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | Bot token |
| `TELEGRAM_CHAT_ID` | Chat ID |
| `AZURE_CREDENTIALS` | Service principal JSON (for Azure deployment) |
| `COSMOS_DB_CONNECTION_STRING` | Connection string (for integration tests) |

### Using in workflows

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Azure Container Apps
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        run: |
          az containerapp secret set \
            --name swingtrader-scanner \
            --resource-group swingtrader-rg \
            --secrets telegram-bot-token=$TELEGRAM_BOT_TOKEN
```

### Secret scoping

- **Repository secrets:** Available to all workflows in the repo. Use this for most secrets.
- **Environment secrets:** Scoped to a deployment environment (e.g., `production`). Use for production-only secrets if you have separate staging/production.

---

## 8. Git Security

### .gitignore essentials

```gitignore
# Secrets — NEVER commit these
.env
.env.local
.env.production
*.pem
*.key

# IDE and OS
.vscode/
.idea/
.DS_Store
__pycache__/

# Python
*.pyc
.venv/
dist/
*.egg-info/

# .NET Aspire
**/appsettings.*.json
!**/appsettings.json

# Data files (could contain sensitive info)
*.db
*.sqlite
data/
```

### Pre-commit hook: prevent secret commits

Install `pre-commit` to catch accidental secret commits:

```bash
pip install pre-commit
```

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### Initial setup

```bash
# Generate a baseline (marks existing "secrets" as known/accepted)
detect-secrets scan > .secrets.baseline

# Install the hook
pre-commit install
```

Now, any `git commit` that introduces a string that looks like a secret (API key, token, password) will be blocked with a warning.

### gitleaks (alternative)

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
```

Both `detect-secrets` and `gitleaks` work well. Pick one — `detect-secrets` is more configurable, `gitleaks` has better pattern matching for known API key formats.

---

## 9. Complete .env.example Template

This file **is** committed to git. It documents every required variable without containing real values.

```bash
# =============================================================================
# SwingTrader Environment Configuration
# =============================================================================
# Copy this file to .env and fill in real values.
# NEVER commit .env to git.
# =============================================================================

# --- Telegram Bot ---
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
TELEGRAM_CHAT_ID=your-chat-id

# --- Database (Cosmos DB) ---
# Local development can use SQLite instead (leave blank)
COSMOS_DB_CONNECTION_STRING=
COSMOS_DB_DATABASE_NAME=swingtrader

# --- Monitoring ---
HEALTHCHECKS_PING_URL=https://hc-ping.com/your-uuid-here

# --- Scanner Configuration (non-secret, but environment-specific) ---
SCAN_SCHEDULE=18:30
LOG_LEVEL=INFO
DRY_RUN=false

# --- Azure (only needed for Azure deployment) ---
# AZURE_CLIENT_ID=
# AZURE_TENANT_ID=
# AZURE_SUBSCRIPTION_ID=
```

---

## 10. Secret Rotation Procedures

### Telegram bot token

1. Open BotFather → `/revoke` → select your bot
2. BotFather issues a new token
3. Update everywhere:
   - Local: `.env`
   - Docker: `.env` → restart container
   - Azure: `az containerapp secret set ...` → create new revision
   - GitHub Actions: Repository settings → update secret
   - Aspire: `dotnet user-secrets set ...`

### Cosmos DB key

1. Azure Portal → Cosmos DB → Keys → Regenerate Secondary Key
2. Update connection strings to use secondary key
3. Regenerate Primary Key
4. This allows zero-downtime rotation

### When to rotate

- **Immediately:** If a secret is accidentally committed to git, even if the commit is later reverted (the secret is in git history forever unless you rewrite history)
- **Periodically:** Every 90 days for production secrets (Phase 2+, when you have Key Vault automation)
- **On personnel changes:** If someone with access leaves the project

---

*Next: [16-omx-ticker-list-management.md](16-omx-ticker-list-management.md) — Managing the list of stocks to scan.*
