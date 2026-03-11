"""Hybrid AI agent with LSTM-GRU ensemble model.

This module provides the legacy HybridAIAgent class that wraps the new
modular components (LSTMPredictor and Ollama LLM integration).
"""

import logging

import numpy as np
import pandas as pd
from keras.models import Sequential
from keras.layers import LSTM, GRU, Dense, Dropout, Input

logger = logging.getLogger(__name__)


class HybridAIAgent:
    """LSTM-GRU ensemble model with optional LLM decision support."""

    def __init__(self):
        self.model = self.create_ensemble_model()
        self._ollama_available = False
        self._init_ollama()

    def create_ensemble_model(self):
        model = Sequential([
            Input(shape=(None, 1)),
            LSTM(50, return_sequences=True),
            Dropout(0.2),
            GRU(50),
            Dropout(0.2),
            Dense(1),
        ])
        model.compile(optimizer="adam", loss="mean_squared_error")
        return model

    def _init_ollama(self):
        """Initialize Ollama LLM connection if available."""
        try:
            import ollama
            self._ollama = ollama
            ollama.list()
            self._ollama_available = True
            logger.info("Ollama LLM connected")
        except Exception:
            self._ollama = None
            self._ollama_available = False
            logger.info("Ollama not available; using predictions only")

    def train(self, data):
        """Train the model on the provided data."""
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        seq_len = min(10, len(data) - 1)
        if seq_len < 2:
            logger.warning("Insufficient data for training (need at least 3 samples)")
            return
        # Create sequences
        X, y = [], []
        for i in range(seq_len, len(data)):
            X.append(data[i - seq_len : i])
            y.append(data[i, 0])
        X = np.array(X)
        y = np.array(y)
        self.model.fit(X, y, epochs=10, batch_size=16, verbose=0)

    def make_decision(self, data):
        """Make a trading decision based on model prediction and optional LLM."""
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        seq_len = min(10, len(data) - 1)
        last_seq = data[-seq_len:].reshape(1, seq_len, 1)
        prediction = self.model.predict(last_seq, verbose=0)[0, 0]
        current = data[-1, 0]

        if self._ollama_available:
            try:
                response = self._ollama.chat(
                    model="llama3",
                    messages=[{
                        "role": "user",
                        "content": (
                            f"Current value: {current:.4f}, "
                            f"Predicted next: {prediction:.4f}. "
                            "Should I buy, sell, or hold? Reply in one word."
                        ),
                    }],
                )
                return response["message"]["content"]
            except Exception as e:
                logger.error("LLM decision error: %s", e)

        # Rule-based fallback
        change = (prediction - current) / current if current != 0 else 0
        if change > 0.01:
            return "BUY"
        elif change < -0.01:
            return "SELL"
        return "HOLD"


if __name__ == "__main__":
    agent = HybridAIAgent()
    dummy_data = np.random.rand(100, 1)
    agent.train(dummy_data)
    print(agent.make_decision(dummy_data))