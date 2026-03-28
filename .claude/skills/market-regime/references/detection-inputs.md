# Regime Detection Inputs

Detailed monitoring table for classifying which regime the market is in.

| Input | Regime A (Orderly) | Regime B (Volatile) | Regime C (Choppy) | Regime D (Panic) |
|-------|----------|----------|----------|----------|
| **MA slope** | Rising 20>50>200 | Trend but choppy | Flat/intertwined | Varies |
| **ADX** | 25-40 | 15-25 or <15 | <20 | Low-variable |
| **VIX** | 15-20 | 20-30 | <18 | >30 |
| **Breakout hold** | >60% | <60% | <50% | Unreliable |
| **Breadth (% >50MA)** | >70% | 50-70% | <50% | Spike up/down |
| **Sector harmony** | 3-4 aligned | Mixed | Scattered | Binary |
| **Gap frequency** | Normal | 2-3x normal | Normal | Nightly |
| **Intraday reversals** | Mild | Sharp | Whipsaws | Violent |

## How to Use This Table

1. Check each row against current market data
2. Count which regime column has the most matches
3. If split between two regimes, use the more conservative one (lower sizing)
4. Re-evaluate weekly or when a major input shifts suddenly
