# 08 - Docker Compose Hosting Alternatives

> Research date: 2026-03-08
> Goal: Find the cheapest ways to run a Docker Compose-based Python swing trading scanner, beyond Azure. Practical comparison of VPS, container platforms, and serverless options.

---

## Table of Contents

1. [Context and Workload](#1-context-and-workload)
2. [VPS Providers (Full Docker Compose Support)](#2-vps-providers-full-docker-compose-support)
3. [Container Platforms (Docker-native, No VM Management)](#3-container-platforms-docker-native-no-vm-management)
4. [Self-Hosted PaaS on a VPS](#4-self-hosted-paas-on-a-vps)
5. [Serverless Container Options](#5-serverless-container-options)
6. [Comparison Table](#6-comparison-table)
7. [Recommendation](#7-recommendation)
8. [Quick Setup: Hetzner + Docker Compose](#8-quick-setup-hetzner--docker-compose)

---

## 1. Context and Workload

This is a personal swing trading scanner with a very simple workload:

- **Daily Python job** running after Stockholm market close (~18:00 CET), takes 1-5 minutes
- **SQLite database** ~15 MB, needs persistent storage between runs
- **Telegram notifications** — outbound HTTPS only, no inbound ports needed
- **Single user, personal tool** — no scaling, no multi-tenancy
- **Possible future addition:** simple web dashboard (Streamlit or FastAPI)
- **Docker Compose** with 1-2 services to start (scanner + optional dashboard)

Key insight: this workload is tiny. Most of the time the server sits idle. The ideal hosting is either very cheap always-on (VPS) or truly pay-per-use (serverless). The SQLite requirement pushes toward solutions with persistent local disk.

---

## 2. VPS Providers (Full Docker Compose Support)

A VPS gives you a Linux server with root access. You install Docker and Docker Compose yourself, clone your repo, and run `docker-compose up -d`. This is the most flexible option — docker-compose works exactly like on your local machine.

### Hetzner Cloud (Germany/Finland)

The go-to recommendation for EU developers on a budget. Best price/performance ratio in Europe.

| Plan | vCPU | RAM | Disk | Price |
|------|------|-----|------|-------|
| CX22 | 2 | 4 GB | 40 GB SSD | €4.35/month |
| CX32 | 4 | 8 GB | 80 GB SSD | €7.59/month |
| CAX11 (ARM) | 2 | 4 GB | 40 GB SSD | €3.89/month |

**Key details:**
- Datacenters in Falkenstein, Nuremberg (Germany) and Helsinki (Finland) — all close to Sweden
- Helsinki is ~1 ms from Stockholm (not that latency matters for a daily batch job)
- CX22 is massive overkill for this workload, but it is the cheapest x86 option
- CAX11 (ARM/Ampere) is even cheaper at €3.89/month — Docker works fine on ARM, but some Python packages may need ARM-compatible builds (pandas, numpy all support ARM)
- Excellent reputation in the EU developer community
- Hetzner Cloud Console is clean and simple
- Snapshots for backups: €0.012/GB/month (a 40 GB snapshot = ~€0.48/month)
- Firewalls are free
- No hidden costs for bandwidth (20 TB included)

**Why it stands out:** Cheapest reliable VPS in the EU with datacenters close to Sweden. The CX22 at €4.35/month is the benchmark everything else gets compared against.

### Oracle Cloud Free Tier

The only option that is genuinely free forever (if you can get an instance).

| Plan | vCPU | RAM | Disk | Price |
|------|------|-----|------|-------|
| VM.Standard.E2.1.Micro (x86) | 1 | 1 GB | 50 GB | Always Free |
| Ampere A1 (ARM) | up to 4 | up to 24 GB | 200 GB | Always Free |

**Key details:**
- The ARM Ampere A1 is absurdly generous: 4 OCPU + 24 GB RAM for free
- EU datacenters available: Amsterdam, Frankfurt
- Full root access, install Docker like any VPS
- **The catch:** ARM instances are frequently "out of capacity" — you may need to try repeatedly for days/weeks to get one. x86 micro instances are easier to get
- **The other catch:** Oracle may reclaim idle free-tier accounts. Reports vary, but if you have a running VM with periodic activity (daily cron job), you should be fine
- **The third catch:** Oracle Cloud Console UI is notoriously confusing compared to Hetzner

**Why it stands out:** If you get an instance, you cannot beat free. The 4 OCPU + 24 GB ARM instance is more powerful than most $20/month VPS plans elsewhere.

### Scaleway (France)

French cloud provider with some of the cheapest VPS options in Europe.

| Plan | vCPU | RAM | Disk | Price |
|------|------|-----|------|-------|
| Stardust | 1 | 1 GB | 10 GB | €0.36/month |
| DEV1-S | 2 | 2 GB | 20 GB | €2.99/month |
| DEV1-M | 3 | 4 GB | 40 GB | €5.99/month |

**Key details:**
- Stardust at €0.36/month is insanely cheap, but availability is very limited (often sold out). Think of it as a lottery
- DEV1-S at €2.99/month is genuinely available and cheaper than Hetzner CX22
- Datacenters in Paris and Amsterdam
- Good API and CLI tools
- Less community buzz than Hetzner, but technically solid

**Why it stands out:** DEV1-S at €2.99/month is the cheapest reliably available VPS with decent specs.

### Contabo (Germany)

Known for aggressive pricing. You get a lot of specs for very little money.

| Plan | vCPU | RAM | Disk | Price |
|------|------|-----|------|-------|
| VPS S | 4 | 8 GB | 200 GB SSD | €5.99/month |
| VPS M | 6 | 16 GB | 400 GB SSD | €9.99/month |

**Key details:**
- Specs look amazing for the price
- EU datacenters (Nuremberg, Munich, Dusseldorf)
- **The catch:** performance can be inconsistent. CPU is often shared aggressively. I/O can be slow during peak times
- Setup fees on some plans (check current pricing)
- Customer support is basic
- Fine for a daily batch job that does not need consistent performance

**Why it stands out:** Most raw specs per euro. Good if you need disk space or RAM for cheap.

### Vultr

US-based cloud with global presence including a Stockholm datacenter.

| Plan | vCPU | RAM | Disk | Price |
|------|------|-----|------|-------|
| Cloud Compute (Regular) | 1 | 1 GB | 25 GB SSD | $5/month |
| Cloud Compute (Regular) | 1 | 2 GB | 50 GB SSD | $10/month |

**Key details:**
- **Stockholm datacenter** — the only major provider with a Sweden location
- Clean, modern UI
- Good API
- Hourly billing (can delete and recreate without penalty)
- Docker marketplace image available (pre-installed)
- $5/month is more expensive than Hetzner/Scaleway for similar specs

**Why it stands out:** Stockholm datacenter. If you want the absolute lowest latency to Swedish market data providers, this is the one. (Though for a daily batch job, this does not matter.)

### DigitalOcean

The VPS that everyone learns on. Known for excellent documentation.

| Plan | vCPU | RAM | Disk | Price |
|------|------|-----|------|-------|
| Basic Droplet | 1 | 1 GB | 25 GB SSD | $6/month |
| Basic Droplet | 1 | 2 GB | 50 GB SSD | $12/month |

**Key details:**
- Amsterdam datacenter (AMS3)
- 1-Click Docker marketplace app (pre-configured)
- Best documentation of any cloud provider (excellent tutorials)
- $200 free credit for new accounts (60-day trial)
- Slightly more expensive than competitors for equivalent specs
- Also has App Platform (managed containers) but that starts at $5/month per service + usage

**Why it stands out:** Best docs, easiest onboarding. Good if you value simplicity over saving €1-2/month.

### Linode (Akamai Cloud)

Reliable, long-running provider now owned by Akamai.

| Plan | vCPU | RAM | Disk | Price |
|------|------|-----|------|-------|
| Nanode | 1 | 1 GB | 25 GB SSD | $5/month |
| Linode 2GB | 1 | 2 GB | 50 GB SSD | $10/month |

**Key details:**
- No EU datacenter close to Sweden (London is the nearest)
- Good reputation for reliability and support
- Similar pricing to Vultr/DigitalOcean
- Less interesting now that Hetzner and Scaleway are cheaper

---

## 3. Container Platforms (Docker-native, No VM Management)

These platforms let you deploy Docker containers without managing a Linux server. You push code or a Docker image, and they handle the infrastructure.

### Railway.app

Modern developer platform. Closest to "push to GitHub, it deploys."

**Pricing:** Hobby plan $5/month (includes $5 of usage credits). Typical total cost for this workload: $5-8/month.

**Key details:**
- Deploy from GitHub repo with a Dockerfile — it builds and runs automatically
- Supports docker-compose-like multi-service setups via `railway.toml` or the UI
- **Persistent volumes** supported — SQLite works
- **Built-in cron jobs** — schedule your scanner without extra configuration
- Automatic HTTPS for web services (useful if you add a dashboard later)
- Logs, metrics, and deploy previews in the web UI
- **US-only datacenters** — but for a daily batch job that calls yfinance and sends a Telegram message, latency to the datacenter is irrelevant
- Environment variables managed in the UI (good for API keys, Telegram tokens)

**Why it stands out:** The easiest deploy experience. If you do not want to SSH into a server or think about Docker installation, this is the most frictionless option.

### Fly.io

Run Docker containers on lightweight VMs (Firecracker) globally.

**Pricing:** Free tier includes 3 shared-cpu-1x VMs with 256 MB RAM. This workload: ~$3-5/month (or free if you stay within limits).

**Key details:**
- Deploy with a Dockerfile — Fly builds and runs it
- Uses `fly.toml` instead of docker-compose (different syntax but similar concept)
- **Fly Volumes** provide persistent disk — SQLite works
- **Fly Machines** can run on-demand and auto-stop when idle — you only pay when the machine is running. Perfect for a daily job
- Amsterdam datacenter available
- Multi-service support (run scanner + dashboard as separate Fly apps)
- Not docker-compose directly, but `fly.toml` covers similar ground
- **Machines pricing (2025):** shared-cpu-1x with 256MB: $0.0000022/s (~$5.70/month if always on, but with auto-stop for a 5-min daily job: essentially free)
- Free allowances: 3 shared-cpu VMs, 1 GB persistent volume

**Why it stands out:** Machines that auto-stop mean you pay almost nothing for a job that runs 5 minutes/day. EU datacenter available. Most cost-efficient container platform for bursty workloads.

### Render.com

Developer-focused platform with Docker support.

**Pricing:** Free tier (with spin-down after 15 min idle). Starter: $7/month for always-on.

**Key details:**
- Deploy from GitHub with a Dockerfile
- **Cron Jobs** built in as a service type — define schedule in the Render dashboard
- Persistent disks: $0.25/GB/month (15 MB SQLite = negligible)
- Free tier web services spin down after 15 min of inactivity (50-second cold start on next request)
- Frankfurt datacenter available
- HTTPS and custom domains included
- **Cron job pricing:** Starter plan at $7/month (runs on schedule, shuts down between runs)

**Why it stands out:** Cron Jobs as a first-class service type. If you want a managed cron that runs your Docker image, Render makes it simple. But at $7/month for a cron job, it is not the cheapest.

---

## 4. Self-Hosted PaaS on a VPS

These tools give you a Railway/Render-like experience, but you run them on your own VPS. You get the web UI and GitHub integration at VPS prices.

### Coolify

Open-source, self-hostable alternative to Railway/Vercel/Netlify.

**Pricing:** Free (open source). You pay only for the VPS it runs on (e.g., Hetzner CX22 at €4.35/month).

**Key details:**
- Install on any VPS with a single command
- **Native docker-compose support** — paste your docker-compose.yml, it deploys
- Web UI for managing services, viewing logs, and setting environment variables
- GitHub/GitLab integration with automatic deployments on push
- Built-in SSL (Let's Encrypt)
- Supports databases, cron jobs, persistent volumes
- **Resource overhead:** Coolify itself uses ~512 MB RAM and some CPU. On a CX22 (4 GB RAM), that leaves 3.5 GB for your workload — more than enough
- Active development, growing community
- Backup management built in

**Why it stands out:** Railway-like experience at VPS prices. If you want a web dashboard to manage your deployment but do not want to pay Railway/Render prices, this is the sweet spot.

### CapRover

Older, more established self-hosted PaaS. Similar concept to Coolify.

**Pricing:** Free (open source). You pay only for the VPS.

**Key details:**
- Docker-compose support via "One-Click Apps" and custom deployments
- Web dashboard for management
- Built-in Nginx reverse proxy and Let's Encrypt
- More mature than Coolify but less actively developed
- Slightly more complex initial setup

**Why it stands out:** Proven and stable. If Coolify feels too new, CapRover is the established alternative.

---

## 5. Serverless Container Options

These run your Docker container on-demand without a persistent server. Great for cost, but SQLite persistence requires workarounds.

### Google Cloud Run

Run Docker containers on demand with automatic scaling to zero.

**Pricing:** Free tier includes 2 million requests/month, 180,000 vCPU-seconds, 360,000 GiB-seconds. This workload would likely be **free**.

**Key details:**
- Build a Docker image, push to Google Container Registry, Cloud Run serves it
- **Cloud Run Jobs** (GA since 2023) — run a container on a schedule. Perfect for a daily scanner
- Scheduled via Cloud Scheduler (cron): 3 free jobs/month
- **No persistent disk** — this is the big limitation. SQLite cannot live on the container filesystem between runs
- **Workaround for SQLite:** Download the SQLite file from Cloud Storage at job start, run the scanner, upload it back at the end. Adds ~2-5 seconds and ~€0.01/month for storage. Requires a small wrapper script
- Alternatively, switch to Firestore or Cloud SQL (but that defeats the simplicity of SQLite)
- EU regions available (europe-west1 Belgium, europe-north1 Finland)
- 15-minute timeout on Jobs (plenty for a 5-minute scan)

**Why it stands out:** Genuinely free for this workload. But the SQLite workaround adds complexity. If you are willing to do the download/upload dance, it is hard to beat $0/month.

### AWS Fargate + EventBridge Scheduler

Run Docker containers on ECS Fargate, triggered by a cron schedule.

**Key details:**
- Define a task (Docker image), create a scheduled rule in EventBridge
- No free tier that covers Fargate practically
- ~$1-3/month for a 5-minute daily task
- **EFS for persistent storage** — SQLite works on EFS, but EFS has high latency for random reads (SQLite performance suffers)
- More complex setup than any other option (IAM roles, task definitions, VPC, etc.)
- Not recommended unless you are already deep in the AWS ecosystem

---

## 6. Comparison Table

| Provider | Type | docker-compose | Persistent SQLite | Monthly Cost | EU DC | Setup Effort |
|----------|------|----------------|-------------------|-------------|-------|-------------|
| **Hetzner CX22** | VPS | Native | Yes | €4.35 | DE/FI | Medium |
| **Hetzner CAX11** | VPS (ARM) | Native | Yes | €3.89 | DE/FI | Medium |
| **Oracle Free Tier** | VPS | Native | Yes | €0 | NL/DE | Medium |
| **Scaleway DEV1-S** | VPS | Native | Yes | €2.99 | FR/NL | Medium |
| **Contabo VPS S** | VPS | Native | Yes | €5.99 | DE | Medium |
| **Vultr** | VPS | Native | Yes | $5 | SE! | Low |
| **DigitalOcean** | VPS | Native | Yes | $6 | NL | Low |
| **Linode** | VPS | Native | Yes | $5 | UK | Low |
| **Railway** | Platform | Supported | Yes | $5-8 | US only | Very Low |
| **Fly.io** | Platform | Partial (fly.toml) | Yes | $0-5 | NL | Low |
| **Render** | Platform | Docker only | Yes (paid disk) | $7+ | DE | Very Low |
| **Coolify on Hetzner** | Self-hosted PaaS | Native | Yes | €4.35 | DE/FI | Medium-High |
| **Google Cloud Run** | Serverless | No | No (workaround) | $0 | FI/BE | Medium |
| **Azure Container Apps** | Serverless | Partial | Yes (volume) | $3-5 | Yes | Medium |
| **AWS Fargate** | Serverless | No | Possible (EFS) | $1-3 | Yes | High |

---

## 7. Recommendation

### Best Overall: Hetzner CX22 (€4.35/month) or CAX11 ARM (€3.89/month)

The CX22 is the default recommendation. Here is why:

- **Full docker-compose support** — your local setup works identically on the server
- **Persistent SQLite** on real SSD — no workarounds needed
- **EU datacenter** close to Sweden (Helsinki or Nuremberg)
- **Flexible** — add a Streamlit dashboard later, run more services, install whatever you want
- **Simple mental model** — it is a Linux server. You SSH in, you run Docker. No platform-specific concepts to learn
- **€4.35/month** is the price of a coffee

The CAX11 (ARM) at €3.89/month is even cheaper. If your Python dependencies all support ARM (pandas, numpy, yfinance, pandas-ta all do), this is the cheapest reliable option.

### Best Free: Oracle Cloud Free Tier

If you can get an ARM Ampere A1 instance (4 OCPU, 24 GB RAM), you get a server that would cost €20+/month elsewhere, for free forever. The caveats are real (availability, Oracle UI, account reclaim risk), but if it works, it is unbeatable.

**Strategy:** Try to get an Oracle ARM instance. If you cannot get one after a week of trying, go with Hetzner.

### Easiest Deploy: Railway ($5-8/month)

If you do not want to manage a server at all — no SSH, no apt-get, no firewall rules — Railway is the answer. Push to GitHub, it deploys. Set a cron schedule in the UI. Done.

The premium over Hetzner (~$3-4/month extra) buys you zero server management. For a personal project, this is a valid trade-off.

US-only datacenters do not matter for a daily batch job that calls yfinance (US-based anyway) and sends a Telegram message.

### Best "PaaS on a Budget": Coolify on Hetzner (€4.35/month)

If you want Railway's deploy experience (web UI, GitHub integration, one-click deploys) but at Hetzner prices, Coolify is the move. It takes 30 minutes to set up, and then you get a web dashboard to manage everything.

The trade-off: you still manage the underlying VPS (updates, security). But Coolify handles Docker, SSL, and deployments.

### If Already Invested in Azure: Azure Container Apps (~$3-5/month)

See [07-azure-hosting.md](07-azure-hosting.md) for the full Azure breakdown. Container Apps supports Docker, scheduled jobs, and persistent volumes. If your Azure subscription is already set up and you know the ecosystem, it makes sense to stay.

---

## 8. Quick Setup: Hetzner + Docker Compose

Since Hetzner is the top recommendation, here is the complete setup from zero to running.

### Step 1: Create the Server

1. Go to [console.hetzner.cloud](https://console.hetzner.cloud)
2. Create a project (e.g., "SwingTrader")
3. Add your SSH public key (Settings > SSH Keys)
4. Create a server:
   - Location: Helsinki (closest to Stockholm)
   - Image: Ubuntu 24.04
   - Type: CX22 (2 vCPU, 4 GB RAM, 40 GB SSD) — €4.35/month
   - SSH key: select the one you added
   - Name: `swingtrader`
5. Note the IP address

### Step 2: Initial Server Setup

```bash
# SSH into the server
ssh root@YOUR_SERVER_IP

# Update system
apt update && apt upgrade -y

# Create a non-root user (optional but recommended)
adduser trader
usermod -aG sudo trader

# Set up basic firewall
ufw allow OpenSSH
ufw enable
```

### Step 3: Install Docker and Docker Compose

```bash
# Install Docker (official method)
curl -fsSL https://get.docker.com | sh

# Add your user to the docker group
usermod -aG docker trader

# Docker Compose v2 is included with Docker Engine as of 2023
# Verify installation
docker --version
docker compose version
```

### Step 4: Deploy SwingTrader

```bash
# Switch to the trader user
su - trader

# Clone your repository
git clone https://github.com/YOUR_USERNAME/SwingTrader.git
cd SwingTrader

# Create .env file with your secrets
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
EOF

# Start the services
docker compose up -d

# Check that everything is running
docker compose ps
docker compose logs -f
```

### Step 5: Set Up Daily Execution

There are two approaches for scheduling:

**Option A: Host crontab (simpler)**

```bash
# Edit crontab for the trader user
crontab -e

# Add this line (runs at 18:15 CET = 17:15 UTC during summer, 16:15 UTC during winter)
# Using 17:15 UTC (CET is UTC+1, CEST is UTC+2 — adjust seasonally or use TZ)
15 16 * * 1-5 cd /home/trader/SwingTrader && docker compose run --rm scanner

# Alternatively, handle timezone properly:
15 16 * * 1-5 TZ=Europe/Stockholm date && cd /home/trader/SwingTrader && docker compose run --rm scanner
```

**Option B: Scheduler container in docker-compose (self-contained)**

Add an `ofelia` scheduler service to your `docker-compose.yml`:

```yaml
services:
  scanner:
    build: .
    volumes:
      - ./data:/app/data
    env_file: .env

  scheduler:
    image: mcuadros/ofelia:latest
    depends_on:
      - scanner
    command: daemon --docker
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    labels:
      ofelia.job-run.scanner.schedule: "0 15 16 * * 1-5"
      ofelia.job-run.scanner.container: "scanner"
```

This keeps everything in docker-compose — no host crontab needed.

### Step 6: Verify and Monitor

```bash
# Check logs after the first scheduled run
docker compose logs scanner --tail 50

# Check SQLite database exists and has data
ls -la data/swingtrader.db

# Set up a simple health check — add to crontab:
# Send yourself a Telegram message if the scanner did not run today
0 20 * * 1-5 cd /home/trader/SwingTrader && docker compose logs scanner --since 4h | grep -q "Scan complete" || curl -s "https://api.telegram.org/botYOUR_TOKEN/sendMessage?chat_id=YOUR_CHAT_ID&text=Scanner%20did%20not%20run%20today"
```

### Step 7: Backups (Optional but Recommended)

```bash
# Simple backup: copy SQLite to a safe location daily
# Add to crontab (runs at 19:00, after the scanner)
0 18 * * 1-5 cp /home/trader/SwingTrader/data/swingtrader.db /home/trader/backups/swingtrader-$(date +\%Y\%m\%d).db

# Keep only last 30 backups
5 18 * * 1-5 ls -t /home/trader/backups/swingtrader-*.db | tail -n +31 | xargs rm -f 2>/dev/null

# Or use Hetzner snapshots (€0.48/month for a 40GB snapshot):
# Create via Hetzner Cloud Console or API
```

### Step 8: Updates

```bash
# Pull latest code and rebuild
cd /home/trader/SwingTrader
git pull
docker compose build
docker compose up -d

# Or if using GitHub Actions, set up auto-deploy:
# Push to main -> GitHub Action SSHs into server, pulls, rebuilds
```

---

## Summary

For a personal Python trading scanner with SQLite and Docker Compose:

| If you want... | Choose | Cost |
|----------------|--------|------|
| Best value, full control | Hetzner CX22 | €4.35/month |
| Free forever (if available) | Oracle Cloud Free Tier | €0 |
| Cheapest reliable VPS | Scaleway DEV1-S | €2.99/month |
| Zero server management | Railway | ~$5-8/month |
| PaaS experience, VPS price | Coolify on Hetzner | €4.35/month |
| Already on Azure | Azure Container Apps | ~$3-5/month |

The Hetzner CX22 at €4.35/month with Docker Compose is the pragmatic choice. It works exactly like your local development setup, has no platform-specific quirks, and costs less than a coffee.
