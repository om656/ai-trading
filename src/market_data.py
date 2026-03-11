"""Market data fetcher using yfinance."""

import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketData:
    """Fetches and processes market data from Yahoo Finance."""

    def __init__(self, watchlist: Optional[list] = None):
        from src.config import Config
        self.watchlist = watchlist or Config.DEFAULT_WATCHLIST
        self._cache = {}

    def get_historical_data(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                logger.warning("No data returned for %s", symbol)
                return pd.DataFrame()
            df.index = pd.to_datetime(df.index)
            self._cache[symbol] = df
            return df
        except Exception as e:
            logger.error("Error fetching data for %s: %s", symbol, e)
            return pd.DataFrame()

    def get_realtime_price(self, symbol: str) -> dict:
        """Get real-time price data for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            return {
                "symbol": symbol,
                "price": float(info.last_price) if hasattr(info, "last_price") else 0.0,
                "previous_close": float(info.previous_close) if hasattr(info, "previous_close") else 0.0,
                "market_cap": float(info.market_cap) if hasattr(info, "market_cap") else 0.0,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error("Error fetching real-time price for %s: %s", symbol, e)
            return {"symbol": symbol, "price": 0.0, "error": str(e)}

    def calculate_atr(self, symbol: str, period: int = 14) -> float:
        """Calculate Average True Range for dynamic stop losses."""
        df = self._cache.get(symbol)
        if df is None or len(df) < period + 1:
            df = self.get_historical_data(symbol, period="3mo")
        if df.empty or len(df) < period + 1:
            return 0.0
        high = df["High"].values
        low = df["Low"].values
        close = df["Close"].values
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1]),
            ),
        )
        atr = np.mean(tr[-period:])
        return float(atr)

    def get_correlation_matrix(self, symbols: Optional[list] = None, period: str = "1y") -> pd.DataFrame:
        """Calculate correlation matrix for portfolio symbols."""
        symbols = symbols or self.watchlist
        close_data = {}
        for symbol in symbols:
            df = self.get_historical_data(symbol, period=period)
            if not df.empty:
                close_data[symbol] = df["Close"]
        if not close_data:
            return pd.DataFrame()
        combined = pd.DataFrame(close_data).dropna()
        return combined.pct_change().dropna().corr()

    def prepare_lstm_features(self, symbol: str, sequence_length: int = 60) -> tuple:
        """Prepare feature sequences for LSTM model input.

        Returns (X, y, scaler) tuple where X has shape (samples, sequence_length, features).
        """
        from sklearn.preprocessing import MinMaxScaler

        df = self.get_historical_data(symbol, period="2y")
        if df.empty or len(df) < sequence_length + 1:
            return np.array([]), np.array([]), None

        # Feature engineering
        df = df.copy()
        df["Returns"] = df["Close"].pct_change()
        df["MA_10"] = df["Close"].rolling(10).mean()
        df["MA_50"] = df["Close"].rolling(50).mean()
        df["Volatility"] = df["Returns"].rolling(20).std()
        df["RSI"] = self._compute_rsi(df["Close"])
        df.dropna(inplace=True)

        features = df[["Close", "Volume", "Returns", "MA_10", "MA_50", "Volatility", "RSI"]].values
        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(features)

        X, y = [], []
        for i in range(sequence_length, len(scaled)):
            X.append(scaled[i - sequence_length : i])
            y.append(scaled[i, 0])  # Predict scaled close price

        return np.array(X), np.array(y), scaler

    @staticmethod
    def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.finfo(float).eps)
        return 100 - (100 / (1 + rs))
