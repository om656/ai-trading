# Backtesting Guide

Guide to running historical news-driven backtests.

## Overview

The `NewsBacktester` replays historical news articles chronologically and
simulates trades based on sentiment signals, allowing you to measure the
historical effectiveness of news-driven strategies.

## Quick Start

```python
from src.news_backtester import NewsBacktester
from src.news_impact_analyzer import NewsArticle
from datetime import datetime, timezone

articles = [
    NewsArticle(
        title="Apple beats earnings",
        content="Apple reported record quarterly profits.",
        source="example",
        symbols=["AAPL"],
        published_at=datetime(2023, 8, 4, 20, 0, tzinfo=timezone.utc),
    ),
]

backtester = NewsBacktester(
    symbol="AAPL",
    initial_capital=10_000.0,
    position_size_pct=0.10,   # risk 10% of capital per trade
    sentiment_threshold=0.3,  # minimum |score| to trade
    hold_hours=24,             # hold each position for 24 hours
)

result = backtester.run(
    articles=articles,
    start_date="2023-01-01",
    end_date="2023-12-31",
)

print(backtester.generate_report(result))
```

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `symbol` | `"AAPL"` | Ticker symbol to backtest |
| `initial_capital` | `10000.0` | Starting capital in USD |
| `position_size_pct` | `0.10` | Fraction of capital per trade |
| `sentiment_threshold` | `0.3` | Minimum \|score\| to trade |
| `hold_hours` | `24` | Hours to hold position |

## Reading the Report

```
========================================================
BACKTEST REPORT – AAPL
Period: 2023-01-01 → 2023-12-31
========================================================
Initial Capital   : $10,000.00
Final Capital     : $11,234.56
Total Return      : +12.35%
Annualized Return : +12.35%
Sharpe Ratio      : 1.423
Max Drawdown      : 4.50%
--------------------------------------------------------
Total Trades      : 23
Win Rate          : 65.2%
Winning Trades    : 15
Losing Trades     : 8
Profit Factor     : 2.154
========================================================
```

## Performance Metrics Explained

| Metric | Good | Description |
|--------|------|-------------|
| Win Rate | > 55% | % of profitable trades |
| Sharpe Ratio | > 1.0 | Risk-adjusted return |
| Max Drawdown | < 20% | Worst peak-to-trough decline |
| Profit Factor | > 1.5 | Gross profit / gross loss |

## Price Data

The backtester uses `yfinance` to download historical price data automatically.
If `yfinance` is not installed, you can supply your own `pd.DataFrame`:

```python
import yfinance as yf
price_data = yf.Ticker("AAPL").history(start="2023-01-01", end="2023-12-31", interval="1h")

result = backtester.run(
    articles=articles,
    start_date="2023-01-01",
    end_date="2023-12-31",
    price_data=price_data,
)
```

## Running the Example

```bash
python examples/backtesting_example.py
```
