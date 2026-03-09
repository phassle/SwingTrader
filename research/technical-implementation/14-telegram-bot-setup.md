# 14 - Telegram Bot Setup

> Research date: 2026-03-09
> Goal: Set up a Telegram bot for SwingTrader signal notifications — from BotFather creation to a complete Python integration class.
> Prerequisites: [01-tech-stack-and-architecture.md](01-tech-stack-and-architecture.md)

---

## Table of Contents

1. [Creating the Bot via BotFather](#1-creating-the-bot-via-botfather)
2. [Getting Your Chat ID](#2-getting-your-chat-id)
3. [Sending Messages with Python](#3-sending-messages-with-python)
4. [Message Formatting for Signals](#4-message-formatting-for-signals)
5. [Error Handling and Rate Limits](#5-error-handling-and-rate-limits)
6. [Complete TelegramNotifier Class](#6-complete-telegramnotifier-class)
7. [Pipeline Integration](#7-pipeline-integration)
8. [Testing Checklist](#8-testing-checklist)

---

## 1. Creating the Bot via BotFather

### Step-by-step

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Choose a display name: `SwingTrader Signals`
4. Choose a username (must end in `bot`): `swingtrader_signals_bot`
5. BotFather returns your **bot token** — looks like `7123456789:AAH1bGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9`

### Post-creation configuration

Send these commands to BotFather:

| Command | Value | Purpose |
|---------|-------|---------|
| `/setdescription` | `Daily swing trading signals for OMX Large Cap` | Shows when users first open the bot |
| `/setabouttext` | `Automated scanner for Swedish large cap stocks` | Bot profile description |
| `/setuserpic` | Upload a chart icon | Bot avatar |
| `/setcommands` | `status - Check if scanner is running` | Slash commands (optional, Phase 2+) |

### Important: Token security

- **Never commit the token to git.** Store it in `.env` (see [15-security-and-secrets-management.md](15-security-and-secrets-management.md)).
- If leaked, use `/revoke` in BotFather immediately to generate a new token.
- The token grants full control of the bot — treat it like a password.

---

## 2. Getting Your Chat ID

The bot needs a `chat_id` to know where to send messages. You can send to a private chat (just you) or a group.

### Method 1: curl (recommended)

1. Send any message to your bot in Telegram (e.g., `/start`)
2. Run:

```bash
curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates" | python3 -m json.tool
```

3. Look for `"chat": {"id": 123456789}` in the response. That number is your chat ID.

### Method 2: Python script

```python
import requests

TOKEN = "your-bot-token"
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
response = requests.get(url)
updates = response.json()

for update in updates.get("result", []):
    chat = update.get("message", {}).get("chat", {})
    print(f"Chat ID: {chat.get('id')}  Name: {chat.get('first_name', chat.get('title', 'N/A'))}")
```

### Private chat vs group

| Feature | Private chat | Group |
|---------|-------------|-------|
| Chat ID format | Positive integer (e.g., `123456789`) | Negative integer (e.g., `-1001234567890`) |
| Setup | Send `/start` to bot | Add bot to group, send a message |
| Use case | Personal notifications | Sharing signals with others |
| Recommendation | **Start here for Phase 1** | Phase 2+ if sharing with others |

---

## 3. Sending Messages with Python

### Using requests (recommended)

No additional dependencies beyond `requests` (already needed for other parts of the pipeline). This is the simplest approach and sufficient for our needs.

```python
import requests

def send_telegram_message(token: str, chat_id: str, text: str) -> bool:
    """Send a message via Telegram Bot API. Returns True on success."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    response = requests.post(url, json=payload, timeout=10)
    return response.status_code == 200
```

### Why not python-telegram-bot?

The `python-telegram-bot` library is excellent for building interactive bots (commands, menus, conversations). SwingTrader only needs to **send** messages — a one-way notification. Using the raw HTTP API via `requests` is simpler, has no extra dependencies, and is easier to understand and debug.

---

## 4. Message Formatting for Signals

Telegram supports HTML formatting in messages. Use `parse_mode: "HTML"` (not Markdown — HTML is more predictable with special characters in ticker names).

### Signal notification format

```python
def format_signal_message(signal: dict) -> str:
    """Format a buy signal for Telegram notification."""
    return (
        f"<b>BUY SIGNAL: {signal['ticker']}</b>\n"
        f"\n"
        f"Strategy: {signal['strategy']}\n"
        f"Price: {signal['close']:.2f} SEK\n"
        f"Setup quality: {signal['quality_score']}/5\n"
        f"\n"
        f"<b>Key levels:</b>\n"
        f"  Stop loss: {signal['stop_loss']:.2f} SEK ({signal['risk_pct']:.1f}%)\n"
        f"  Target: {signal['target']:.2f} SEK ({signal['reward_pct']:.1f}%)\n"
        f"  R:R ratio: {signal['rr_ratio']:.1f}\n"
        f"\n"
        f"<i>Scan date: {signal['scan_date']}</i>"
    )
```

**Rendered example:**

> **BUY SIGNAL: VOLV-B.ST**
>
> Strategy: EMA Pullback
> Price: 245.60 SEK
> Setup quality: 4/5
>
> **Key levels:**
>   Stop loss: 238.00 SEK (-3.1%)
>   Target: 268.00 SEK (+9.1%)
>   R:R ratio: 2.9
>
> *Scan date: 2026-03-09*

### Daily summary format

```python
def format_daily_summary(signals: list[dict], scan_date: str) -> str:
    """Format a daily scan summary."""
    if not signals:
        return f"<b>Daily Scan — {scan_date}</b>\n\nNo signals today. Market scanned successfully."

    header = f"<b>Daily Scan — {scan_date}</b>\n{len(signals)} signal(s) found:\n"
    lines = []
    for s in signals:
        lines.append(
            f"\n{'='*30}\n"
            f"<b>{s['ticker']}</b> — {s['strategy']}\n"
            f"Price: {s['close']:.2f} | Stop: {s['stop_loss']:.2f} | Target: {s['target']:.2f}\n"
            f"Quality: {s['quality_score']}/5 | R:R: {s['rr_ratio']:.1f}"
        )
    return header + "".join(lines)
```

### HTML tags reference

| Tag | Result | Example |
|-----|--------|---------|
| `<b>text</b>` | **Bold** | Ticker names, headers |
| `<i>text</i>` | *Italic* | Dates, notes |
| `<code>text</code>` | `Monospace` | Numbers, values |
| `<pre>text</pre>` | Code block | Tables, data dumps |
| `<a href="url">text</a>` | Link | Chart links (Phase 2+) |

---

## 5. Error Handling and Rate Limits

### Telegram API rate limits

| Limit | Value |
|-------|-------|
| Messages to same chat | ~30 per second |
| Messages to different chats | ~30 per second |
| Message length | 4096 characters |
| Bulk notifications | 30 messages/sec total |

For SwingTrader (sending 1-5 messages per day), rate limits are a non-issue. Still, handle errors gracefully.

### Retry logic

```python
import time

def send_with_retry(token: str, chat_id: str, text: str, max_retries: int = 3) -> bool:
    """Send message with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                return True

            if response.status_code == 429:  # Rate limited
                retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                time.sleep(retry_after)
                continue

            # Other error — log and retry
            response.raise_for_status()

        except requests.RequestException:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            continue

    return False
```

### Message splitting for long messages

```python
def split_message(text: str, max_length: int = 4096) -> list[str]:
    """Split a long message into chunks that respect Telegram's limit."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        # Find last newline before limit
        split_pos = text.rfind("\n", 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n")
    return chunks
```

---

## 6. Complete TelegramNotifier Class

```python
"""
telegram_notifier.py — Telegram notification integration for SwingTrader.

Usage:
    from telegram_notifier import TelegramNotifier

    notifier = TelegramNotifier()  # reads from environment
    notifier.send_signal(signal_dict)
    notifier.send_daily_summary(signals_list, "2026-03-09")
    notifier.send_error_alert("Scanner failed: connection timeout")
"""

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Sends SwingTrader notifications via Telegram Bot API."""

    MAX_MESSAGE_LENGTH = 4096
    MAX_RETRIES = 3

    def __init__(self, token: str | None = None, chat_id: str | None = None):
        self.token = token or os.environ["TELEGRAM_BOT_TOKEN"]
        self.chat_id = chat_id or os.environ["TELEGRAM_CHAT_ID"]
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_signal(self, signal: dict) -> bool:
        """Send a formatted buy signal notification."""
        message = (
            f"<b>BUY SIGNAL: {signal['ticker']}</b>\n"
            f"\n"
            f"Strategy: {signal['strategy']}\n"
            f"Price: {signal['close']:.2f} SEK\n"
            f"Setup quality: {signal['quality_score']}/5\n"
            f"\n"
            f"<b>Key levels:</b>\n"
            f"  Stop loss: {signal['stop_loss']:.2f} SEK ({signal['risk_pct']:.1f}%)\n"
            f"  Target: {signal['target']:.2f} SEK ({signal['reward_pct']:.1f}%)\n"
            f"  R:R ratio: {signal['rr_ratio']:.1f}\n"
            f"\n"
            f"<i>Scan date: {signal['scan_date']}</i>"
        )
        return self._send(message)

    def send_daily_summary(self, signals: list[dict], scan_date: str) -> bool:
        """Send a daily scan summary."""
        if not signals:
            message = f"<b>Daily Scan — {scan_date}</b>\n\nNo signals today. Market scanned successfully."
            return self._send(message)

        header = f"<b>Daily Scan — {scan_date}</b>\n{len(signals)} signal(s) found:\n"
        lines = []
        for s in signals:
            lines.append(
                f"\n{'='*30}\n"
                f"<b>{s['ticker']}</b> — {s['strategy']}\n"
                f"Price: {s['close']:.2f} | Stop: {s['stop_loss']:.2f} | Target: {s['target']:.2f}\n"
                f"Quality: {s['quality_score']}/5 | R:R: {s['rr_ratio']:.1f}"
            )
        message = header + "".join(lines)
        return self._send(message)

    def send_error_alert(self, error_message: str) -> bool:
        """Send an error alert to the admin chat."""
        message = f"<b>ALERT: SwingTrader Error</b>\n\n<code>{error_message}</code>"
        return self._send(message)

    def _send(self, text: str) -> bool:
        """Send a message with retry logic and message splitting."""
        chunks = self._split_message(text)
        for chunk in chunks:
            if not self._send_with_retry(chunk):
                return False
        return True

    def _send_with_retry(self, text: str) -> bool:
        """Send a single message with exponential backoff."""
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    },
                    timeout=10,
                )
                if response.status_code == 200:
                    return True

                if response.status_code == 429:
                    retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                    logger.warning("Telegram rate limited, retrying in %ds", retry_after)
                    time.sleep(retry_after)
                    continue

                logger.error("Telegram API error %d: %s", response.status_code, response.text)

            except requests.RequestException as e:
                logger.error("Telegram request failed (attempt %d): %s", attempt + 1, e)

            if attempt < self.MAX_RETRIES - 1:
                time.sleep(2 ** attempt)

        logger.error("Failed to send Telegram message after %d attempts", self.MAX_RETRIES)
        return False

    @staticmethod
    def _split_message(text: str, max_length: int = 4096) -> list[str]:
        """Split long messages into chunks respecting Telegram's limit."""
        if len(text) <= max_length:
            return [text]

        chunks = []
        while text:
            if len(text) <= max_length:
                chunks.append(text)
                break
            split_pos = text.rfind("\n", 0, max_length)
            if split_pos == -1:
                split_pos = max_length
            chunks.append(text[:split_pos])
            text = text[split_pos:].lstrip("\n")
        return chunks
```

---

## 7. Pipeline Integration

### How it fits in the daily scan pipeline

```python
from telegram_notifier import TelegramNotifier

def run_daily_scan():
    """Main pipeline entry point."""
    notifier = TelegramNotifier()

    try:
        # ... fetch data, calculate indicators, run strategies ...
        signals = generate_signals(indicators)

        # Send individual signal notifications
        for signal in signals:
            notifier.send_signal(signal)

        # Send daily summary
        notifier.send_daily_summary(signals, scan_date)

    except Exception as e:
        notifier.send_error_alert(str(e))
        raise
```

### Environment variables needed

```bash
TELEGRAM_BOT_TOKEN=7123456789:AAH1bGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
TELEGRAM_CHAT_ID=123456789
```

---

## 8. Testing Checklist

Before going live, verify each step:

- [ ] Bot created via BotFather, token saved to `.env`
- [ ] Chat ID retrieved and saved to `.env`
- [ ] Test message sends successfully: `TelegramNotifier().send_error_alert("Test message")`
- [ ] Signal formatting renders correctly in Telegram (bold, italic, code)
- [ ] Long message splitting works (test with >4096 char message)
- [ ] Error alert sends when pipeline throws an exception
- [ ] `.env` is in `.gitignore` — token is not committed

---

*Next: [15-security-and-secrets-management.md](15-security-and-secrets-management.md) — Protecting tokens and secrets across all environments.*
