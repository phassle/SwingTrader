# 10 - Hetzner + Coolify Deep Dive

> Research date: 2026-03-08
> Prerequisite: [08-docker-compose-hosting-alternatives.md](08-docker-compose-hosting-alternatives.md) (general hosting overview)
> Goal: Complete end-to-end guide for deploying SwingTrader on Hetzner Cloud with Coolify v4 as a self-hosted PaaS.

---

## Table of Contents

1. [Why Hetzner + Coolify](#1-why-hetzner--coolify)
2. [Hetzner Server Selection](#2-hetzner-server-selection)
3. [Coolify Overview](#3-coolify-overview)
4. [Complete Hetzner + Coolify Setup](#4-complete-hetzner--coolify-setup)
5. [docker-compose.yml for Coolify](#5-docker-composeyml-for-coolify)
6. [Scheduled Execution](#6-scheduled-execution)
7. [Persistent Storage](#7-persistent-storage)
8. [Adding the Dashboard (Streamlit)](#8-adding-the-dashboard-streamlit)
9. [SSL and Domain Setup](#9-ssl-and-domain-setup)
10. [Monitoring and Maintenance](#10-monitoring-and-maintenance)
11. [Cost Breakdown](#11-cost-breakdown)
12. [Troubleshooting](#12-troubleshooting)
13. [Migration Path](#13-migration-path)

---

## 1. Why Hetzner + Coolify

### The Problem

You want to deploy a Python Docker Compose project with:
- Minimal cost (personal tool, not a business)
- Web UI for managing deployments (not just SSH + manual `docker compose up`)
- GitHub integration with auto-deploy on push
- Persistent SQLite storage
- Easy SSL when you add a web dashboard later
- EU datacenter close to Sweden

### The Solution: Hetzner + Coolify

**Hetzner Cloud** is the best price/performance VPS provider in Europe. Their CX22 at **EUR 4.35/month** gives you 2 vCPU, 4 GB RAM, and 40 GB NVMe SSD. Datacenters in Helsinki (Finland) and Falkenstein (Germany) are both close to Sweden with sub-10ms latency.

**Coolify** is an open-source, self-hosted PaaS (Platform as a Service). It is a free alternative to Railway, Vercel, and Render that you install on your own server. It gives you:

- **Web dashboard** for managing services, viewing logs, and monitoring
- **GitHub integration** with automatic deployments on push to main
- **Docker Compose support** — paste your `docker-compose.yml` and it deploys
- **Environment variable management** in the UI (no `.env` files on the server)
- **SSL certificates** via Let's Encrypt, automatically renewed
- **Persistent volumes** that survive redeployments
- **Log viewer** with real-time streaming

**Together**, they give you a Railway-like developer experience at EUR 4.35/month instead of $5-8/month. The key difference: you own the server. No vendor lock-in, no platform-specific configuration files, and your `docker-compose.yml` works identically on your local machine, on Coolify, or on any other Docker host.

### Why Not Just Raw Docker on Hetzner?

You absolutely can run raw `docker compose up -d` on a Hetzner VPS (see section 8 of [08-docker-compose-hosting-alternatives.md](08-docker-compose-hosting-alternatives.md)). Coolify adds value when:

- You want a web UI instead of SSH for routine tasks (check logs, restart, redeploy)
- You want GitHub webhooks for auto-deploy without writing your own CI/CD
- You plan to add more services later (dashboard, monitoring) and want easy management
- You want SSL/HTTPS without manually configuring Nginx and certbot

If you just want the simplest possible setup and are comfortable with SSH, skip Coolify and use raw Docker Compose. Coolify is for when you want convenience.

---

## 2. Hetzner Server Selection

### Recommended: CX22

| Spec | Value |
|------|-------|
| vCPU | 2 (shared, Intel) |
| RAM | 4 GB |
| Disk | 40 GB NVMe SSD |
| Traffic | 20 TB included |
| Price | EUR 4.35/month |
| Architecture | x86_64 |

This is the sweet spot. Coolify uses approximately 500 MB-1 GB RAM at idle. Your Python scanner uses at most 200-500 MB during a scan. That leaves 2.5-3 GB of headroom for the OS, Docker overhead, and a future Streamlit dashboard.

40 GB NVMe is far more than enough: Coolify takes about 2-5 GB (including Docker images for its own services), your scanner image will be 200-500 MB, and the SQLite database is 15 MB.

### Alternative: CX32 (If Adding More Services)

| Spec | Value |
|------|-------|
| vCPU | 4 (shared, Intel) |
| RAM | 8 GB |
| Disk | 80 GB NVMe SSD |
| Traffic | 20 TB included |
| Price | EUR 7.59/month |

Choose this if you plan to run multiple additional services on the same server (e.g., scanner + Streamlit dashboard + Uptime Kuma + maybe a second project). The extra 4 GB RAM gives comfortable headroom.

### Alternative: CAX11 (ARM, Cheapest)

| Spec | Value |
|------|-------|
| vCPU | 2 (Ampere ARM) |
| RAM | 4 GB |
| Disk | 40 GB NVMe SSD |
| Traffic | 20 TB included |
| Price | EUR 3.79/month |

ARM is slightly cheaper (EUR 0.56/month savings). Coolify supports ARM servers. All Python dependencies used by this project (pandas, numpy, yfinance, pandas-ta, requests) have ARM wheels. However:

- Some Docker base images may need `--platform linux/arm64` or ARM-specific tags
- If you build the Docker image locally on an x86 Mac/PC, you need `docker buildx` for cross-platform builds, or build on the server
- Coolify builds images on the server itself, so this is handled automatically

The savings are minimal. **Stick with CX22 (x86) unless you have a specific reason for ARM.**

### Location

- **Helsinki** (hel1) — closest to Stockholm, approximately 450 km. Sub-5ms latency. Best choice for a Sweden-focused project.
- **Falkenstein** (fsn1) — central Germany. Approximately 1200 km from Stockholm. Sub-20ms latency. Still perfectly fine for a daily batch job.
- **Nuremberg** (nbg1) — very close to Falkenstein, similar latency.

**Recommendation: Helsinki.** Latency does not matter for a daily batch job, but if you add a web dashboard, Helsinki gives the snappiest response times for a Swedish user.

### Operating System

**Ubuntu 24.04 LTS.** This is the most widely supported Linux distribution for Docker and Coolify. Coolify's install script is tested primarily on Ubuntu.

### SSH Key Setup

Generate an SSH key on your local machine if you do not already have one:

```bash
# Generate a new SSH key (if you do not have one)
ssh-keygen -t ed25519 -C "swingtrader-hetzner"

# The key pair will be at:
# ~/.ssh/id_ed25519 (private key - never share this)
# ~/.ssh/id_ed25519.pub (public key - upload to Hetzner)

# View your public key (you will paste this into Hetzner)
cat ~/.ssh/id_ed25519.pub
```

### Firewall Rules

Configure either via Hetzner Cloud Console (recommended) or `ufw` on the server:

| Port | Protocol | Purpose | Required |
|------|----------|---------|----------|
| 22 | TCP | SSH access | Yes |
| 80 | TCP | HTTP (Coolify, Let's Encrypt validation) | Yes |
| 443 | TCP | HTTPS (Coolify UI, your services) | Yes |
| 8000 | TCP | Coolify UI (initial setup, before SSL) | Yes (can close after SSL setup) |

In Hetzner Cloud Console, create a firewall and attach it to your server. This is free and applied at the network level (before traffic reaches your server).

---

## 3. Coolify Overview

### What Coolify Is

Coolify is an open-source, self-hosted platform that turns any VPS into a PaaS similar to Railway, Vercel, or Render. You install it on your server, and it provides a web-based management interface for deploying and managing Docker-based applications.

Think of it as: **your own private Railway that runs on a EUR 4.35/month server.**

### Coolify v4 (Current Version)

Coolify v4 is a complete rewrite from v3. It is built with Laravel (PHP) on the backend and uses Docker under the hood to manage all deployments. Key details:

- **Release:** v4 has been the main version since late 2023, actively developed throughout 2024-2025
- **License:** Apache 2.0 (fully open source, free to self-host)
- **Paid option:** Coolify Cloud (hosted version) exists, but self-hosting is free
- **Community:** Active GitHub repository, Discord community, regular updates

### Core Features

**Deployment:**
- Deploy from GitHub, GitLab, Bitbucket, or any Git repository
- Docker Compose deployment (reads your `docker-compose.yml` directly)
- Dockerfile-based builds
- Nixpacks builds (auto-detect language and build — like Railway)
- Static site deployment
- Auto-deploy on push via webhooks

**Infrastructure:**
- Persistent volumes (Docker named volumes)
- Environment variable management in the UI
- Health checks and auto-restart
- Resource limits (CPU, memory) per service
- Multiple servers from a single Coolify dashboard
- Container log viewing in real-time

**Networking:**
- Built-in reverse proxy (Traefik)
- Automatic SSL via Let's Encrypt
- Custom domain mapping per service
- Wildcard SSL certificates
- HTTP to HTTPS redirect

**Operations:**
- Web-based terminal (SSH into containers from the browser)
- Deployment history and rollback
- Notifications (email, Telegram, Discord, Slack)
- API for automation
- S3-compatible backup destinations

### Resource Usage

Coolify itself runs several containers:

| Container | Purpose | RAM Usage |
|-----------|---------|-----------|
| coolify | Main application (Laravel) | ~150-250 MB |
| coolify-db | PostgreSQL database | ~50-100 MB |
| coolify-redis | Redis cache | ~10-30 MB |
| coolify-realtime | WebSocket server | ~30-50 MB |
| traefik | Reverse proxy | ~30-50 MB |
| coolify-sentinel | Monitoring agent | ~20-40 MB |

**Total Coolify overhead: approximately 400-600 MB RAM, 1-2 GB disk.**

On a CX22 with 4 GB RAM, this leaves approximately 3.2-3.5 GB for your applications — more than enough for the scanner, a Streamlit dashboard, and additional services.

### What Coolify Does NOT Do

- **No built-in cron scheduler for containers.** Coolify v4 does not have a native "run this container on a schedule" feature like Railway's cron jobs. You need an external scheduler (system cron or Ofelia). See [Section 6](#6-scheduled-execution).
- **No database management UI.** It can deploy databases (PostgreSQL, MySQL, Redis) but does not provide a phpMyAdmin-like interface.
- **No CI/CD pipelines.** It builds and deploys, but does not run tests. Use GitHub Actions for that.
- **Not a Kubernetes replacement.** It is single-server or multi-server Docker, not an orchestrator.

---

## 4. Complete Hetzner + Coolify Setup

### Step 1: Create Hetzner Server

#### Option A: Hetzner Cloud Console (Web UI)

1. Go to [console.hetzner.cloud](https://console.hetzner.cloud)
2. Sign up or log in
3. Create a new project: click "New Project", name it `SwingTrader`
4. Go to **Security > SSH Keys** and add your public key:
   - Click "Add SSH Key"
   - Paste the contents of `~/.ssh/id_ed25519.pub`
   - Name it (e.g., `macbook`)
5. Go to **Servers > Add Server**:
   - **Location:** Helsinki
   - **Image:** Ubuntu 24.04
   - **Type:** Shared vCPU > CX22 (2 vCPU, 4 GB, 40 GB)
   - **Networking:** Public IPv4 + IPv6 (default)
   - **SSH Keys:** Select the key you added
   - **Firewalls:** Create a new one with rules for ports 22, 80, 443, 8000 (TCP inbound)
   - **Name:** `swingtrader`
6. Click "Create & Buy Now"
7. Note the server's public IPv4 address (shown on the server detail page)

#### Option B: Hetzner CLI (hcloud)

```bash
# Install hcloud CLI
# macOS:
brew install hcloud

# Authenticate
hcloud context create swingtrader
# Enter your Hetzner API token (generate one in Cloud Console > Security > API Tokens)

# Upload your SSH key
hcloud ssh-key create --name macbook --public-key-from-file ~/.ssh/id_ed25519.pub

# Create a firewall
hcloud firewall create --name swingtrader-fw
hcloud firewall add-rule swingtrader-fw --direction in --protocol tcp --port 22 --source-ips 0.0.0.0/0 --source-ips ::/0 --description "SSH"
hcloud firewall add-rule swingtrader-fw --direction in --protocol tcp --port 80 --source-ips 0.0.0.0/0 --source-ips ::/0 --description "HTTP"
hcloud firewall add-rule swingtrader-fw --direction in --protocol tcp --port 443 --source-ips 0.0.0.0/0 --source-ips ::/0 --description "HTTPS"
hcloud firewall add-rule swingtrader-fw --direction in --protocol tcp --port 8000 --source-ips 0.0.0.0/0 --source-ips ::/0 --description "Coolify"

# Create the server
hcloud server create \
  --name swingtrader \
  --type cx22 \
  --image ubuntu-24.04 \
  --location hel1 \
  --ssh-key macbook \
  --firewall swingtrader-fw

# The output will show the server's IP address
hcloud server ip swingtrader
```

### Step 2: Initial Server Setup

```bash
# SSH into the server as root
ssh root@YOUR_SERVER_IP

# Update all packages
apt update && apt upgrade -y

# Set the timezone to Stockholm (important for cron jobs later)
timedatectl set-timezone Europe/Stockholm

# Verify timezone
date
# Should show CET/CEST time

# Install fail2ban for SSH brute-force protection
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Configure UFW firewall (defense in depth, in addition to Hetzner firewall)
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # Coolify initial UI
ufw --force enable

# Verify firewall status
ufw status
```

**Optional but recommended: Create a non-root user**

```bash
# Create a user (Coolify needs root for Docker, but a non-root user is good practice for other tasks)
adduser trader
usermod -aG sudo trader

# Copy SSH key to new user
mkdir -p /home/trader/.ssh
cp ~/.ssh/authorized_keys /home/trader/.ssh/
chown -R trader:trader /home/trader/.ssh
chmod 700 /home/trader/.ssh
chmod 600 /home/trader/.ssh/authorized_keys
```

Note: Coolify's install script must be run as root and it manages Docker itself. You do not need to install Docker manually.

### Step 3: Install Coolify

Coolify provides a one-line install command that sets up everything (Docker, Docker Compose, Traefik, PostgreSQL, the Coolify application itself):

```bash
# Run as root on the server
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

This script will:
1. Install Docker Engine and Docker Compose if not present
2. Pull all Coolify Docker images
3. Start the Coolify stack (app, database, redis, proxy)
4. Print the URL to access the Coolify UI

The installation takes 2-5 minutes depending on network speed.

**After installation:**

```bash
# Verify Coolify is running
docker ps

# You should see containers for:
# - coolify
# - coolify-db (PostgreSQL)
# - coolify-redis
# - coolify-realtime
# - coolify-sentinel
# - traefik
```

### Step 4: Initial Coolify Web UI Setup

1. Open your browser and go to `http://YOUR_SERVER_IP:8000`
2. You will see the Coolify registration page
3. Create your admin account:
   - Email address
   - Password (use a strong password)
4. After logging in, you will see the Coolify dashboard
5. Coolify will detect the local server (the one it is running on) and add it automatically as a "Server" resource

**Important first steps in the UI:**

- Go to **Settings** (gear icon) and configure:
  - Instance name (e.g., "SwingTrader Server")
  - Instance domain (if you have one — otherwise leave blank)
  - FQDN for Coolify itself (if you have a domain, e.g., `coolify.yourdomain.com` — otherwise use `http://YOUR_SERVER_IP:8000`)
- Go to **Notifications** and set up Telegram notifications (you already have a bot token):
  - Navigate to Settings > Notifications > Telegram
  - Enter your bot token and chat ID
  - This lets Coolify notify you of deployment successes/failures

### Step 5: Connect GitHub Repository

Coolify connects to GitHub via a GitHub App (not a personal access token). This gives fine-grained permissions and enables webhooks for auto-deploy.

1. In Coolify, go to **Sources** in the left sidebar
2. Click **Add New Source > GitHub App**
3. Coolify will guide you through creating a GitHub App:
   - Click "Register a GitHub App" — this opens GitHub with pre-filled settings
   - Name the app (e.g., `coolify-swingtrader`)
   - Install it on your GitHub account
   - Select **Only select repositories** and choose your `SwingTrader` repository
   - Authorize and install
4. Back in Coolify, the GitHub source should now show as connected
5. Verify by checking that your `SwingTrader` repo appears when you try to create a new resource

**Alternative: Deploy Key (simpler but no auto-deploy)**

If you do not want the GitHub App integration, you can use a deploy key:
1. In your project settings in Coolify, add a deploy key (SSH key)
2. Add the public key as a deploy key in your GitHub repo (Settings > Deploy Keys)
3. This allows Coolify to pull the repo, but you will need to manually trigger deployments (no webhook auto-deploy)

### Step 6: Configure Docker Compose Deployment

1. In Coolify, go to **Projects** in the left sidebar
2. Click **Add New Project**, name it `SwingTrader`
3. Within the project, click **Add New Resource**
4. Select **Docker Compose**
5. Choose your GitHub source and select the `SwingTrader` repository
6. Branch: `main` (or whatever your default branch is)
7. Coolify will detect the `docker-compose.yml` in the root of your repository

**Configure environment variables:**

1. In the service settings, go to the **Environment Variables** tab
2. Add your secrets:
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `TELEGRAM_CHAT_ID` = your chat ID
   - Any other environment variables your scanner needs
3. Mark sensitive values as "Secret" (they will be masked in the UI)

These environment variables are injected into the container at runtime — they replace the `env_file: .env` directive in docker-compose.yml.

**Configure persistent volume:**

Coolify reads the `volumes` section from your `docker-compose.yml`. Named volumes (like `scanner-data`) are automatically created as Docker named volumes on the host. These persist across container restarts and redeployments.

No additional configuration is needed if your `docker-compose.yml` already defines named volumes (see [Section 5](#5-docker-composeyml-for-coolify)).

**Build settings:**

1. In the service settings, check:
   - **Build Path:** `.` (root of repo, where the Dockerfile lives)
   - **Dockerfile:** `Dockerfile` (or your custom name)
2. Coolify will build the Docker image on the server when you deploy

### Step 7: Deploy

1. In the Coolify project view, click **Deploy** on your service
2. Coolify will:
   - Pull the latest code from GitHub
   - Build the Docker image using your Dockerfile
   - Create/update named volumes
   - Start the container(s) defined in docker-compose.yml
   - Inject environment variables
3. Watch the build log in real-time in the Coolify UI
4. Once deployed, check the **Logs** tab to see your container output
5. The container status will show as "Running" (green) in the dashboard

**Testing the first run:**

After deployment, the scanner container will start. Depending on your Dockerfile's CMD, it may:
- Run the scan once and exit (if CMD is `python src/main.py`)
- Stay running waiting for a scheduler trigger

For initial testing, you can use Coolify's **Execute Command** feature (web terminal) to run a command inside the container, or check the logs to verify the first scan completed.

**Auto-deploy on push:**

With the GitHub App connected, every push to `main` will automatically trigger a new deployment. Coolify receives the webhook from GitHub, pulls the new code, rebuilds the image, and redeploys. You can see the deployment history in the Coolify UI.

---

## 5. docker-compose.yml for Coolify

This `docker-compose.yml` works with Coolify and also locally with `docker compose up`:

```yaml
services:
  scanner:
    build: .
    container_name: swingtrader-scanner
    env_file: .env
    volumes:
      - scanner-data:/app/data
    restart: "no"
    # The scanner runs once and exits.
    # Scheduling is handled externally (cron or Ofelia).
    # For local development: docker compose run scanner

volumes:
  scanner-data:
    # Named volume — persists across container restarts and redeployments.
    # On the host, Docker stores this at /var/lib/docker/volumes/scanner-data/_data
```

**Key design decisions:**

- **`env_file: .env`** — Used for local development. On Coolify, environment variables set in the UI override or supplement this. You can keep a `.env.example` in the repo and have the real `.env` in `.gitignore`.
- **`restart: "no"`** — The scanner runs once and exits. We do not want Docker to restart it endlessly. The scheduler triggers the next run.
- **Named volume `scanner-data`** — This is critical. A named volume persists independently of the container. When Coolify rebuilds and redeploys your container, the volume is preserved. Bind mounts (`./data:/app/data`) also work but named volumes are more portable and Coolify handles them natively.
- **No `ports` on scanner** — The scanner does not need inbound network access. It only makes outbound HTTPS calls (yfinance, Telegram API).

**Corresponding Dockerfile:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY config/ config/

# Create data directory (volume mount point)
RUN mkdir -p /app/data

# Default command: run the scanner
CMD ["python", "src/main.py"]
```

**Local development without Docker:**

The project still works without Docker:

```bash
# Local development (no Docker needed)
cd SwingTrader
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

The key is that `src/main.py` reads the data directory from config or uses a relative path (`data/`). Whether that `data/` directory is a Docker volume or a local folder, the code does not care.

---

## 6. Scheduled Execution

The SwingTrader scanner needs to run daily after Stockholm market close at 18:15 CET (Monday through Friday). There are three options for scheduling.

### Option A: Coolify's Built-in Scheduler

**Status: Coolify v4 does NOT have a built-in cron scheduler for running containers on a schedule.**

Coolify can restart services, auto-deploy on push, and manage running containers, but it does not have a "run this container at this time" cron feature like Railway offers. This is a known feature request in the Coolify community.

Coolify's scheduled tasks feature (if present in newer versions) is limited to internal maintenance tasks, not arbitrary container execution.

**Verdict: Not an option. Use Option B or C.**

### Option B: System Cron on the Hetzner Server (Recommended)

The simplest and most reliable approach. The server's crontab triggers `docker compose run` on a schedule.

```bash
# SSH into the server
ssh root@YOUR_SERVER_IP

# Set the server timezone (if not already done in Step 2)
timedatectl set-timezone Europe/Stockholm

# Edit the root crontab
crontab -e

# Add the following line:
# Run SwingTrader scanner at 18:15 CET, Monday-Friday
# Because the server timezone is Europe/Stockholm, cron uses CET/CEST automatically
15 18 * * 1-5 cd /opt/swingtrader && docker compose run --rm scanner >> /var/log/swingtrader-cron.log 2>&1
```

**Explanation:**
- `15 18 * * 1-5` — 18:15, Monday (1) through Friday (5)
- `cd /opt/swingtrader` — The directory where Coolify checks out your docker-compose project. The actual path depends on Coolify's configuration. Alternatively, you can use `docker compose -f /path/to/docker-compose.yml run --rm scanner`
- `docker compose run --rm scanner` — Creates a new container from the `scanner` service, runs it, and removes it after completion. The `--rm` flag cleans up the container but preserves the named volume.
- `>> /var/log/swingtrader-cron.log 2>&1` — Logs output for debugging

**Finding the Coolify project path:**

When Coolify deploys a Docker Compose project, it stores the configuration in its own directory structure. To find where your project lives:

```bash
# Find the docker-compose file Coolify is using
find /data/coolify -name "docker-compose.yml" 2>/dev/null

# Or check running containers to find the project directory
docker inspect swingtrader-scanner | grep -i "com.docker.compose.project.working_dir"
```

Typically, Coolify stores projects under `/data/coolify/applications/<uuid>/` or similar.

**Alternative: Use docker directly instead of compose:**

```bash
# If you know the image name that Coolify builds
15 18 * * 1-5 docker run --rm --env-file /data/coolify/apps/swingtrader/.env -v scanner-data:/app/data swingtrader-scanner >> /var/log/swingtrader-cron.log 2>&1
```

**Why this is the recommended option:**
- Dead simple, zero dependencies beyond cron (which is always installed)
- Server timezone handles CET/CEST transitions automatically
- Logs are captured for debugging
- Works regardless of whether Coolify is running
- Cron has been reliable on Linux for 50 years

### Option C: Ofelia (Docker-Based Cron)

Ofelia is a Docker job scheduler. It runs as a container alongside your services and triggers other containers on a cron schedule. This keeps everything in Docker — no host crontab needed.

```yaml
services:
  scanner:
    build: .
    container_name: swingtrader-scanner
    env_file: .env
    volumes:
      - scanner-data:/app/data
    restart: "no"
    labels:
      - "ofelia.enabled=true"
      - "ofelia.job-run.scanner.schedule=0 15 18 * * 1-5"
      - "ofelia.job-run.scanner.container=swingtrader-scanner"

  ofelia:
    image: mcuadros/ofelia:latest
    container_name: swingtrader-scheduler
    depends_on:
      - scanner
    command: daemon --docker
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - TZ=Europe/Stockholm

volumes:
  scanner-data:
```

**Ofelia schedule format:** `seconds minutes hours day-of-month month day-of-week`

Note the leading `0` for seconds — Ofelia uses a 6-field cron format, not the standard 5-field format.

**Key details:**
- `ofelia.job-run.scanner.schedule=0 15 18 * * 1-5` — Run at 18:15:00, Mon-Fri
- `ofelia.job-run.scanner.container=swingtrader-scanner` — The container to start
- `TZ=Europe/Stockholm` — Ofelia container uses Stockholm timezone
- Docker socket mount (`/var/run/docker.sock`) allows Ofelia to start/stop other containers
- Ofelia itself uses approximately 10-20 MB RAM

**Pros:**
- Fully containerized — the entire stack is defined in docker-compose.yml
- No host-level configuration needed
- Schedule is version-controlled with your code
- Deploys via Coolify like any other service

**Cons:**
- Extra container running 24/7 (minimal resource usage, but still)
- Docker socket mount is a security consideration (Ofelia can control any container on the host)
- Slightly more complex than a one-line crontab entry
- If Ofelia crashes, scans do not run

### Recommendation

**Use Option B (system cron) for simplicity.** It is one line in crontab, zero dependencies, and rock solid. You are already managing the server (since you are running Coolify), so adding a crontab entry is trivial.

**Use Option C (Ofelia) if** you want everything defined in `docker-compose.yml` and version-controlled. This is more "infrastructure as code" but adds a dependency.

Either option works well. For a personal project, system cron is the pragmatic choice.

---

## 7. Persistent Storage

### How Docker Named Volumes Work

When your `docker-compose.yml` defines:

```yaml
volumes:
  scanner-data:
```

And your service mounts it:

```yaml
services:
  scanner:
    volumes:
      - scanner-data:/app/data
```

Docker creates a named volume on the host at `/var/lib/docker/volumes/scanner-data/_data/`. This directory:

- **Persists across container restarts** — stopping and starting the scanner does not delete the data
- **Persists across container rebuilds** — when Coolify deploys a new version of your image, the volume is reattached to the new container
- **Persists across `docker compose down`** — the volume is only deleted if you explicitly run `docker volume rm scanner-data`
- **Is NOT deleted by Coolify redeployments** — Coolify preserves named volumes when updating services

### SQLite File Location

Inside the container: `/app/data/swingtrader.db`
On the host: `/var/lib/docker/volumes/scanner-data/_data/swingtrader.db`

Your Python code should use a configurable data directory:

```python
import os

DATA_DIR = os.environ.get("DATA_DIR", "data")
DB_PATH = os.path.join(DATA_DIR, "swingtrader.db")
```

This way:
- In Docker: `DATA_DIR` defaults to `data`, which maps to `/app/data` (the volume mount)
- Locally: `DATA_DIR` defaults to `data`, which is `./data/` relative to the project root

### Backup Strategy

#### Option 1: Cron Job Copying SQLite

```bash
# Add to root crontab on the server
# Runs at 19:00 daily (after the scanner finishes at ~18:20)
0 19 * * 1-5 cp /var/lib/docker/volumes/scanner-data/_data/swingtrader.db /root/backups/swingtrader-$(date +\%Y\%m\%d).db

# Clean up backups older than 30 days
5 19 * * 1-5 find /root/backups -name "swingtrader-*.db" -mtime +30 -delete
```

Create the backup directory first:

```bash
mkdir -p /root/backups
```

#### Option 2: Hetzner Snapshots

Hetzner can snapshot the entire server (all data, all Docker volumes, everything):

- **Automatic backups:** EUR 0.87/month (20% of CX22 price). Hetzner keeps the last 7 daily backups automatically.
- **Manual snapshots:** EUR 0.012/GB/month. A 40 GB server snapshot costs approximately EUR 0.48/month.

To enable automatic backups:
1. Go to Hetzner Cloud Console > Servers > swingtrader > Backups
2. Enable "Backups" — adds EUR 0.87/month to your bill
3. Hetzner automatically takes daily snapshots and retains the last 7

For a personal project, the cron-based SQLite copy (Option 1) is sufficient. Hetzner automatic backups are worth the EUR 0.87/month for peace of mind — they protect against everything (accidental deletion, server corruption, botched updates).

#### Option 3: Off-Server Backup

For extra safety, copy the SQLite file off the server entirely:

```bash
# Run from your local machine (not the server)
# Pulls the SQLite file to your local backups directory
scp root@YOUR_SERVER_IP:/var/lib/docker/volumes/scanner-data/_data/swingtrader.db ~/backups/swingtrader-$(date +%Y%m%d).db
```

Or automate this with a local cron job or a scheduled task on your Mac.

---

## 8. Adding the Dashboard (Streamlit)

When you are ready to add a web dashboard (Phase 3 of the project), add a second service to `docker-compose.yml`:

### Updated docker-compose.yml

```yaml
services:
  scanner:
    build: .
    container_name: swingtrader-scanner
    env_file: .env
    volumes:
      - scanner-data:/app/data
    restart: "no"

  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    container_name: swingtrader-dashboard
    ports:
      - "8501:8501"
    volumes:
      - scanner-data:/app/data:ro
    environment:
      - DATA_DIR=/app/data
    restart: unless-stopped
    depends_on:
      - scanner

volumes:
  scanner-data:
```

### Dockerfile.dashboard

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install Streamlit and dependencies
COPY requirements-dashboard.txt .
RUN pip install --no-cache-dir -r requirements-dashboard.txt

# Copy dashboard code
COPY src/dashboard/ src/dashboard/

# Streamlit config
EXPOSE 8501

CMD ["streamlit", "run", "src/dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

### Key Details

- **Read-only volume mount (`scanner-data:/app/data:ro`)** — The dashboard can read the SQLite database but cannot modify it. This prevents any accidental writes from the dashboard corrupting the scanner's data.
- **Separate Dockerfile** — The dashboard has different dependencies (Streamlit, plotly, etc.) than the scanner. Separate Dockerfiles keep images lean.
- **`restart: unless-stopped`** — The dashboard should always be running (unlike the scanner which runs once and exits).
- **Port 8501** — Streamlit's default port. Coolify's Traefik reverse proxy will route traffic from your domain to this port.

### Coolify Configuration for the Dashboard

After pushing the updated `docker-compose.yml`:

1. Coolify will detect the new `dashboard` service automatically
2. In the Coolify UI, go to the service settings for `dashboard`
3. Under **Domains**, add:
   - `swingtrader.yourdomain.com` (if you have a domain)
   - Or leave empty to access via `http://YOUR_SERVER_IP:8501`
4. Coolify's Traefik proxy will:
   - Route HTTPS traffic for your domain to port 8501
   - Handle SSL certificate via Let's Encrypt
   - Redirect HTTP to HTTPS

### SQLite Concurrency Note

SQLite supports concurrent reads but only one writer at a time. With this setup:
- The scanner writes to the database (once daily, for 1-5 minutes)
- The dashboard reads from the database (continuously, read-only mount)

This is perfectly safe. The `:ro` mount on the dashboard prevents accidental writes. During the brief window when the scanner is writing, the dashboard reads may occasionally see a brief WAL checkpoint delay, but this is imperceptible for a human viewing a web page.

---

## 9. SSL and Domain Setup

### Option A: Custom Domain with SSL (Recommended If You Have a Domain)

If you own a domain (e.g., `yourdomain.com`), you can set up:
- `coolify.yourdomain.com` — Coolify management UI
- `swingtrader.yourdomain.com` — Streamlit dashboard (when ready)

**Step 1: DNS Configuration**

At your domain registrar (Namecheap, Cloudflare, etc.), add A records:

```
Type: A
Name: coolify
Value: YOUR_SERVER_IP
TTL: 3600

Type: A
Name: swingtrader
Value: YOUR_SERVER_IP
TTL: 3600
```

**Step 2: Configure Coolify's Own Domain**

1. In Coolify UI, go to **Settings > General**
2. Set **Instance's Domain** to `https://coolify.yourdomain.com`
3. Coolify will automatically:
   - Configure Traefik to route `coolify.yourdomain.com` to the Coolify UI
   - Request a Let's Encrypt SSL certificate
   - Redirect HTTP to HTTPS
4. After a minute, access Coolify at `https://coolify.yourdomain.com`

**Step 3: Configure Dashboard Domain (When Ready)**

1. In Coolify UI, go to your SwingTrader project > dashboard service
2. Under **Domains**, enter `https://swingtrader.yourdomain.com`
3. Coolify handles SSL automatically

**Step 4: Close Port 8000**

Once Coolify is accessible via HTTPS on your domain, you can remove the port 8000 firewall rule:

```bash
# On the server
ufw delete allow 8000/tcp

# Also remove from Hetzner firewall in the Cloud Console
```

### Option B: IP Address Only (No Domain, No SSL)

For a personal tool with no public users, you can skip the domain entirely:

- Coolify UI: `http://YOUR_SERVER_IP:8000`
- Dashboard (later): `http://YOUR_SERVER_IP:8501`

**Security note:** Without SSL, your Coolify login credentials are sent in plain text. This is acceptable on a personal network or with SSH tunneling, but not recommended if accessing from public WiFi.

**SSH tunnel alternative (secure, no domain needed):**

```bash
# From your local machine, create an SSH tunnel
ssh -L 8000:localhost:8000 -L 8501:localhost:8501 root@YOUR_SERVER_IP

# Then access in your browser:
# Coolify: http://localhost:8000
# Dashboard: http://localhost:8501
```

This is secure (traffic is encrypted through SSH) and requires no domain or SSL certificate.

### Option C: Cloudflare Tunnel (Free, No Open Ports)

If you use Cloudflare for DNS, you can use Cloudflare Tunnel to expose Coolify and the dashboard without opening any ports on the server:

1. Install `cloudflared` on the server
2. Create a tunnel that routes `coolify.yourdomain.com` to `localhost:8000`
3. All traffic goes through Cloudflare's network, encrypted
4. No need to open ports 80, 443, or 8000 on the firewall

This is the most secure option but adds Cloudflare as a dependency.

---

## 10. Monitoring and Maintenance

### Coolify Dashboard

Coolify provides built-in monitoring for your deployed services:

- **Service Status:** Green (running), red (stopped/crashed), yellow (deploying)
- **Container Logs:** Real-time log streaming in the browser. Click on any service > Logs tab
- **Deployment History:** See all past deployments, their status, and build logs. Roll back to a previous deployment if needed
- **Resource Usage:** Basic CPU and memory stats per container (via Coolify's sentinel agent)

### Server Monitoring via Hetzner

Hetzner Cloud Console provides server-level metrics:

- **CPU Usage:** Graph showing utilization over time
- **Disk I/O:** Read/write throughput
- **Network Traffic:** Inbound/outbound bandwidth
- Access via: Cloud Console > Servers > swingtrader > Metrics

These are sufficient for a personal project. You will see daily CPU spikes when the scanner runs, and minimal usage the rest of the time.

### Optional: Uptime Kuma (Self-Hosted Monitoring)

If you want uptime monitoring and alerts, deploy Uptime Kuma on the same server via Coolify:

1. In Coolify, add a new resource
2. Choose **Docker Image** deployment
3. Image: `louislam/uptime-kuma:latest`
4. Port: 3001
5. Add a persistent volume for `/app/data`
6. Deploy

Uptime Kuma can then monitor:
- Your Streamlit dashboard (HTTP check)
- The scanner (check if the SQLite database was modified today)
- External services (Telegram API, yfinance)
- Send alerts via Telegram

Resource usage: approximately 50-100 MB RAM. Fits easily on the CX22 alongside Coolify and SwingTrader.

### Server Updates

**Coolify updates:**

Coolify has a built-in update mechanism:

```bash
# SSH into the server
# Coolify update (checks for latest version and updates all Coolify containers)
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

Or update from the Coolify UI: Settings > Update (if available in your version).

**Operating system updates:**

```bash
# Manual update
apt update && apt upgrade -y

# Automatic security updates (recommended)
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
# Select "Yes" to enable automatic security updates
```

Unattended upgrades will install security patches automatically without rebooting. Kernel updates may require a manual reboot, but this is infrequent (once every few months).

**Docker image updates (your application):**

1. Push code changes to GitHub
2. Coolify auto-deploys (if GitHub App webhook is configured)
3. Or manually click "Deploy" in Coolify UI

No SSH required for routine application updates.

### Backup Schedule

| What | How | Frequency | Cost |
|------|-----|-----------|------|
| SQLite database | Cron copy to `/root/backups/` | Daily (19:00) | Free |
| Entire server | Hetzner automatic backups | Daily (7 retained) | EUR 0.87/month |
| SQLite off-server | SCP to local machine | Weekly (manual or scripted) | Free |
| Server snapshot | Hetzner manual snapshot | Before major changes | EUR 0.012/GB/month |

---

## 11. Cost Breakdown

### Minimum Setup (Scanner Only)

| Item | Monthly Cost |
|------|-------------|
| Hetzner CX22 (2 vCPU, 4 GB, 40 GB) | EUR 4.35 |
| Coolify | Free (open source) |
| Docker | Free |
| **Total** | **EUR 4.35** |

### Recommended Setup (Scanner + Backups)

| Item | Monthly Cost |
|------|-------------|
| Hetzner CX22 | EUR 4.35 |
| Coolify | Free |
| Hetzner automatic backups | EUR 0.87 |
| **Total** | **EUR 5.22** |

### Full Setup (Scanner + Dashboard + Domain + Backups)

| Item | Monthly Cost |
|------|-------------|
| Hetzner CX22 | EUR 4.35 |
| Coolify | Free |
| Hetzner automatic backups | EUR 0.87 |
| Domain (e.g., .com from Namecheap) | ~EUR 1-2 (amortized from ~EUR 12-20/year) |
| SSL (Let's Encrypt via Coolify) | Free |
| **Total** | **EUR 6-7** |

### Comparison to Alternatives

| Platform | Monthly Cost | Notes |
|----------|-------------|-------|
| **Hetzner + Coolify** | **EUR 4.35-7** | Self-managed, full control |
| Azure Container Apps | ~EUR 5-10 | Managed, more complex setup |
| Railway | ~$5-8 (EUR 5-7) | Fully managed, zero ops |
| Render | ~$7+ (EUR 6+) | Cron job pricing tier |
| DigitalOcean App Platform | ~$5-12 | Managed, US-centric |
| Running locally | EUR 0 | Must leave computer on, unreliable |

The Hetzner + Coolify setup matches Railway's cost while giving you full server access, EU datacenter, and no platform lock-in.

---

## 12. Troubleshooting

### Coolify Not Deploying

**Symptom:** Deployment stuck or failing in Coolify UI.

**Check:**
1. Click on the deployment in Coolify and read the build log
2. Common issues:
   - **Dockerfile syntax error** — Fix the Dockerfile, push, and redeploy
   - **pip install failing** — Missing system dependency. Add `apt-get install` to Dockerfile
   - **Out of disk space** — Check with `df -h`. Prune old Docker images: `docker system prune -a`
   - **Out of memory during build** — CX22 has 4 GB, large `pip install` can exhaust this. Add `--no-cache-dir` to pip install

```bash
# Check disk space
df -h

# Check memory
free -h

# Prune unused Docker images and containers
docker system prune -a
# WARNING: This removes all unused images. Coolify will rebuild on next deploy.
```

### Scanner Not Running on Schedule

**Symptom:** No scan results at 18:15, no Telegram notification.

**Check:**
1. Verify cron is running:
   ```bash
   systemctl status cron
   ```
2. Check cron logs:
   ```bash
   grep CRON /var/log/syslog | tail -20
   ```
3. Check your scanner log:
   ```bash
   cat /var/log/swingtrader-cron.log
   ```
4. Verify timezone:
   ```bash
   date
   timedatectl
   ```
5. Test manual run:
   ```bash
   docker compose -f /path/to/docker-compose.yml run --rm scanner
   ```

### SQLite Database Locked

**Symptom:** `sqlite3.OperationalError: database is locked`

**Cause:** Two processes trying to write to SQLite simultaneously.

**Fix:**
- Ensure only one scanner instance runs at a time. The cron job should use `docker compose run` (creates a new container) not `docker compose up` (which may conflict with a running container).
- Add a flock wrapper to the cron job to prevent overlapping runs:
  ```bash
  15 18 * * 1-5 flock -n /tmp/swingtrader.lock docker compose -f /path/to/docker-compose.yml run --rm scanner >> /var/log/swingtrader-cron.log 2>&1
  ```
  `flock -n` will skip the run if the previous one is still running.
- If using Ofelia, it will not start a new container if the previous one is still running (by default).

### Coolify Using Too Much RAM

**Symptom:** Server running slow, OOM kills, Coolify UI unresponsive.

**Check:**
```bash
# See memory usage by container
docker stats --no-stream

# Check system memory
free -h
```

**Fix:**
- Coolify should use 400-600 MB. If significantly more, restart it:
  ```bash
  cd /data/coolify/source
  docker compose down
  docker compose up -d
  ```
- If total RAM usage exceeds 3.5 GB consistently, consider upgrading to CX32 (8 GB RAM, EUR 7.59/month)
- Reduce Coolify's PostgreSQL memory: edit `/data/coolify/source/docker-compose.yml` and add memory limits

### GitHub Webhook Not Firing (No Auto-Deploy)

**Symptom:** You push to GitHub but Coolify does not start a new deployment.

**Check:**
1. In GitHub: go to your repo > Settings > Webhooks. Check if the Coolify webhook is listed and if recent deliveries show green checkmarks or red X marks.
2. If deliveries fail with connection errors: verify ports 80/443 are open on the Hetzner firewall.
3. In Coolify: go to Sources > your GitHub App. Check if it shows as connected.
4. Re-register the webhook: in Coolify, disconnect and reconnect the GitHub source.

### SSL Certificate Issues

**Symptom:** Browser shows "Not Secure" or certificate error for your domain.

**Check:**
1. Verify DNS: `dig swingtrader.yourdomain.com` should return your server IP
2. Verify ports 80 and 443 are open (Let's Encrypt needs port 80 for HTTP-01 challenge)
3. Check Traefik logs:
   ```bash
   docker logs traefik 2>&1 | tail -50
   ```
4. Force certificate renewal in Coolify: go to the service settings, remove and re-add the domain.

### Coolify UI Not Accessible

**Symptom:** Cannot reach `http://YOUR_SERVER_IP:8000`

**Check:**
1. SSH into the server (if SSH works, the server is up)
2. Check if Coolify containers are running:
   ```bash
   docker ps | grep coolify
   ```
3. Restart Coolify:
   ```bash
   cd /data/coolify/source
   docker compose up -d
   ```
4. Check port 8000 is open:
   ```bash
   ufw status
   # Should show 8000/tcp ALLOW
   ```

---

## 13. Migration Path

### From Local Development to Hetzner + Coolify

1. Ensure your project has a `Dockerfile` and `docker-compose.yml` in the repo
2. Push to GitHub
3. Set up Hetzner + Coolify (follow [Section 4](#4-complete-hetzner--coolify-setup))
4. Connect GitHub repo in Coolify
5. Add environment variables in Coolify UI
6. Deploy

Total migration time: approximately 30-60 minutes for initial setup, then auto-deploy on every push.

### From Hetzner + Coolify to Azure

If you later need Azure-specific features (Azure AD integration, compliance, corporate environment):

1. Your `Dockerfile` and `docker-compose.yml` work identically on Azure
2. Options on Azure:
   - **Azure Container Apps:** Deploy the same Docker image, configure scheduled execution
   - **Azure Container Instances:** Run the container on a schedule via Logic Apps
   - **Azure VM:** Same as Hetzner — install Docker, run compose
3. SQLite database: download from Hetzner, upload to Azure persistent volume
4. See [07-azure-hosting.md](07-azure-hosting.md) for Azure-specific details

### From Hetzner + Coolify to Railway/Render

If you want fully managed and are willing to pay more:

1. Push the same repo to Railway/Render
2. Both can build from a Dockerfile
3. Configure environment variables in their UI
4. Railway supports cron scheduling natively
5. SQLite: Railway supports persistent volumes; Render charges for persistent disks

### Key Principle

The `Dockerfile` and `docker-compose.yml` are the portable interface. They work the same on:
- Your local machine (`docker compose up`)
- Hetzner with Coolify
- Hetzner with raw Docker
- Azure Container Apps
- Railway
- Any Docker host

You are never locked in. The only Coolify-specific configuration (environment variables, domains, volumes) is trivially recreatable on any other platform.

---

## Summary

Hetzner CX22 (EUR 4.35/month) + Coolify v4 (free) gives you a self-hosted PaaS with a web UI, GitHub auto-deploy, persistent volumes, and SSL — everything Railway offers, at a fraction of the cost, in an EU datacenter close to Sweden.

**Setup takes about 30-60 minutes:**
1. Create Hetzner server (5 min)
2. Basic security setup (10 min)
3. Install Coolify (5 min)
4. Connect GitHub and configure deployment (15 min)
5. Set up cron scheduling (5 min)

**After setup, the daily workflow is:**
- Push code to GitHub
- Coolify auto-deploys
- Cron runs the scanner at 18:15 CET
- Telegram sends you the results
- Coolify UI shows logs and status if you want to check

No SSH needed for routine operations. The Coolify web UI handles everything.
