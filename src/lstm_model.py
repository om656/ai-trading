"""LSTM prediction model for price forecasting."""

import logging
import os
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class LSTMPredictor:
    """LSTM-based price prediction model with GRU ensemble layers."""

    def __init__(self, sequence_length: int = 60, n_features: int = 7):
        from src.config import Config
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = Config.LSTM_UNITS
        self.gru_units = Config.GRU_UNITS
        self.epochs = Config.EPOCHS
        self.batch_size = Config.BATCH_SIZE
        self.model = None
        self._build_model()

    def _build_model(self):
        """Build the LSTM-GRU ensemble model."""
        try:
            from keras.layers import LSTM, GRU, Dense, Dropout, Input
            from keras.models import Sequential

            model = Sequential([
                Input(shape=(self.sequence_length, self.n_features)),
                LSTM(self.lstm_units, return_sequences=True),
                Dropout(0.2),
                GRU(self.gru_units, return_sequences=False),
                Dropout(0.2),
                Dense(32, activation="relu"),
                Dense(1),
            ])
            model.compile(optimizer="adam", loss="mean_squared_error", metrics=["mae"])
            self.model = model
            logger.info("LSTM-GRU model built successfully")
        except ImportError:
            logger.warning("TensorFlow/Keras not available; model will not be built")
            self.model = None

    def train(self, X_train: np.ndarray, y_train: np.ndarray, validation_split: float = 0.1) -> dict:
        """Train the LSTM model on prepared sequences."""
        if self.model is None:
            logger.error("Model not built; cannot train")
            return {}
        if len(X_train) == 0:
            logger.error("Empty training data")
            return {}

        history = self.model.fit(
            X_train, y_train,
            epochs=self.epochs,
            batch_size=self.batch_size,
            validation_split=validation_split,
            verbose=0,
        )
        metrics = {
            "loss": float(history.history["loss"][-1]),
            "val_loss": float(history.history.get("val_loss", [0])[-1]),
            "mae": float(history.history["mae"][-1]),
        }
        logger.info("Training complete: %s", metrics)
        return metrics

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions from input sequences."""
        if self.model is None:
            logger.error("Model not built; cannot predict")
            return np.array([])
        return self.model.predict(X, verbose=0).flatten()

    def predict_next(self, recent_sequence: np.ndarray) -> float:
        """Predict the next value from a single sequence."""
        if self.model is None:
            return 0.0
        if recent_sequence.ndim == 2:
            recent_sequence = recent_sequence.reshape(1, *recent_sequence.shape)
        pred = self.model.predict(recent_sequence, verbose=0)
        return float(pred[0, 0])

    def save_model(self, path: str = "models/lstm_model.h5"):
        """Save the trained model to disk."""
        if self.model is None:
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save(path)
        logger.info("Model saved to %s", path)

    def load_model(self, path: str = "models/lstm_model.h5"):
        """Load a trained model from disk."""
        try:
            from keras.models import load_model
            self.model = load_model(path)
            logger.info("Model loaded from %s", path)
        except Exception as e:
            logger.error("Error loading model: %s", e)

    def get_prediction_signal(self, current_price: float, predicted_price: float) -> str:
        """Convert a prediction into a trading signal."""
        change_pct = (predicted_price - current_price) / current_price
        if change_pct > 0.02:
            return "STRONG_BUY"
        elif change_pct > 0.005:
            return "BUY"
        elif change_pct < -0.02:
            return "STRONG_SELL"
        elif change_pct < -0.005:
            return "SELL"
        return "HOLD"
