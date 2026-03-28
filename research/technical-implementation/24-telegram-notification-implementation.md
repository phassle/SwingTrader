# 24 - Telegram Notification Implementation

> Research date: 2026-03-10
> Goal: Define the implementation approach for formatting trading signal recommendations into actionable Telegram messages, handling zero-signal days, managing notification failures, and logging delivery results.
> Prerequisites: [14-telegram-bot-setup.md](14-telegram-bot-setup.md), [23-signal-engine-implementation.md](23-signal-engine-implementation.md)

## Table of Contents

1. [Overview](#overview)
2. [Message Formatting Strategy](#message-formatting-strategy)
3. [Single Signal Template](#single-signal-template)
4. [Multi-Signal Template](#multi-signal-template)
5. [Zero-Signal Handling](#zero-signal-handling)
6. [Telegram API Integration](#telegram-api-integration)
7. [Error Handling and Retries](#error-handling-and-retries)
8. [Failure Isolation](#failure-isolation)
9. [Testing Strategy](#testing-strategy)
10. [Future Enhancements](#future-enhancements)

---

## Overview

The Telegram notifier is the **output layer** that delivers scan results to the user. Key responsibilities:

1. **Format recommendations** — transform Signal objects into readable messages
2. **Handle empty days** — send "No setups today" message (or remain silent)
3. **Respect Telegram limits** — 4096 characters per message, rate limits
4. **Retry failures** — handle transient network errors
5. **Isolate failures** — notification error doesn't corrupt scan data or crash scanner

**Design principles:**
- **Actionable messages:** Include entry, stop, target (no raw indicators)
- **Concise format:** Essential info only (fit 5 signals in one message)
- **Graceful degradation:** If Telegram fails, scan results still persisted
- **Observable:** Log delivery success/failure for monitoring

---

## Message Formatting Strategy

### Formatting Goals

1. **Readability:** Clear sections, consistent formatting, no clutter
2. **Actionable:** Entry price, stop loss, target explicit
3. **Context:** Strategy name, score, risk/reward ratio
4. **Scannable:** User can quickly assess quality (score first)

### Message Structure

```
📊 SwingTrader Scan Results
Date: 2026-03-10

Found 5 setups:

━━━━━━━━━━━━━━━━━━━━
🥇 ERIC.ST (Score: 24/30)
Strategy: Mean Reversion
Entry: 95.50 SEK
Stop: 91.00 SEK
Target: 102.00 SEK
Risk/Reward: 1.44:1 (4.7% risk)

🥈 VOLV-B.ST (Score: 22/30)
Strategy: MACD Crossover
Entry: 258.00 SEK
Stop: 252.00 SEK
Target: 276.00 SEK
Risk/Reward: 3:1 (2.3% risk)

[... 3 more signals ...]

━━━━━━━━━━━━━━━━━━━━
Scan duration: 45s
Data source: yfinance
```

**Key elements:**
- **Ranking indicators:** 🥇🥈🥉 (top 3)
- **Score visibility:** Shows total score (0-30 scale)
- **Price levels:** Entry, stop, target in native currency
- **Risk metrics:** R:R ratio and risk %
- **Metadata:** Scan date, duration, data source

---

## Single Signal Template

### Template Function

```python
def format_single_signal(signal, rank: int) -> str:
    """Format one signal as text block.
    
    Args:
        signal: Signal object
        rank: 1-based rank (1 = best)
    
    Returns:
        Formatted text block (no leading/trailing newlines)
    """
    
    # Rank emoji
    rank_emoji = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
    }.get(rank, "🔹")
    
    # Format price with 2 decimals
    entry = f"{signal.entry_price:.2f}"
    stop = f"{signal.stop_loss:.2f}"
    target = f"{signal.target_price:.2f}"
    
    # Risk/Reward ratio
    rr_ratio = f"{signal.risk_reward_ratio:.2f}"
    risk_pct = f"{signal.risk_percent:.1f}"
    
    # Build message block
    lines = [
        f"{rank_emoji} {signal.ticker} (Score: {signal.total_score:.0f}/30)",
        f"Strategy: {signal.strategy}",
        f"Entry: {entry} SEK",
        f"Stop: {stop} SEK",
        f"Target: {target} SEK",
        f"Risk/Reward: {rr_ratio}:1 ({risk_pct}% risk)",
    ]
    
    return "\n".join(lines)
```

**Design choices:**

1. **SEK currency:** Hardcoded for Swedish stocks (Phase 1)
2. **2 decimal precision:** Matches OMX price ticks
3. **Rank emoji only for top 3:** Others get generic bullet (🔹)
4. **Score out of 30:** Consistent with scoring framework

---

## Multi-Signal Template

### Full Message Function

```python
from datetime import datetime
from typing import List

def format_recommendations_message(
    recommendations: List[Signal],
    scan_date: datetime,
    duration_seconds: float,
) -> str:
    """Format complete scan results message.
    
    Args:
        recommendations: List of Signal objects (already ranked)
        scan_date: Date of scan
        duration_seconds: Scan execution duration
    
    Returns:
        Complete message text (ready to send)
    """
    
    if not recommendations:
        return format_zero_signals_message(scan_date)
    
    # Header
    header = [
        "📊 SwingTrader Scan Results",
        f"Date: {scan_date.strftime('%Y-%m-%d')}",
        "",
        f"Found {len(recommendations)} setup{'s' if len(recommendations) != 1 else ''}:",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
    ]
    
    # Signal blocks
    signal_blocks = []
    for i, signal in enumerate(recommendations, start=1):
        block = format_single_signal(signal, rank=i)
        signal_blocks.append(block)
    
    # Footer
    footer = [
        "━━━━━━━━━━━━━━━━━━━━",
        f"Scan duration: {duration_seconds:.0f}s",
        "Data source: yfinance",
    ]
    
    # Combine all parts
    parts = header + ["\n".join(signal_blocks)] + footer
    message = "\n\n".join(parts)
    
    return message
```

**Message structure:**
1. Header (title, date, count)
2. Separator
3. Signal blocks (joined with blank line)
4. Separator
5. Footer (metadata)

---

## Zero-Signal Handling

### Phase 1 Decision: Explicit No-Setup Message

**Rationale:**
- User expects daily notification (confirms scanner is running)
- Silence could mean scanner failed
- Explicit message = clear feedback

### Zero-Signal Message

```python
def format_zero_signals_message(scan_date: datetime) -> str:
    """Format message for days with no valid setups.
    
    Returns:
        Message indicating no setups found.
    """
    
    return (
        "📊 SwingTrader Scan Results\n"
        f"Date: {scan_date.strftime('%Y-%m-%d')}\n"
        "\n"
        "No setups found today.\n"
        "\n"
        "All signals were disqualified (low liquidity, weak trend, or poor risk/reward).\n"
        "\n"
        "Check again tomorrow! 🔍"
    )
```

**Alternative (Phase 2):** Silent mode (skip notification if zero signals).

**Configuration:**
```python
# In ScannerConfig
notify_on_zero_signals: bool = True  # Default: send message
```

---

## Telegram API Integration

### TelegramNotifier Class

```python
import requests
import logging
from typing import List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NotificationResult:
    """Result of sending notification."""
    success: bool
    error_message: str | None = None

class TelegramNotifier:
    """Sends formatted messages to Telegram."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_base = f"https://api.telegram.org/bot{bot_token}"
    
    def send_recommendations(
        self,
        recommendations: List[Signal],
        scan_date: datetime,
        duration_seconds: float,
    ) -> NotificationResult:
        """Send scan results to Telegram.
        
        Returns NotificationResult with success/failure status.
        """
        
        try:
            # Format message
            message = format_recommendations_message(
                recommendations,
                scan_date,
                duration_seconds,
            )
            
            # Send to Telegram
            result = self._send_message(message)
            
            if result.success:
                logger.info("Telegram notification sent successfully", extra={
                    "signal_count": len(recommendations),
                    "message_length": len(message),
                })
            else:
                logger.error(f"Telegram notification failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error("Failed to send Telegram notification", exc_info=True)
            return NotificationResult(success=False, error_message=str(e))
    
    def _send_message(self, text: str) -> NotificationResult:
        """Send text message via Telegram API.
        
        Returns NotificationResult.
        """
        
        # Check message length (Telegram limit: 4096 chars)
        if len(text) > 4096:
            logger.warning(f"Message too long ({len(text)} chars), truncating")
            text = text[:4093] + "..."
        
        # Build API request
        url = f"{self.api_base}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",  # Optional: enable HTML formatting
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return NotificationResult(success=True)
            else:
                error_msg = response.json().get("description", "Unknown error")
                return NotificationResult(success=False, error_message=error_msg)
                
        except requests.RequestException as e:
            return NotificationResult(success=False, error_message=str(e))
```

**Key patterns:**

1. **Length check:** Truncate if > 4096 chars (unlikely with 5 signals)
2. **Timeout:** 10-second timeout for API call
3. **Error handling:** Catch network errors, return structured result
4. **Structured logging:** Log success/failure with metadata

---

## Error Handling and Retries

### Retry Strategy

**Transient errors** (retry):
- Network timeout
- 500 Internal Server Error
- 429 Too Many Requests (rate limit)

**Permanent errors** (don't retry):
- 400 Bad Request (invalid chat_id or token)
- 403 Forbidden (bot blocked by user)
- 404 Not Found (invalid bot token)

### Retry Implementation

```python
import time

def _send_message_with_retry(self, text: str, max_retries: int = 3) -> NotificationResult:
    """Send message with retry logic for transient failures.
    
    Returns NotificationResult.
    """
    
    for attempt in range(max_retries):
        result = self._send_message(text)
        
        if result.success:
            return result
        
        # Check if error is retryable
        if "timeout" in result.error_message.lower() or "500" in result.error_message:
            backoff = 2 ** attempt  # 1s, 2s, 4s
            logger.warning(f"Transient error, retrying after {backoff}s (attempt {attempt + 1})")
            time.sleep(backoff)
        else:
            # Permanent error, don't retry
            logger.error(f"Permanent error, not retrying: {result.error_message}")
            return result
    
    return NotificationResult(
        success=False,
        error_message=f"Failed after {max_retries} retries",
    )
```

---

## Failure Isolation

### Design Principle: Notification Failure Must Not Crash Scanner

**Problem without isolation:**
```python
# BAD: Notification failure crashes entire scan
notifier.send_recommendations(recommendations, scan_date, duration)
# If this raises exception, scan_runs not updated, scanner exits with error
```

**Solution with isolation:**
```python
# GOOD: Notification failure logged, scan continues
try:
    result = notifier.send_recommendations(recommendations, scan_date, duration)
    notification_sent = result.success
except Exception as e:
    logger.error("Notification failed, continuing scan", exc_info=True)
    notification_sent = False

# Update scan_runs with notification status
repository.scan_runs.update_scan_run(scan_run_id, {
    "notification_sent": notification_sent,
    "status": "completed",
})
```

**Why this matters:**
- Telegram API down → scanner still completes, results in Cosmos
- User can query Cosmos directly if notifications fail
- Separate notification retries from scan execution

---

## Testing Strategy

### Unit Tests

```python
# tests/test_notifier.py
from scanner.notifier import format_single_signal, format_recommendations_message
from datetime import datetime, date

def test_format_single_signal():
    """Test signal formatting."""
    signal = Signal(
        ticker="ERIC.ST",
        date=date(2026, 3, 10),
        strategy="Mean Reversion",
        entry_price=95.50,
        stop_loss=91.00,
        target_price=102.00,
        risk_reward_ratio=1.44,
        risk_percent=4.7,
        total_score=24,
        # ... other fields
    )
    
    text = format_single_signal(signal, rank=1)
    
    assert "🥇 ERIC.ST" in text
    assert "Score: 24/30" in text
    assert "Entry: 95.50 SEK" in text
    assert "Stop: 91.00 SEK" in text
    assert "Target: 102.00 SEK" in text
    assert "Risk/Reward: 1.44:1" in text

def test_format_zero_signals():
    """Test zero-signal message."""
    message = format_zero_signals_message(datetime(2026, 3, 10))
    
    assert "No setups found today" in message
    assert "2026-03-10" in message
```

### Integration Test (Mock Telegram API)

```python
import responses

@responses.activate
def test_send_message_success():
    """Test successful Telegram API call."""
    # Mock Telegram API
    responses.add(
        responses.POST,
        "https://api.telegram.org/bot123:ABC/sendMessage",
        json={"ok": True, "result": {"message_id": 123}},
        status=200,
    )
    
    notifier = TelegramNotifier(bot_token="123:ABC", chat_id="987654321")
    result = notifier._send_message("Test message")
    
    assert result.success is True

@responses.activate
def test_send_message_rate_limit():
    """Test rate limit handling."""
    responses.add(
        responses.POST,
        "https://api.telegram.org/bot123:ABC/sendMessage",
        json={"ok": False, "description": "Too Many Requests"},
        status=429,
    )
    
    notifier = TelegramNotifier(bot_token="123:ABC", chat_id="987654321")
    result = notifier._send_message("Test message")
    
    assert result.success is False
    assert "Too Many Requests" in result.error_message
```

---

## Future Enhancements

### Phase 2: Rich Formatting

**HTML formatting** (Telegram supports):
```python
text = (
    f"<b>{signal.ticker}</b> (Score: {signal.total_score}/30)\n"
    f"<i>Strategy:</i> {signal.strategy}\n"
    f"<code>Entry: {entry} SEK</code>\n"
    # ...
)
```

**Benefits:** Bold tickers, italic labels, monospace prices.

---

### Phase 3: Interactive Buttons

**Inline keyboard** (Telegram Bot API):
```python
payload = {
    "chat_id": self.chat_id,
    "text": message,
    "reply_markup": {
        "inline_keyboard": [
            [{"text": "View Details", "url": f"https://finance.yahoo.com/quote/{signal.ticker}"}],
            [{"text": "Dismiss", "callback_data": "dismiss"}],
        ]
    }
}
```

**Benefits:** Quick links to Yahoo Finance, TradingView, etc.

---

### Phase 4: Charts/Images

**Send chart image** (via imgkit, matplotlib):
```python
# Generate candlestick chart
chart_path = generate_chart(signal.ticker, signal.date)

# Send as photo
url = f"{self.api_base}/sendPhoto"
files = {"photo": open(chart_path, "rb")}
data = {"chat_id": self.chat_id, "caption": f"Chart for {signal.ticker}"}
requests.post(url, files=files, data=data)
```

**Benefits:** Visual confirmation of setup.

---

## Summary

### Key Decisions

1. **Concise message format** — essential info only (fit 5 signals comfortably)
2. **Explicit zero-signal message** — confirms scanner is running
3. **Retry transient failures** — handle network errors gracefully
4. **Isolate notification failures** — don't crash scan if Telegram down
5. **Structured logging** — track delivery success/failure for monitoring

### What This Enables

- **Actionable notifications:** User can trade immediately (entry, stop, target clear)
- **Reliable delivery:** Retry transient failures, log permanent failures
- **Observable:** Notification success tracked in scan_runs, logs
- **Graceful degradation:** Scanner completes even if Telegram fails

### Next Steps

1. **Document local development workflow** → [25-local-development-workflow.md](25-local-development-workflow.md)
2. **Build Azure deployment guide** → [26-azure-containerization-and-azd.md](26-azure-containerization-and-azd.md)
3. **Test end-to-end locally** → Run complete scan, verify Telegram notification

---

## References

- [Telegram Bot API documentation](https://core.telegram.org/bots/api)
- [14-telegram-bot-setup.md](14-telegram-bot-setup.md) — Bot creation and integration
- [23-signal-engine-implementation.md](23-signal-engine-implementation.md) — Signal structure
- [17-monitoring-and-alerting.md](17-monitoring-and-alerting.md) — Observability patterns
