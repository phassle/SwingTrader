# Hosting & Deployment Research for SwingTrader

> Research date: 2026-03-08
> Goal: Determine the best hosting and deployment approach for a personal swing trading scanner targeting Swedish stocks.

---

## Table of Contents

1. [What Needs to Run and When](#1-what-needs-to-run-and-when)
2. [Option A: Run Locally](#2-option-a-run-locally-simplest)
3. [Option B: Raspberry Pi / Home Server](#3-option-b-raspberry-pi--home-server)
4. [Option C: Cloud VPS](#4-option-c-cloud-vps-cheapest-always-on)
5. [Option D: Serverless / Cloud Functions](#5-option-d-serverless--cloud-functions)
6. [Option E: Container-Based (Docker)](#6-option-e-container-based-docker)
7. [Option F: Platform-as-a-Service](#7-option-f-platform-as-a-service)
8. [Notification Delivery Options](#8-notification-delivery-options)
9. [If You Want a Web Dashboard](#9-if-you-want-a-web-dashboard)
10. [Recommendation Matrix](#10-recommendation-matrix)
11. [Concrete Setup Guide for Recommended Path](#11-concrete-setup-guide-for-recommended-path)

---

## 1. What Needs to Run and When

Before evaluating hosting options, let's be precise about the workload:

### The Daily Scanner Job

- **Runs once per day** after Stockholm market close (17:30 CET)
- **Recommended schedule:** 18:00 CET (30 minutes after close lets data settle — Yahoo Finance sometimes has a short delay updating end-of-day bars for Nordic exchanges)
- **Duration:** 1-5 minutes for ~100 stocks. The bottleneck is network I/O (fetching data from Yahoo), not CPU. Each `yfinance` download takes roughly 0.5-2 seconds per ticker.
- **Resource needs:** Minimal. ~100 MB RAM, negligible CPU. Any machine from the last decade can handle this.
- **No weekends:** Stockholm exchange is closed Saturday-Sunday and Swedish public holidays. The cron job can run every day — it just won't find new data on non-trading days. Or you can skip weekends to be tidy.

### What Happens After the Scan

1. Fetch OHLCV data for all stocks in the universe (~100 tickers)
2. Calculate technical indicators (pandas-ta, pure CPU, takes milliseconds per stock)
3. Apply strategy rules, generate signals
4. Store results in SQLite
5. **Send notification** with any new buy signals (this is the part you actually care about seeing)
6. Optionally serve a web dashboard to review signals and history

### The Real Question

The scanner itself is trivial to run. The hosting decision really comes down to:
- **Do you want it to run unattended?** (If yes, you need something always-on)
- **Do you want remote access to results?** (If yes, you need notifications or a web UI)
- **How much do you want to maintain?** (Ranges from "nothing" to "full server admin")

---

## 2. Option A: Run Locally (Simplest)

Run the scanner on your own Mac or Linux machine using a scheduled task.

### macOS: launchd

The native macOS way to schedule tasks. More reliable than cron on macOS because it handles sleep/wake properly.

Create a plist file at `~/Library/LaunchAgents/com.swingtrader.scanner.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.swingtrader.scanner</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/perhassle/source/SwingTrader/venv/bin/python</string>
        <string>/Users/perhassle/source/SwingTrader/scanner.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/swingtrader.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/swingtrader-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>TZ</key>
        <string>Europe/Stockholm</string>
    </dict>
</dict>
</plist>
```

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.swingtrader.scanner.plist

# Verify it's loaded
launchctl list | grep swingtrader

# Unload if needed
launchctl unload ~/Library/LaunchAgents/com.swingtrader.scanner.plist
```

**Important macOS quirk:** launchd uses the system timezone. The `TZ` environment variable ensures 18:00 is interpreted as CET/CEST (Stockholm time), which handles daylight saving automatically.

### Linux: cron

```bash
crontab -e
```

Add:

```
# Run SwingTrader scanner at 18:00 CET daily (adjust for your server's timezone)
0 18 * * * cd /home/user/SwingTrader && /home/user/SwingTrader/venv/bin/python scanner.py >> /var/log/swingtrader.log 2>&1
```

If the server is in UTC, Stockholm is UTC+1 (CET) or UTC+2 (CEST). To handle DST properly:

```
# Use the TZ trick to let cron handle timezone correctly
0 18 * * * TZ="Europe/Stockholm" cd /home/user/SwingTrader && ./venv/bin/python scanner.py >> /var/log/swingtrader.log 2>&1
```

Or better yet, set the server timezone to `Europe/Stockholm` with `timedatectl set-timezone Europe/Stockholm`.

### Pros

- **Free.** No hosting costs.
- **Simple.** No deployment pipeline, no servers to manage.
- **Fast iteration.** Edit code, run it, see results immediately.
- **Full control.** No cloud provider restrictions or weird timeout limits.
- **Good for prototyping.** This is where you should start.

### Cons

- **Must be running.** If your Mac is off, asleep, or lid-closed at 18:00, the job doesn't run. macOS launchd will run missed jobs when the machine wakes up, but this is unreliable.
- **No remote access.** You can only see results on this machine (unless you add notifications).
- **Network dependency.** Your home internet must be up at scan time.
- **Not portable.** Tied to one physical machine.

### Verdict

**Perfect for Phase 1 prototyping.** Pair with Telegram notifications (Section 8) and you get results on your phone even when away from the machine. Graduate to a VPS once you want reliability.

---

## 3. Option B: Raspberry Pi / Home Server

A Raspberry Pi (or any always-on mini PC) sitting on your home network, running the scanner 24/7.

### Hardware

- **Raspberry Pi 4/5** — 2 GB RAM is enough, 4 GB is comfortable. Raspberry Pi 5 (4 GB) is ~$60.
- **microSD card** — 32 GB is plenty. ~$10.
- **Power supply** — ~$10.
- **Total cost:** ~$70-80 one-time.
- **Power consumption:** ~5W (Pi 4) to ~8W (Pi 5). At Swedish electricity prices (~1.5 SEK/kWh), that's roughly 5-10 SEK/month.

### Setup

```bash
# Install Raspberry Pi OS Lite (headless, no desktop needed)
# SSH in, then:

sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y

# Clone your repo
git clone https://github.com/yourusername/SwingTrader.git
cd SwingTrader

# Set up venv
python3 -m venv venv
source venv/bin/activate
pip install yfinance pandas pandas-ta

# Set timezone
sudo timedatectl set-timezone Europe/Stockholm

# Add cron job
crontab -e
# 0 18 * * * cd /home/pi/SwingTrader && ./venv/bin/python scanner.py >> /home/pi/swingtrader.log 2>&1
```

### Pros

- **Always on.** Runs 24/7, doesn't depend on your laptop being open.
- **Cheap.** One-time cost, negligible electricity.
- **No recurring fees.** Unlike a VPS.
- **Can serve a web dashboard** on your local network (Streamlit, FastAPI, etc.).
- **Fun project** if you like tinkering with hardware.

### Cons

- **Maintenance.** SD cards can corrupt. You need to manage updates, handle power outages (get a UPS or accept occasional missed runs).
- **Network dependency.** Relies on your home internet. If your router reboots at 18:00, the scan fails.
- **ARM architecture.** Most Python packages work fine on ARM, but occasionally you'll hit one that doesn't have pre-built wheels. pandas, numpy, yfinance all work fine though.
- **No remote access by default.** You'd need to set up a VPN, Tailscale, or port forwarding to access a dashboard remotely.
- **Single point of failure.** If it dies, you don't get notified (unless you have monitoring, which is more to maintain).

### Remote Access Options

If you want to access a Pi dashboard from outside your home:

- **Tailscale** (free, easy) — creates a private VPN between your devices. Install on Pi and phone. Access the dashboard via Tailscale IP.
- **Cloudflare Tunnel** (free) — expose a local port to the internet securely without port forwarding.
- **Neither is needed if you just use Telegram notifications.** The Pi sends you a message; you read it on your phone.

### Verdict

**Good middle ground** between local and cloud. Always-on without recurring costs. Best for someone who already has a Pi or enjoys home server tinkering. If you just want reliability without maintenance, a VPS is less hassle for ~$4/month.

---

## 4. Option C: Cloud VPS (Cheapest Always-On)

A small virtual private server in a European data center. This is the pragmatic choice for reliable, unattended operation.

### Provider Comparison

| Provider | Plan | RAM | CPU | Storage | EU Data Center | Monthly Cost |
|----------|------|-----|-----|---------|----------------|-------------|
| **Hetzner Cloud** | CX22 | 4 GB | 2 vCPU | 40 GB SSD | Falkenstein/Nuremberg (DE), Helsinki (FI) | **~$4.50** |
| **Hetzner Cloud** | CX11 | 2 GB | 1 vCPU | 20 GB SSD | Same as above | **~$3.30** |
| DigitalOcean | Basic Droplet | 1 GB | 1 vCPU | 25 GB SSD | Frankfurt (DE), Amsterdam (NL) | $6.00 |
| Linode (Akamai) | Nanode | 1 GB | 1 vCPU | 25 GB SSD | Frankfurt (DE) | $5.00 |
| AWS Lightsail | Micro | 1 GB | 2 vCPU | 40 GB SSD | Stockholm (SE), Frankfurt (DE) | $5.00 |
| Vultr | Cloud Compute | 1 GB | 1 vCPU | 25 GB SSD | Stockholm (SE), Amsterdam (NL) | $5.00 |
| Oracle Cloud | Always Free | 1 GB | 1/8 OCPU | 50 GB | Frankfurt (DE), Stockholm (SE) | **Free** |

### Why Hetzner Stands Out

- **Price/performance king in Europe.** The CX22 at ~$4.50/month gives you 4 GB RAM and 2 vCPUs — twice what competitors offer at the same price.
- **EU data centers.** Falkenstein and Nuremberg in Germany, Helsinki in Finland. Low latency to Nordic exchanges and Yahoo Finance's European CDN endpoints.
- **Simple, no-nonsense UX.** No AWS-style complexity with 200 services. You get a server, you SSH in, you're done.
- **Reliable.** Hetzner has been around since 1997. German engineering, literally.
- **The CX11 (2 GB, 1 vCPU, ~$3.30/month)** is actually more than enough for this workload. The scanner needs <100 MB RAM.

### Oracle Cloud Always Free Tier

Worth mentioning: Oracle Cloud offers a genuinely free tier that doesn't expire (unlike AWS Free Tier which expires after 12 months):
- 1 GB RAM, 1/8 OCPU (ARM-based), 50 GB storage
- Available in Frankfurt and Stockholm
- **Catch:** Oracle's UX is terrible. Account creation sometimes gets flagged for "verification" and never resolves. ARM architecture can have occasional package compatibility issues. If you can get it working, it's free forever. If you value your time, pay Hetzner $4/month.

### What You Get

A full Linux server (Ubuntu recommended) where you have root access. Install Python, set up cron, deploy your code. It's like having a Raspberry Pi in a professional data center with redundant power, networking, and storage.

### Setup Time

About 30 minutes from account creation to running scanner. See Section 11 for the full step-by-step guide.

### Pros

- **Always on.** 99.9%+ uptime SLA. The server doesn't sleep.
- **Remote access.** SSH from anywhere. Serve a web dashboard on the public IP.
- **Cheap.** $3-5/month is less than a coffee.
- **EU data centers.** Low latency for fetching Nordic market data.
- **Easy to maintain.** `apt update && apt upgrade` every few weeks. That's it.
- **Easy to backup.** SQLite file is tiny — copy it off the server periodically, or use Hetzner's snapshot feature (~$0.01/GB/month).
- **Scales up.** If you later want a web dashboard, PostgreSQL, or more processing power, just resize the VPS.

### Cons

- **Recurring cost.** ~$4/month, forever. (Trivial, but not free.)
- **Server maintenance.** You're responsible for OS updates, security patches, firewall rules. For a personal tool, this is minimal — but it's not zero.
- **SSH key management.** You need to manage SSH access. Not hard, but one more thing to know.

### Security Basics for a VPS

Since this is a personal tool, not a production SaaS, the security setup is minimal:

```bash
# Disable password login (use SSH keys only)
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Basic firewall
sudo ufw allow OpenSSH
sudo ufw enable

# If serving a web dashboard later:
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Automatic security updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Verdict

**The recommended choice for Phase 2+.** Hetzner CX11 or CX22 gives you a reliable, always-on server in Europe for less than a cup of coffee per month. Simple setup, minimal maintenance, and it just works.

---

## 5. Option D: Serverless / Cloud Functions

Run the scanner as a cloud function that executes on a schedule, with no server to manage.

### AWS Lambda + EventBridge

- **How it works:** Package the scanner as a Lambda function. EventBridge triggers it daily at 18:00 CET.
- **Timeout:** Max 15 minutes per invocation (plenty for scanning 100 stocks).
- **Memory:** Configurable, 128 MB to 10 GB. 256-512 MB is enough.
- **Free tier:** 1 million requests/month + 400,000 GB-seconds of compute. Your daily scan uses ~1 request and ~300 GB-seconds/month. **Effectively free forever.**
- **Cold start:** First invocation after idle period takes 5-15 seconds to initialize the Python runtime. Not a problem for a daily batch job.

```yaml
# AWS SAM template (simplified)
Resources:
  ScannerFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: scanner.lambda_handler
      Runtime: python3.12
      Timeout: 300
      MemorySize: 512
      Events:
        DailySchedule:
          Type: Schedule
          Properties:
            Schedule: cron(0 17 ? * MON-FRI *)  # 17:00 UTC = 18:00 CET
```

### Google Cloud Functions + Cloud Scheduler

- **How it works:** Deploy a Python function, Cloud Scheduler triggers it via HTTP.
- **Timeout:** Max 9 minutes (Gen 1) or 60 minutes (Gen 2). Gen 2 is fine.
- **Free tier:** 2 million invocations/month, 400,000 GB-seconds. Also effectively free.
- **Cloud Scheduler:** $0.10/month per scheduled job. Negligible.

### Azure Functions + Timer Trigger

- **How it works:** Python function with a timer trigger (CRON expression).
- **Timeout:** Max 10 minutes on Consumption plan.
- **Free tier:** 1 million executions/month, 400,000 GB-seconds. Free.

### The SQLite Problem

Here's the fundamental issue with serverless for this use case: **serverless functions have no persistent local storage.**

- Lambda functions run in ephemeral containers. When the function finishes, the filesystem is gone.
- SQLite requires a local file. You can't store your database inside the function.
- **Workarounds:**
  - Use S3 to store the SQLite file, download it at start, upload it when done. Works but adds complexity and latency.
  - Switch to DynamoDB (AWS) or Firestore (GCP). Different API, different query patterns. More vendor lock-in.
  - Use a managed PostgreSQL (AWS RDS, Supabase, Neon). Now you're adding a $10-15/month database to a "free" compute solution.

### Package Size Issue

Lambda and Cloud Functions have deployment package size limits:
- **Lambda:** 50 MB zipped, 250 MB unzipped
- **pandas + numpy + pandas-ta + yfinance** is roughly 150-200 MB unzipped
- **Solution:** Use a Lambda Layer or container image deployment (Lambda supports Docker images up to 10 GB)
- This is solvable but adds deployment complexity

### Pros

- **Zero server maintenance.** No OS updates, no SSH, no firewall rules.
- **Free (or nearly free).** Well within free tier limits for all providers.
- **Automatic scaling.** Not that you need it for 1 daily run, but it's there.
- **Built-in monitoring.** CloudWatch (AWS), Cloud Logging (GCP) included.

### Cons

- **SQLite doesn't work natively.** You need a different storage solution, which adds cost and complexity.
- **Deployment is more complex.** Packaging Python dependencies with native extensions (numpy, pandas) requires Docker-based builds or Lambda Layers.
- **Vendor lock-in.** Your code becomes tied to AWS/GCP/Azure patterns (event format, logging, etc.).
- **Debugging is harder.** You can't just SSH in and run the script manually. You're debugging via cloud console logs.
- **Overkill in complexity.** You're solving a "run a Python script daily" problem with enterprise-grade infrastructure.
- **Timezone handling.** EventBridge uses UTC. You need to handle CET/CEST conversion yourself or accept running at a fixed UTC time (which drifts by 1 hour with DST).

### Verdict

**Not recommended for this use case.** The serverless approach solves a problem you don't have (scaling, zero-downtime deployments) while creating a problem you do have (SQLite doesn't work, complex deployment). A $4/month VPS with cron is simpler, cheaper in total, and more flexible.

Serverless would make sense if: you already have AWS infrastructure, you're using DynamoDB anyway, and you want to avoid any server maintenance. For a personal trading scanner starting from scratch, it's over-engineering.

---

## 6. Option E: Container-Based (Docker)

Package the scanner in a Docker container and deploy it to a container hosting platform.

### Why Docker?

Docker wraps your entire environment — Python version, all dependencies, cron configuration — into a single image. "It works on my machine" becomes "it works everywhere."

### Dockerfile Example

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run scanner directly (platform handles scheduling)
CMD ["python", "scanner.py"]
```

### Container Hosting Platforms

#### Railway.app

- **What:** Simple deploy-from-Git platform. Push to GitHub, it builds and deploys.
- **Cron jobs:** Built-in cron support. Set a schedule in the dashboard.
- **Persistent storage:** Supports attached volumes for SQLite.
- **Cost:** Usage-based. For a 5-minute daily job: ~$1-3/month. Minimum $5/month if you use their Hobby plan (needed for cron).
- **EU region:** Available.
- **DX:** Excellent. `railway up` and you're deployed.

#### Fly.io

- **What:** Deploy Docker containers globally. Runs on Firecracker microVMs.
- **Persistent storage:** Fly Volumes — persistent disk attached to your VM. Perfect for SQLite.
- **Cron:** No built-in cron. You'd run a minimal always-on VM with cron inside the container, or use an external scheduler.
- **Cost:** Smallest VM (shared-cpu-1x, 256 MB) is ~$1.94/month. Volume storage is $0.15/GB/month. Total ~$2-3/month.
- **EU region:** Amsterdam, Stockholm (!) available.
- **DX:** Good. `fly launch`, `fly deploy`. Slightly more config than Railway.

```toml
# fly.toml
app = "swingtrader"
primary_region = "arn"  # Stockholm

[build]
  dockerfile = "Dockerfile"

[[mounts]]
  source = "swingtrader_data"
  destination = "/data"
  initial_size = "1"  # 1 GB

[env]
  TZ = "Europe/Stockholm"
  DATABASE_PATH = "/data/swingtrader.db"
```

#### Render.com

- **What:** PaaS with cron job support built in.
- **Cron jobs:** First-class feature. Define schedule, point to a Dockerfile or repo.
- **Cost:** Cron jobs on free tier (limited to monthly free hours). Paid starts at $7/month.
- **EU region:** Frankfurt available.
- **Persistent storage:** Render Disks, available on paid plans.
- **DX:** Very good. Connect GitHub repo, set up cron, done.

### Pros

- **Reproducible.** Same environment everywhere. Works on your Mac, works in the cloud.
- **Portable.** Move between Fly.io, Railway, any VPS, your local machine — same Docker image.
- **Clean dependency management.** No "pip install broke my system Python" issues.
- **Easy rollback.** Tag images, deploy previous versions if something breaks.

### Cons

- **Learning curve.** If you haven't used Docker before, there's a ramp-up period (a few hours to learn basics).
- **Slightly more complex than "just run the script."** You're adding a layer between your code and the OS.
- **Image size.** Python + pandas + numpy image is ~400-500 MB. Not a problem, but builds take a minute.
- **Cost varies.** Some platforms charge for build minutes, some for runtime, some for storage.

### Verdict

**Good choice for Phase 2-3**, especially if you plan to add a web dashboard later. Docker makes it easy to run both the scanner and a web app in the same deployment. Not necessary for Phase 1 — just run the script directly.

If you go this route, **Fly.io with a Stockholm region is the most interesting option** — persistent volumes for SQLite, Docker-native, and you can run a web dashboard on the same deployment.

---

## 7. Option F: Platform-as-a-Service

Platforms specifically designed for running Python scripts and web apps without managing servers.

### PythonAnywhere

- **What:** A Python-specific hosting platform with built-in scheduled tasks.
- **Scheduled tasks:** First-class feature. Set a script to run daily at a specific time. This is literally their core use case.
- **How it works:** Upload your code (or git clone), set up a virtual environment, schedule the task. That's it.
- **Free tier:** 1 scheduled task per day, 512 MB storage, limited CPU. Enough for the scanner.
- **Paid tier:** $5/month — unlimited scheduled tasks, more CPU time, SSH access, custom domains.
- **External access:** Free tier blocks outbound internet except to a whitelist. **yfinance requires outbound HTTP**, so you need the $5/month plan (or verify that Yahoo Finance's endpoints are on their whitelist — they may be).
- **SQLite:** Works perfectly. Persistent filesystem.

```bash
# On PythonAnywhere:
git clone https://github.com/yourusername/SwingTrader.git
cd SwingTrader
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Then in the PythonAnywhere dashboard:
# Scheduled Tasks > Add > /home/yourusername/SwingTrader/venv/bin/python /home/yourusername/SwingTrader/scanner.py
# Schedule: 17:00 UTC (= 18:00 CET)
```

### Heroku

- **What:** General PaaS. Deploy from Git, runs in ephemeral containers ("dynos").
- **Scheduler:** Heroku Scheduler add-on (free) — runs tasks at set intervals (daily, hourly, every 10 min).
- **Cost:** Eco dyno plan at $5/month. Scheduler is a free add-on.
- **Storage problem:** Heroku dynos have **ephemeral filesystems**. When the dyno restarts (at least once every 24 hours), your SQLite file is gone. You'd need Heroku Postgres ($0-5/month for hobby tier).
- **No EU region.** US and EU available, but EU is a paid-only option.

### Comparison for Python Cron Workloads

| Feature | PythonAnywhere | Heroku |
|---------|---------------|--------|
| Scheduled tasks | Built-in, first-class | Add-on (Scheduler) |
| SQLite support | Yes (persistent filesystem) | No (ephemeral filesystem) |
| Python focus | Yes (it's in the name) | General purpose |
| Cost | Free / $5/month | $5-7/month |
| Setup complexity | Very low | Low-medium |
| EU data center | EU server option | EU (paid plans) |
| Outbound internet (free) | Restricted whitelist | Unrestricted |
| Web app hosting | Yes (WSGI apps) | Yes |

### Verdict

**PythonAnywhere is underrated for this exact use case.** It's literally designed for "I have a Python script that needs to run on a schedule." The $5/month plan gives you scheduled tasks, persistent storage (SQLite works), and outbound internet. No Docker, no cron configuration, no server maintenance.

**Heroku is not a great fit** because of the ephemeral filesystem (SQLite dies on restart) and the need for an add-on database. If you're already on Heroku for other projects, it works. Otherwise, PythonAnywhere or a VPS is simpler.

---

## 8. Notification Delivery Options

Once the scanner runs, you need to know the results. Here are the practical options, ranked by ease of setup.

### Telegram Bot (Recommended)

**Why Telegram wins for personal tools:**
- Free. Forever. No API costs.
- Push notifications to your phone instantly.
- Rich formatting (bold, code blocks, links).
- Dead simple to set up (10 minutes).
- No server needed — your script makes an HTTP POST, Telegram delivers it.
- Works on phone, desktop, and web.

**Setup time:** 10 minutes.

#### Step-by-step Setup

1. **Create a bot:** Open Telegram, find `@BotFather`, send `/newbot`, follow the prompts. You'll get an API token like `7123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`.

2. **Get your chat ID:** Send any message to your new bot, then visit:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
   Find `"chat":{"id":123456789}` in the response. That's your chat ID.

3. **Send messages from Python:**

```python
import requests

TELEGRAM_BOT_TOKEN = "7123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw"
TELEGRAM_CHAT_ID = "123456789"

def send_telegram_message(message: str) -> bool:
    """Send a message via Telegram bot. Returns True if successful."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Telegram notification failed: {e}")
        return False

# Usage in scanner:
def notify_signals(signals: list[dict]) -> None:
    if not signals:
        msg = "SwingTrader: No buy signals today."
    else:
        lines = ["*SwingTrader Buy Signals*\n"]
        for s in signals:
            lines.append(
                f"*{s['ticker']}* ({s['name']})\n"
                f"  Close: {s['close']}  |  RSI: {s['rsi']}\n"
                f"  Signal: {s['strategy']}\n"
            )
        msg = "\n".join(lines)

    send_telegram_message(msg)
```

4. **Store the token securely.** Don't hardcode it. Use environment variables or a `.env` file:

```python
import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
```

```bash
# .env file (add to .gitignore!)
TELEGRAM_BOT_TOKEN=7123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
TELEGRAM_CHAT_ID=123456789
```

### Slack Webhook

- **Setup:** Create a Slack workspace (free), create an Incoming Webhook via Slack API dashboard.
- **How:** POST JSON to the webhook URL.
- **Pros:** Rich formatting, threaded messages, search history.
- **Cons:** Requires a Slack workspace (overkill for 1 person). Webhook URLs can expire if the app is reinstalled.

```python
import requests

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]  # from Slack Incoming Webhooks

def send_slack_message(message: str) -> bool:
    payload = {"text": message}
    response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
    return response.status_code == 200
```

### Discord Webhook

- **Setup:** Create a Discord server, create a webhook in channel settings.
- **Pros:** Free, supports embeds (rich cards with colors, fields, thumbnails).
- **Cons:** Discord is more "gaming/community" oriented. Fine for personal use.

```python
import requests

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/123456/abcdef..."

def send_discord_message(message: str) -> bool:
    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
    return response.status_code == 204
```

### Email (SMTP / SendGrid)

- **Gmail SMTP:** Free, but Google has tightened security. You need an "App Password" (not your regular password). Can end up in spam.
- **SendGrid:** Free tier is 100 emails/day. More reliable delivery than raw SMTP.
- **Pros:** Universal. Everyone has email.
- **Cons:** Slower delivery than push notifications. Easy to miss among other emails. More setup than Telegram.

```python
import smtplib
from email.mime.text import MIMEText

def send_email(subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "your-email@gmail.com"
    msg["To"] = "your-email@gmail.com"

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("your-email@gmail.com", "your-app-password")
        server.send_message(msg)
```

### Pushover

- **What:** Dedicated push notification service. iOS/Android app.
- **Cost:** $5 one-time purchase per platform (iOS or Android).
- **API:** Simple HTTP POST with API token and user key.
- **Pros:** Designed for exactly this — machine-to-human notifications. Priority levels, sounds, quiet hours.
- **Cons:** Costs $5. Not free like Telegram.

### Comparison

| Method | Cost | Setup Time | Push Notification | Rich Formatting | Best For |
|--------|------|-----------|-------------------|-----------------|----------|
| **Telegram** | Free | 10 min | Yes | Markdown | Personal tools (recommended) |
| Slack | Free | 15 min | Yes | Rich blocks | If you already use Slack |
| Discord | Free | 10 min | Yes | Embeds | If you already use Discord |
| Email | Free | 20 min | No (pull) | HTML | Formal reports |
| Pushover | $5 once | 10 min | Yes | Basic | Dedicated notification fans |

### Recommendation

**Start with Telegram.** It's free, takes 10 minutes to set up, and gives you instant push notifications on your phone. The code is trivial (one HTTP POST). You can always add other channels later.

---

## 9. If You Want a Web Dashboard

### Do You Need One at Phase 1?

**No.** At Phase 1, a Telegram notification with today's buy signals is all you need. A dashboard is a Phase 3 feature — build it when:

- You want to review historical signals visually
- You want to see stock charts with indicator overlays
- You want to browse the full signal history, not just today's

### Simple Option: Streamlit

**Streamlit is purpose-built for this.** Write Python, get a web app. No frontend code at all.

```python
# dashboard.py
import streamlit as st
import pandas as pd
import sqlite3

st.title("SwingTrader Dashboard")

conn = sqlite3.connect("swingtrader.db")

# Recent signals
st.header("Recent Buy Signals")
signals = pd.read_sql("""
    SELECT date, ticker, strategy, strength, price_at_signal
    FROM signals
    WHERE signal_type = 'BUY'
    ORDER BY date DESC
    LIMIT 20
""", conn)
st.dataframe(signals)

# RSI overview
st.header("Current RSI Values")
rsi_data = pd.read_sql("""
    SELECT s.ticker, s.name, i.rsi_14, i.date
    FROM indicators i
    JOIN stocks s ON i.ticker = s.ticker
    WHERE i.date = (SELECT MAX(date) FROM indicators)
    ORDER BY i.rsi_14 ASC
""", conn)
st.bar_chart(rsi_data.set_index("ticker")["rsi_14"])
```

```bash
pip install streamlit
streamlit run dashboard.py
# Opens browser at http://localhost:8501
```

- **Hosting:** Run on the same VPS. Access via `http://your-vps-ip:8501`.
- **Streamlit Cloud:** Free for public apps. But your trading signals are personal — you probably don't want them public.
- **Authentication:** Streamlit has basic password protection (`st.secrets`). For personal use, restricting access by IP or VPN is simpler.

### More Control: FastAPI + Simple Frontend

If you want an API (e.g., for a mobile app later):

```python
# api.py
from fastapi import FastAPI
import sqlite3

app = FastAPI()

@app.get("/signals/latest")
def get_latest_signals():
    conn = sqlite3.connect("swingtrader.db")
    cursor = conn.execute("""
        SELECT ticker, date, strategy, strength, price_at_signal
        FROM signals
        WHERE signal_type = 'BUY' AND date = (SELECT MAX(date) FROM signals)
    """)
    return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor]
```

```bash
pip install fastapi uvicorn
uvicorn api:app --host 0.0.0.0 --port 8000
```

Pair with a simple HTML page, a React/Next.js frontend, or just use the JSON API directly from your phone browser.

### Verdict

**Skip the dashboard for Phase 1-2.** Telegram notifications give you everything you need. When you're ready for Phase 3, Streamlit is the fastest path — you can build a functional dashboard in an afternoon, and it's all Python (no React/TypeScript needed unless you want polish).

---

## 10. Recommendation Matrix

| Phase | Hosting | Storage | Notifications | Web UI | Cost |
|-------|---------|---------|---------------|--------|------|
| **Phase 1** (prototype, weeks 1-4) | Local (Mac launchd or manual) | SQLite | Telegram | None | Free |
| **Phase 2** (reliable daily operation) | Hetzner CX11 VPS (~$3.30/mo) or PythonAnywhere ($5/mo) | SQLite | Telegram | None | ~$3-5/mo |
| **Phase 3** (with dashboard) | Hetzner CX22 VPS (~$4.50/mo) | SQLite or PostgreSQL | Telegram + Web UI | Streamlit | ~$4-5/mo |
| **Phase 3 alt** (container-based) | Fly.io Stockholm + Docker | SQLite (Fly Volume) | Telegram + Web UI | Streamlit/FastAPI | ~$3-5/mo |

### Decision Flowchart

```
Start here:
  |
  v
Are you still building/testing the strategy?
  |-- Yes --> Run locally (Phase 1). Add Telegram for convenience.
  |-- No, strategy works, want reliable daily runs -->
        |
        Do you want zero server management?
        |-- Yes --> PythonAnywhere ($5/mo). Scheduled tasks built in.
        |-- No, comfortable with SSH/Linux -->
              |
              Do you plan to add a web dashboard?
              |-- Not yet --> Hetzner CX11 ($3.30/mo) + cron
              |-- Yes --> Hetzner CX22 ($4.50/mo) + Docker + Streamlit
```

---

## 11. Concrete Setup Guide for Recommended Path

**Target:** Hetzner CX11/CX22 VPS + Python + cron + Telegram notifications.

This is the full path from zero to "scanner runs automatically every day and texts me the results."

### Step 1: Create a Hetzner Cloud Account

1. Go to [console.hetzner.cloud](https://console.hetzner.cloud)
2. Sign up (email + payment method, they accept credit cards and PayPal)
3. Create a new project (e.g., "SwingTrader")

### Step 2: Create the Server

1. Click "Add Server"
2. **Location:** Falkenstein (DE) or Helsinki (FI) — both are close to Stockholm
3. **Image:** Ubuntu 24.04 LTS
4. **Type:** CX11 (2 GB RAM, 1 vCPU, 20 GB SSD) — more than enough
5. **SSH Key:** Add your public key. If you don't have one:
   ```bash
   # On your Mac:
   ssh-keygen -t ed25519 -C "swingtrader-hetzner"
   # Press Enter for default location, set a passphrase or leave empty
   cat ~/.ssh/id_ed25519.pub
   # Copy the output and paste it into Hetzner's SSH key field
   ```
6. **Server name:** `swingtrader`
7. Click "Create & Buy Now" (~$3.30/month)

### Step 3: Connect and Set Up the Server

```bash
# SSH into your new server (replace with your server's IP)
ssh root@<YOUR_SERVER_IP>

# Set timezone to Stockholm
timedatectl set-timezone Europe/Stockholm

# Update system
apt update && apt upgrade -y

# Install Python and essentials
apt install python3 python3-pip python3-venv git -y

# Create a non-root user (good practice)
adduser swingtrader --disabled-password --gecos ""
usermod -aG sudo swingtrader

# Copy SSH key to the new user
mkdir -p /home/swingtrader/.ssh
cp ~/.ssh/authorized_keys /home/swingtrader/.ssh/
chown -R swingtrader:swingtrader /home/swingtrader/.ssh

# Switch to the new user
su - swingtrader
```

### Step 4: Deploy the Code

```bash
# As the swingtrader user:
cd ~

# Option A: Clone from GitHub
git clone https://github.com/yourusername/SwingTrader.git
cd SwingTrader

# Option B: Copy files from your Mac (from your local terminal)
# scp -r /Users/perhassle/source/SwingTrader swingtrader@<YOUR_SERVER_IP>:~/

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install yfinance pandas pandas-ta requests python-dotenv
```

### Step 5: Create the Telegram Bot

1. Open Telegram on your phone
2. Search for `@BotFather` and start a chat
3. Send `/newbot`
4. Choose a name (e.g., "SwingTrader Bot") and username (e.g., `swingtrader_signals_bot`)
5. Copy the API token you receive
6. Send any message to your new bot (this creates the chat)
7. Get your chat ID:
   ```bash
   curl "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"
   # Find "chat":{"id":XXXXXXX} in the response
   ```

### Step 6: Configure Environment Variables

```bash
# On the server:
cat > ~/SwingTrader/.env << 'EOF'
TELEGRAM_BOT_TOKEN=7123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
TELEGRAM_CHAT_ID=123456789
EOF

# Make sure .env is in .gitignore
echo ".env" >> ~/SwingTrader/.gitignore
```

### Step 7: Add Notification Code to the Scanner

Add to your scanner script (or create a `notifications.py` module):

```python
# notifications.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(message: str) -> bool:
    """Send a Telegram message. Returns True on success."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Warning: Telegram credentials not configured")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            print(f"Telegram API error: {resp.status_code} {resp.text}")
            return False
        return True
    except requests.RequestException as e:
        print(f"Telegram send failed: {e}")
        return False


def format_signal_report(signals: list[dict], date: str) -> str:
    """Format buy signals into a Telegram message."""
    if not signals:
        return f"SwingTrader {date}: No buy signals today."

    lines = [f"*SwingTrader Signals - {date}*\n"]
    for i, s in enumerate(signals, 1):
        lines.append(
            f"{i}. *{s['ticker']}* ({s['name']})\n"
            f"   Strategy: {s.get('strategy', 'N/A')}\n"
            f"   RSI: {s.get('rsi', 'N/A')} | Close: {s.get('close', 'N/A')}\n"
        )
    lines.append(f"_{len(signals)} signal(s) total_")
    return "\n".join(lines)
```

Call it from your scanner's `main()`:

```python
from notifications import send_telegram, format_signal_report

# At the end of main():
message = format_signal_report(buy_signals, datetime.now().strftime("%Y-%m-%d"))
send_telegram(message)
```

### Step 8: Test Everything

```bash
# On the server:
cd ~/SwingTrader
source venv/bin/activate

# Run the scanner manually
python scanner.py

# You should see output in the terminal AND get a Telegram message
```

### Step 9: Set Up the Cron Job

```bash
# Edit crontab
crontab -e

# Add this line (18:00 Stockholm time, Monday-Friday):
0 18 * * 1-5 cd /home/swingtrader/SwingTrader && /home/swingtrader/SwingTrader/venv/bin/python scanner.py >> /home/swingtrader/scanner.log 2>&1
```

Verify the timezone is correct:

```bash
date
# Should show Stockholm time (CET/CEST)

# List cron jobs
crontab -l
```

### Step 10: Basic Monitoring

Add a simple health check — if the scanner fails, you want to know:

```python
# Add to the end of scanner.py main():
try:
    # ... your scanning logic ...
    message = format_signal_report(buy_signals, today)
    send_telegram(message)
except Exception as e:
    send_telegram(f"SwingTrader ERROR: {e}")
    raise
```

This way, if the scanner crashes, you still get a Telegram message telling you something went wrong.

### Step 11: Log Rotation (Optional but Tidy)

Prevent the log file from growing forever:

```bash
# Create logrotate config
sudo tee /etc/logrotate.d/swingtrader << 'EOF'
/home/swingtrader/scanner.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
EOF
```

### Step 12: Automatic Updates from Git (Optional)

If you push updates to GitHub and want the server to pull them automatically before each scan:

```bash
# In crontab, change the command to:
0 18 * * 1-5 cd /home/swingtrader/SwingTrader && git pull --ff-only && /home/swingtrader/SwingTrader/venv/bin/python scanner.py >> /home/swingtrader/scanner.log 2>&1
```

**Be careful with this.** A broken commit on main will break your daily scan. Only do this if you're disciplined about testing before pushing.

---

## Summary

For a personal swing trading scanner targeting Swedish stocks:

1. **Start local** (Phase 1). Run on your Mac, add Telegram notifications. Free, fast iteration.
2. **Move to Hetzner CX11** (Phase 2) when you want reliability. $3.30/month, 30 minutes to set up, and it just runs.
3. **Add Streamlit dashboard** (Phase 3) on the same VPS when you want visual review of signals.
4. **Telegram for notifications** from day one. 10 minutes to set up, free, instant push to your phone.

Total cost at steady state: **~$3-5/month.** That's it. No need for Kubernetes, serverless, microservices, or any enterprise infrastructure. This is a personal tool that runs a Python script once a day.
