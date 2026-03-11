"""Risk management module with professional-grade controls."""

import logging
import math
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class RiskManager:
    """Professional risk management with Kelly Criterion, drawdown controls,
    dynamic stop losses, and circuit breakers."""

    def __init__(self, initial_capital: float = 100000.0):
        from src.config import Config
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_capital = initial_capital
        self.max_position_size = Config.MAX_POSITION_SIZE
        self.max_drawdown = Config.MAX_DRAWDOWN
        self.stop_loss_atr_mult = Config.STOP_LOSS_ATR_MULTIPLIER
        self.trailing_stop_pct = Config.TRAILING_STOP_PCT
        self.circuit_breaker_active = False
        self.daily_loss = 0.0
        self.daily_loss_limit = 0.03  # 3% daily loss limit

    def kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Calculate optimal position size using Kelly Criterion.

        Returns the fraction of capital to risk (capped at max_position_size).
        """
        if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0
        win_loss_ratio = avg_win / abs(avg_loss)
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
        # Use half-Kelly for safety
        half_kelly = kelly / 2.0
        return max(0.0, min(half_kelly, self.max_position_size))

    def calculate_position_size(
        self, price: float, atr: float, win_rate: float = 0.55,
        avg_win: float = 1.5, avg_loss: float = 1.0,
    ) -> int:
        """Calculate the number of shares to buy based on risk parameters."""
        if price <= 0 or self.circuit_breaker_active:
            return 0

        kelly_fraction = self.kelly_criterion(win_rate, avg_win, avg_loss)
        risk_amount = self.current_capital * kelly_fraction

        # ATR-based risk per share
        risk_per_share = atr * self.stop_loss_atr_mult
        if risk_per_share <= 0:
            return 0

        shares = int(risk_amount / risk_per_share)
        # Cap by max position size
        max_shares = int((self.current_capital * self.max_position_size) / price)
        return min(shares, max_shares)

    def calculate_stop_loss(self, entry_price: float, atr: float, direction: str = "long") -> float:
        """Calculate ATR-based dynamic stop loss."""
        stop_distance = atr * self.stop_loss_atr_mult
        if direction == "long":
            return entry_price - stop_distance
        return entry_price + stop_distance

    def calculate_trailing_stop(self, highest_price: float, direction: str = "long") -> float:
        """Calculate trailing stop based on highest price achieved."""
        if direction == "long":
            return highest_price * (1 - self.trailing_stop_pct)
        return highest_price * (1 + self.trailing_stop_pct)

    def check_drawdown(self) -> dict:
        """Check current drawdown against limits."""
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        if drawdown >= self.max_drawdown:
            self.circuit_breaker_active = True
            logger.warning(
                "CIRCUIT BREAKER ACTIVATED: Drawdown %.2f%% exceeds limit %.2f%%",
                drawdown * 100, self.max_drawdown * 100,
            )
        return {
            "current_drawdown": drawdown,
            "max_allowed": self.max_drawdown,
            "circuit_breaker": self.circuit_breaker_active,
            "peak_capital": self.peak_capital,
            "current_capital": self.current_capital,
        }

    def update_daily_pnl(self, pnl: float):
        """Update daily P&L and check daily loss limit."""
        self.daily_loss += pnl
        self.current_capital += pnl
        daily_loss_pct = abs(self.daily_loss) / self.peak_capital if self.daily_loss < 0 else 0
        if daily_loss_pct >= self.daily_loss_limit:
            self.circuit_breaker_active = True
            logger.warning("Daily loss limit reached: %.2f%%", daily_loss_pct * 100)

    def reset_daily(self):
        """Reset daily tracking (call at start of trading day)."""
        self.daily_loss = 0.0
        self.circuit_breaker_active = False
        logger.info("Daily risk counters reset")

    def assess_trade_risk(self, symbol: str, price: float, shares: int, direction: str = "long") -> dict:
        """Assess overall risk for a proposed trade."""
        total_exposure = price * shares
        exposure_pct = total_exposure / self.current_capital if self.current_capital > 0 else 1.0

        return {
            "symbol": symbol,
            "approved": not self.circuit_breaker_active and exposure_pct <= self.max_position_size,
            "exposure_pct": exposure_pct,
            "max_allowed_pct": self.max_position_size,
            "circuit_breaker": self.circuit_breaker_active,
            "direction": direction,
        }
