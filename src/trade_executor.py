"""Trade execution module for paper and live trading."""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class TradeExecutor:
    """Executes trades through paper trading or live exchange connections."""

    def __init__(self, portfolio, risk_manager, market_data, paper_trading: bool = True):
        self.portfolio = portfolio
        self.risk_manager = risk_manager
        self.market_data = market_data
        self.paper_trading = paper_trading
        self.pending_orders = []

    def execute_signal(self, symbol: str, signal: str, reason: str = "") -> dict:
        """Execute a trading signal (BUY/SELL/HOLD)."""
        if signal == "HOLD":
            return {"action": "HOLD", "symbol": symbol, "reason": reason}

        price_data = self.market_data.get_realtime_price(symbol)
        price = price_data.get("price", 0)
        if price <= 0:
            return {"action": "ERROR", "symbol": symbol, "error": "Could not get price"}

        if signal in ("BUY", "STRONG_BUY"):
            return self._execute_buy(symbol, price, reason)
        elif signal in ("SELL", "STRONG_SELL"):
            return self._execute_sell(symbol, price, reason)

        return {"action": "UNKNOWN", "signal": signal}

    def _execute_buy(self, symbol: str, price: float, reason: str) -> dict:
        """Execute a buy order."""
        atr = self.market_data.calculate_atr(symbol)
        shares = self.risk_manager.calculate_position_size(price, atr)
        if shares <= 0:
            return {
                "action": "BLOCKED",
                "symbol": symbol,
                "reason": "Risk manager blocked trade (position size = 0)",
            }

        # Risk assessment
        assessment = self.risk_manager.assess_trade_risk(symbol, price, shares)
        if not assessment["approved"]:
            return {"action": "BLOCKED", "symbol": symbol, "reason": "Risk assessment failed", "details": assessment}

        stop_loss = self.risk_manager.calculate_stop_loss(price, atr)

        if self.paper_trading:
            result = self.portfolio.open_position(symbol, shares, price, "long", stop_loss)
        else:
            result = self._live_buy(symbol, shares, price)

        if result.get("success"):
            logger.info("BUY %d shares of %s at $%.2f | Reason: %s", shares, symbol, price, reason)

        return {
            "action": "BUY",
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "stop_loss": stop_loss,
            "reason": reason,
            "result": result,
        }

    def _execute_sell(self, symbol: str, price: float, reason: str) -> dict:
        """Execute a sell order (close position)."""
        if symbol not in self.portfolio.positions:
            return {"action": "NO_POSITION", "symbol": symbol, "reason": "No position to sell"}

        if self.paper_trading:
            result = self.portfolio.close_position(symbol, price)
        else:
            result = self._live_sell(symbol, price)

        if result.get("success"):
            self.risk_manager.update_daily_pnl(result.get("pnl", 0))
            logger.info("SELL %s at $%.2f | PnL: $%.2f | Reason: %s",
                        symbol, price, result.get("pnl", 0), reason)

        return {
            "action": "SELL",
            "symbol": symbol,
            "price": price,
            "reason": reason,
            "result": result,
        }

    def _live_buy(self, symbol: str, shares: int, price: float) -> dict:
        """Execute a live buy order via exchange API."""
        logger.warning("Live trading not yet configured. Use paper trading.")
        return {"success": False, "error": "Live trading not configured"}

    def _live_sell(self, symbol: str, price: float) -> dict:
        """Execute a live sell order via exchange API."""
        logger.warning("Live trading not yet configured. Use paper trading.")
        return {"success": False, "error": "Live trading not configured"}

    def check_stop_losses(self) -> list:
        """Check all positions for stop loss triggers."""
        triggered = []
        for symbol, position in list(self.portfolio.positions.items()):
            price_data = self.market_data.get_realtime_price(symbol)
            price = price_data.get("price", 0)
            if price <= 0:
                continue

            # Update trailing stop
            position.update_trailing_stop(price, self.risk_manager.trailing_stop_pct)

            if position.should_stop_out(price):
                result = self._execute_sell(symbol, price, "Stop loss triggered")
                triggered.append(result)
                logger.warning("STOP LOSS triggered for %s at $%.2f", symbol, price)

        return triggered
