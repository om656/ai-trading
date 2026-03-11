"""Configuration management for the AI Trading System."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration for the trading system."""

    # API Keys (loaded from environment variables)
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

    # Trading settings
    PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"
    INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "100000"))
    MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "0.1"))  # 10% of portfolio
    MAX_DRAWDOWN = float(os.getenv("MAX_DRAWDOWN", "0.15"))  # 15% max drawdown
    STOP_LOSS_ATR_MULTIPLIER = float(os.getenv("STOP_LOSS_ATR_MULTIPLIER", "2.0"))
    TRAILING_STOP_PCT = float(os.getenv("TRAILING_STOP_PCT", "0.05"))  # 5%

    # LSTM Model settings
    LSTM_UNITS = int(os.getenv("LSTM_UNITS", "64"))
    GRU_UNITS = int(os.getenv("GRU_UNITS", "32"))
    SEQUENCE_LENGTH = int(os.getenv("SEQUENCE_LENGTH", "60"))
    EPOCHS = int(os.getenv("EPOCHS", "50"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))

    # Sentiment settings
    SENTIMENT_THRESHOLD_BUY = float(os.getenv("SENTIMENT_THRESHOLD_BUY", "0.3"))
    SENTIMENT_THRESHOLD_SELL = float(os.getenv("SENTIMENT_THRESHOLD_SELL", "-0.3"))

    # News sources
    NEWS_SOURCES = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US",
        "https://www.investing.com/rss/news.rss",
        "https://feeds.reuters.com/reuters/businessNews",
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://feeds.marketwatch.com/marketwatch/topstories/",
    ]

    # Watchlist
    DEFAULT_WATCHLIST = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
        "META", "NVDA", "JPM", "V", "SPY",
    ]

    # Polling intervals (seconds)
    NEWS_POLL_INTERVAL = int(os.getenv("NEWS_POLL_INTERVAL", "300"))  # 5 minutes
    MARKET_POLL_INTERVAL = int(os.getenv("MARKET_POLL_INTERVAL", "60"))  # 1 minute
