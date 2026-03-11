# Sentiment Charts Guide

Guide to generating sentiment visualizations.

## Overview

The `sentiment_charts` module provides six chart types for analyzing sentiment data.

## Requirements

```bash
pip install matplotlib seaborn
```

## Available Charts

### 1. Sentiment Over Time
Line chart with color-coded points.

```python
from src.sentiment_charts import plot_sentiment_over_time

plot_sentiment_over_time(
    timestamps=timestamps,
    scores=scores,
    symbol="AAPL",
    save_path="sentiment_over_time.png",
)
```

### 2. Sentiment by Symbol
Horizontal bar chart comparing symbols.

```python
from src.sentiment_charts import plot_sentiment_by_symbol

plot_sentiment_by_symbol(
    symbol_scores={"AAPL": 0.42, "TSLA": -0.25, "NVDA": 0.67},
    save_path="by_symbol.png",
)
```

### 3. Sentiment vs Price
Dual-axis chart overlaying sentiment and price.

```python
from src.sentiment_charts import plot_sentiment_vs_price

plot_sentiment_vs_price(
    timestamps=timestamps,
    sentiment_scores=scores,
    prices=prices,
    symbol="AAPL",
    save_path="vs_price.png",
)
```

### 4. Sentiment Heatmap
Grid showing sentiment across symbols and dates.

```python
import numpy as np
from src.sentiment_charts import plot_sentiment_heatmap

plot_sentiment_heatmap(
    symbols=["AAPL", "TSLA", "MSFT"],
    dates=dates,
    scores=np.array([[0.4, -0.2, 0.1], [0.6, 0.3, -0.5], [-0.1, 0.2, 0.4]]),
    save_path="heatmap.png",
)
```

### 5. Sentiment Distribution
Histogram showing distribution of scores.

```python
from src.sentiment_charts import plot_sentiment_distribution

plot_sentiment_distribution(
    scores=scores,
    symbol="AAPL",
    save_path="distribution.png",
)
```

### 6. Sentiment Strength Over Time
Rolling mean with confidence bands.

```python
from src.sentiment_charts import plot_sentiment_strength_over_time

plot_sentiment_strength_over_time(
    timestamps=timestamps,
    scores=scores,
    window=7,
    symbol="AAPL",
    save_path="strength.png",
)
```

## Running the Example

```bash
python examples/sentiment_charts_example.py
```

Charts are saved to `/tmp/sentiment_charts/`.

## Chart Colors

| Color | Meaning |
|-------|---------|
| 🟢 Green (`#2ecc71`) | Positive sentiment (score > 0.05) |
| 🔴 Red (`#e74c3c`) | Negative sentiment (score < -0.05) |
| ⚫ Grey (`#95a5a6`) | Neutral sentiment |
| 🔵 Blue (`#3498db`) | Rolling/aggregate values |
