# 17 - Monitoring and Alerting

> Research date: 2026-03-09
> Goal: Define what can go wrong with the SwingTrader daily scanner and how to detect and respond to failures — health checks, logging, data quality validation, and alerting.
> Prerequisites: [05-data-pipeline-and-quality.md](05-data-pipeline-and-quality.md), [09-azure-container-apps-deep-dive.md](09-azure-container-apps-deep-dive.md), [10-hetzner-coolify-deep-dive.md](10-hetzner-coolify-deep-dive.md), [14-telegram-bot-setup.md](14-telegram-bot-setup.md)

---

## Table of Contents

1. [What Can Go Wrong](#1-what-can-go-wrong)
2. [Health Checks: Dead Man's Switch](#2-health-checks-dead-mans-switch)
3. [Logging Best Practices](#3-logging-best-practices)
4. [Data Quality Checks](#4-data-quality-checks)
5. [Azure-Specific Monitoring](#5-azure-specific-monitoring)
6. [Hetzner/Coolify-Specific Monitoring](#6-hetznercoolify-specific-monitoring)
7. [Alerting Strategy](#7-alerting-strategy)
8. [Complete Monitoring Integration](#8-complete-monitoring-integration)
9. [Operational Runbook](#9-operational-runbook)

---

## 1. What Can Go Wrong

### Failure modes for a daily scanner

| Failure | Severity | Detection | Frequency |
|---------|----------|-----------|-----------|
| Scanner doesn't run at all | **Critical** | Dead man's switch | Rare (cron/scheduler issue) |
| yfinance API down or rate limited | High | Data quality check | Occasional |
| Partial data (some tickers fail) | Medium | Ticker count check | Common |
| Stale data (weekend/holiday data) | Low | Date freshness check | Expected |
| Telegram notification fails | Medium | Send result logging | Rare |
| Database write fails | High | Exception handling | Rare |
| Scanner runs but produces wrong signals | **Critical** | Hard to detect automatically | Very rare |
| Container crashes mid-scan | High | Container restart + dead man's switch | Rare |
| Disk full (SQLite) or RU exhaustion (Cosmos DB) | Medium | Resource monitoring | Rare |

### The most dangerous failure

The scanner silently not running. If it crashes, you get no signals — but you also get no error notification (because the notification code didn't run either). This is why a **dead man's switch** is essential.

---

## 2. Health Checks: Dead Man's Switch

### Concept

A dead man's switch monitors by expecting a regular "I'm alive" ping. If the ping stops, it alerts you. This detects the most dangerous failure mode: the scanner not running at all.

### Healthchecks.io (recommended)

**Free tier:** 20 checks, unlimited pings, email/Telegram/Slack notifications.

#### Setup

1. Create an account at [healthchecks.io](https://healthchecks.io)
2. Create a new check:
   - **Name:** `SwingTrader Daily Scan`
   - **Period:** 24 hours
   - **Grace:** 1 hour (allows for schedule drift)
3. Copy the ping URL: `https://hc-ping.com/your-uuid-here`
4. Add the URL to your `.env` as `HEALTHCHECKS_PING_URL`

#### How it works

```
Normal: Scanner runs → pings healthchecks.io → timer resets → all good
Failure: Scanner doesn't run → no ping → timer expires → alert sent
```

#### Ping integration

```python
import os
import requests
import logging

logger = logging.getLogger(__name__)

def ping_healthcheck(status: str = "") -> None:
    """Ping Healthchecks.io to signal the scanner is alive.

    Args:
        status: "" for success, "/fail" for failure, "/start" for scan start.
    """
    url = os.environ.get("HEALTHCHECKS_PING_URL")
    if not url:
        logger.debug("HEALTHCHECKS_PING_URL not set, skipping ping")
        return

    try:
        requests.get(f"{url}{status}", timeout=5)
    except requests.RequestException as e:
        # Never let monitoring failure crash the scanner
        logger.warning("Failed to ping healthchecks.io: %s", e)
```

#### Usage in the pipeline

```python
def run_daily_scan():
    ping_healthcheck("/start")  # Signal scan has started

    try:
        # ... run the scan ...
        ping_healthcheck()  # Signal success
    except Exception as e:
        ping_healthcheck("/fail")  # Signal failure
        raise
```

#### Alert channels

Configure Healthchecks.io to notify you via:
- **Telegram** (uses your same bot — Healthchecks.io has built-in Telegram integration)
- Email (as backup)

This means: if the scanner fails to run, you get a Telegram message from Healthchecks.io. If Telegram itself is down, you get an email.

---

## 3. Logging Best Practices

### Structured logging setup

```python
import logging
import sys

def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the scanner pipeline."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
```

### What to log at each level

| Level | Use for | Example |
|-------|---------|---------|
| `DEBUG` | Detailed diagnostic info | `"Fetched 126 rows for VOLV-B.ST"` |
| `INFO` | Normal operational events | `"Scan started for 95 tickers"`, `"3 signals generated"` |
| `WARNING` | Unexpected but handled issues | `"Failed to fetch ELAN-B.ST, skipping"`, `"Healthcheck ping failed"` |
| `ERROR` | Failures that need attention | `"Telegram notification failed after 3 retries"` |
| `CRITICAL` | Scanner cannot continue | `"Database connection failed, aborting scan"` |

### Log key metrics at scan completion

```python
logger.info(
    "Scan complete: tickers=%d, successful=%d, failed=%d, signals=%d, duration=%.1fs",
    total_tickers,
    successful_tickers,
    failed_tickers,
    signal_count,
    duration_seconds,
)
```

This single line lets you spot trends:
- `failed=15` when it's usually `failed=0` → yfinance issue
- `signals=0` for many days → strategy may need tuning (or market is just quiet)
- `duration=180s` when it's usually `30s` → rate limiting or network issues

### Log rotation (Phase 2+)

For Phase 1, logging to stdout is sufficient — container platforms capture stdout logs automatically. For Phase 2:

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler("scanner.log", maxBytes=10_000_000, backupCount=5)
```

---

## 4. Data Quality Checks

Run these checks after fetching data but before generating signals.

### Check 1: Minimum ticker coverage

```python
def check_ticker_coverage(
    results: dict[str, any],
    total_tickers: int,
    min_coverage: float = 0.8,
) -> bool:
    """Ensure at least 80% of tickers returned data."""
    success_rate = len(results) / total_tickers
    if success_rate < min_coverage:
        logger.error(
            "Ticker coverage too low: %d/%d (%.0f%%). Minimum: %.0f%%",
            len(results), total_tickers, success_rate * 100, min_coverage * 100,
        )
        return False
    if success_rate < 0.95:
        logger.warning(
            "Ticker coverage below normal: %d/%d (%.0f%%)",
            len(results), total_tickers, success_rate * 100,
        )
    return True
```

### Check 2: Data freshness

```python
from datetime import date, timedelta

def check_data_freshness(
    latest_date: date,
    max_age_days: int = 3,
) -> bool:
    """Ensure the latest data point is recent enough.

    Allows for weekends (2 days) and single holidays (3 days).
    """
    age = (date.today() - latest_date).days
    if age > max_age_days:
        logger.error("Data is %d days old (latest: %s). Possible data source issue.", age, latest_date)
        return False
    if age > 1:
        logger.info("Data is %d days old (latest: %s) — likely weekend/holiday.", age, latest_date)
    return True
```

### Check 3: Price sanity

```python
def check_price_sanity(ticker: str, close: float, prev_close: float) -> bool:
    """Flag suspicious price movements (>30% in one day)."""
    if prev_close == 0:
        return True
    change_pct = abs(close - prev_close) / prev_close
    if change_pct > 0.30:
        logger.warning(
            "Suspicious price for %s: %.2f → %.2f (%.1f%% change). Possible data error.",
            ticker, prev_close, close, change_pct * 100,
        )
        return False
    return True
```

### Check 4: Volume sanity

```python
def check_volume_sanity(ticker: str, volume: int, avg_volume: float) -> bool:
    """Flag tickers with abnormally low volume (possible data issue)."""
    if avg_volume > 0 and volume < avg_volume * 0.01:
        logger.warning(
            "Abnormally low volume for %s: %d (avg: %.0f). Possible data gap.",
            ticker, volume, avg_volume,
        )
        return False
    return True
```

---

## 5. Azure-Specific Monitoring

### Azure Container Apps built-in features

| Feature | What it does | Setup |
|---------|-------------|-------|
| **Container logs** | Stdout/stderr captured automatically | View in Azure Portal → Logs |
| **Log Analytics** | Query logs with KQL | Auto-enabled with Container Apps |
| **Revision health** | Shows if container is running | Azure Portal → Revisions |
| **Alerts** | Email/SMS on conditions | Azure Monitor → Alerts |

### Useful KQL queries

```kusto
// Recent scanner logs
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "swingtrader-scanner"
| where TimeGenerated > ago(24h)
| order by TimeGenerated desc
| take 100

// Error logs only
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "swingtrader-scanner"
| where Log_s contains "[ERROR]" or Log_s contains "[CRITICAL]"
| where TimeGenerated > ago(7d)
| order by TimeGenerated desc

// Container restarts (crash detection)
ContainerAppSystemLogs_CL
| where ContainerAppName_s == "swingtrader-scanner"
| where EventSource_s == "KEDA" or Reason_s contains "restart"
| where TimeGenerated > ago(7d)
```

### Azure Monitor alert (Phase 2+)

```bash
# Alert on scanner errors
az monitor metrics alert create \
  --name "SwingTrader Scanner Errors" \
  --resource-group swingtrader-rg \
  --scopes /subscriptions/.../containerApps/swingtrader-scanner \
  --condition "count Log_s contains 'ERROR' > 0" \
  --action-group email-alerts
```

For Phase 1, Healthchecks.io + Telegram alerts are sufficient. Azure Monitor adds value in Phase 2 when you want dashboards and historical analysis.

---

## 6. Hetzner/Coolify-Specific Monitoring

### Coolify built-in features

| Feature | What it does |
|---------|-------------|
| **Container logs** | View stdout/stderr in Coolify UI |
| **Health checks** | Built-in container health monitoring |
| **Notifications** | Telegram/Discord/email on deploy events |

### Server-level monitoring

On a Hetzner VPS, also monitor the server itself:

```bash
# Check disk usage (cron job, alert if >80%)
df -h / | awk 'NR==2 {print $5}' | tr -d '%'

# Check memory usage
free -m | awk 'NR==2 {printf "%.0f", $3/$2*100}'
```

### Uptime Kuma (optional)

If self-hosting on Hetzner, [Uptime Kuma](https://github.com/louislam/uptime-kuma) is a lightweight monitoring tool that runs alongside your scanner:

- Monitors HTTP endpoints, TCP ports, Docker containers
- Sends alerts via Telegram, email, Discord
- Self-hosted, free, low resource usage
- Can act as a dead man's switch (Push monitor type)

Deploy via Coolify with one click or:

```yaml
# docker-compose monitoring stack
services:
  uptime-kuma:
    image: louislam/uptime-kuma:1
    volumes:
      - uptime-kuma-data:/app/data
    ports:
      - "3001:3001"
    restart: unless-stopped
```

---

## 7. Alerting Strategy

### Alert tiers

| Tier | What triggers it | How you're notified | Response time |
|------|------------------|--------------------|----|
| **P1 Critical** | Scanner didn't run, database down | Healthchecks.io → Telegram + Email | Same day |
| **P2 Warning** | Ticker coverage <80%, Telegram send failed | Scanner error log → Telegram alert | Next scan |
| **P3 Info** | Low coverage (80-95%), data staleness | Log entry only | Next weekly review |

### Avoid alert fatigue

- Only send Telegram alerts for P1 and P2 events
- Log P3 events but don't alert
- One daily summary is enough — don't send individual alerts for each failed ticker
- If a known issue recurs (e.g., a specific ticker always fails), suppress the alert for that ticker

### Alert deduplication

```python
def should_alert(error_key: str, cooldown_hours: int = 24) -> bool:
    """Prevent duplicate alerts for the same issue within the cooldown period."""
    cache_file = Path(".alert_cache.json")
    now = time.time()

    cache = {}
    if cache_file.exists():
        cache = json.loads(cache_file.read_text())

    last_alert = cache.get(error_key, 0)
    if now - last_alert < cooldown_hours * 3600:
        return False

    cache[error_key] = now
    cache_file.write_text(json.dumps(cache))
    return True
```

---

## 8. Complete Monitoring Integration

```python
"""
monitoring.py — Health checks, data quality, and alerting for SwingTrader.
"""

import json
import logging
import os
import time
from datetime import date, timedelta
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class ScanMonitor:
    """Monitors scan health and sends alerts when things go wrong."""

    def __init__(self, notifier=None):
        """
        Args:
            notifier: TelegramNotifier instance for sending alerts.
                      If None, alerts are logged only.
        """
        self.notifier = notifier
        self.healthcheck_url = os.environ.get("HEALTHCHECKS_PING_URL")
        self.alert_cache_path = Path(".alert_cache.json")
        self.issues: list[str] = []

    def ping_start(self) -> None:
        """Signal that the scan has started."""
        self._ping("/start")

    def ping_success(self) -> None:
        """Signal that the scan completed successfully."""
        self._ping("")

    def ping_failure(self) -> None:
        """Signal that the scan failed."""
        self._ping("/fail")

    def check_ticker_coverage(
        self,
        successful: int,
        total: int,
        min_coverage: float = 0.8,
    ) -> bool:
        """Verify sufficient tickers returned data."""
        rate = successful / total if total > 0 else 0
        if rate < min_coverage:
            msg = f"Ticker coverage critical: {successful}/{total} ({rate:.0%})"
            logger.error(msg)
            self.issues.append(msg)
            return False
        if rate < 0.95:
            logger.warning("Ticker coverage below normal: %d/%d (%.0%%)", successful, total, rate * 100)
        return True

    def check_data_freshness(self, latest_date: date, max_age_days: int = 3) -> bool:
        """Verify data is not stale."""
        age = (date.today() - latest_date).days
        if age > max_age_days:
            msg = f"Data is {age} days old (latest: {latest_date})"
            logger.error(msg)
            self.issues.append(msg)
            return False
        return True

    def report(self, scan_duration: float, signal_count: int) -> None:
        """Send final report: alerts for issues, summary for success."""
        if self.issues:
            alert_msg = "Scan issues detected:\n" + "\n".join(f"- {i}" for i in self.issues)
            logger.error(alert_msg)
            if self.notifier and self._should_alert("scan_issues"):
                self.notifier.send_error_alert(alert_msg)
            self.ping_failure()
        else:
            logger.info(
                "Scan healthy: duration=%.1fs, signals=%d, issues=0",
                scan_duration, signal_count,
            )
            self.ping_success()

    def _ping(self, suffix: str) -> None:
        """Ping Healthchecks.io."""
        if not self.healthcheck_url:
            return
        try:
            requests.get(f"{self.healthcheck_url}{suffix}", timeout=5)
        except requests.RequestException as e:
            logger.warning("Healthcheck ping failed: %s", e)

    def _should_alert(self, error_key: str, cooldown_hours: int = 24) -> bool:
        """Prevent duplicate alerts within cooldown period."""
        now = time.time()
        cache = {}
        if self.alert_cache_path.exists():
            try:
                cache = json.loads(self.alert_cache_path.read_text())
            except (json.JSONDecodeError, OSError):
                cache = {}

        last_alert = cache.get(error_key, 0)
        if now - last_alert < cooldown_hours * 3600:
            return False

        cache[error_key] = now
        try:
            self.alert_cache_path.write_text(json.dumps(cache))
        except OSError:
            pass
        return True
```

### Pipeline integration

```python
from monitoring import ScanMonitor
from telegram_notifier import TelegramNotifier

def run_daily_scan():
    notifier = TelegramNotifier()
    monitor = ScanMonitor(notifier)

    monitor.ping_start()
    start_time = time.time()

    try:
        # Fetch data
        results = fetch_all_tickers(OMX_LARGE_CAP_TICKERS)

        # Quality checks
        monitor.check_ticker_coverage(len(results), len(OMX_LARGE_CAP_TICKERS))
        monitor.check_data_freshness(get_latest_date(results))

        # Generate signals
        signals = generate_signals(results)

        # Notify
        for signal in signals:
            notifier.send_signal(signal)
        notifier.send_daily_summary(signals, str(date.today()))

        # Report health
        duration = time.time() - start_time
        monitor.report(duration, len(signals))

    except Exception as e:
        monitor.ping_failure()
        notifier.send_error_alert(str(e))
        raise
```

---

## 9. Operational Runbook

### Daily: automated, no action needed

The scanner runs, pings Healthchecks.io, sends signals. You only act if alerted.

### Weekly: quick check (~2 minutes)

- [ ] Glance at Healthchecks.io dashboard — all checks green?
- [ ] Review scan logs for warning patterns (increasing failed tickers?)
- [ ] Check signal count trend — unusual silence or unusual volume?

### Quarterly: ticker list update (~5 minutes)

- [ ] Check Nasdaq Nordic for Large Cap changes
- [ ] Update `config/tickers.py`
- [ ] Run `validate_tickers.py`
- [ ] Commit and deploy

### Incident response

| Symptom | First check | Likely cause | Fix |
|---------|-------------|--------------|-----|
| No Healthchecks.io ping | Container logs | Container crashed or scheduler failed | Restart container, check cron |
| Telegram alert: low coverage | Scanner logs | yfinance API issues | Wait and retry next day; if persistent, check yfinance GitHub issues |
| No signals for 5+ days | Signal history | Market conditions or strategy issue | Manual chart review; likely just a quiet market |
| Data looks wrong | Compare with Avanza | yfinance data error | Flag specific ticker, consider excluding temporarily |

---

*This completes the technical implementation research series (01-17). Next step: build Phase 1.*
