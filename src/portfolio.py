"""Portfolio tracking and management."""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class Position:
    """Represents a single trading position."""

    def __init__(self, symbol: str, shares: int, entry_price: float,
                 direction: str = "long", stop_loss: float = 0.0,
                 trailing_stop: float = 0.0):
        self.symbol = symbol
        self.shares = shares
        self.entry_price = entry_price
        self.direction = direction
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop
        self.highest_price = entry_price
        self.entry_time = datetime.now()

    def unrealized_pnl(self, current_price: float) -> float:
        if self.direction == "long":
            return (current_price - self.entry_price) * self.shares
        return (self.entry_price - current_price) * self.shares

    def update_trailing_stop(self, current_price: float, trailing_pct: float):
        if self.direction == "long" and current_price > self.highest_price:
            self.highest_price = current_price
            self.trailing_stop = current_price * (1 - trailing_pct)
        elif self.direction == "short" and current_price < self.highest_price:
            self.highest_price = current_price
            self.trailing_stop = current_price * (1 + trailing_pct)

    def should_stop_out(self, current_price: float) -> bool:
        effective_stop = max(self.stop_loss, self.trailing_stop)
        if self.direction == "long":
            return current_price <= effective_stop
        # For short positions, stop out when price rises above stop level
        if self.stop_loss > 0:
            return current_price >= min(self.stop_loss, self.trailing_stop)
        return False

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "shares": self.shares,
            "entry_price": self.entry_price,
            "direction": self.direction,
            "stop_loss": self.stop_loss,
            "trailing_stop": self.trailing_stop,
            "highest_price": self.highest_price,
            "entry_time": self.entry_time.isoformat(),
        }


class Portfolio:
    """Real-time portfolio tracking with trade history."""

    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: dict[str, Position] = {}
        self.trade_history: list[dict] = []

    def open_position(self, symbol: str, shares: int, price: float,
                      direction: str = "long", stop_loss: float = 0.0) -> dict:
        """Open a new position."""
        cost = shares * price
        if cost > self.cash:
            return {"success": False, "error": "Insufficient funds", "available": self.cash}

        if symbol in self.positions:
            return {"success": False, "error": f"Position already exists for {symbol}"}

        self.cash -= cost
        self.positions[symbol] = Position(symbol, shares, price, direction, stop_loss)

        trade = {
            "action": "OPEN",
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "direction": direction,
            "timestamp": datetime.now().isoformat(),
            "cost": cost,
        }
        self.trade_history.append(trade)
        logger.info("Opened %s position: %d shares of %s at $%.2f", direction, shares, symbol, price)
        return {"success": True, "trade": trade}

    def close_position(self, symbol: str, price: float) -> dict:
        """Close an existing position."""
        if symbol not in self.positions:
            return {"success": False, "error": f"No position for {symbol}"}

        position = self.positions[symbol]
        pnl = position.unrealized_pnl(price)
        proceeds = position.shares * price
        self.cash += proceeds

        trade = {
            "action": "CLOSE",
            "symbol": symbol,
            "shares": position.shares,
            "entry_price": position.entry_price,
            "exit_price": price,
            "direction": position.direction,
            "pnl": pnl,
            "timestamp": datetime.now().isoformat(),
        }
        self.trade_history.append(trade)
        del self.positions[symbol]
        logger.info("Closed %s: PnL $%.2f", symbol, pnl)
        return {"success": True, "pnl": pnl, "trade": trade}

    def get_portfolio_value(self, prices: dict) -> float:
        """Calculate total portfolio value given current prices."""
        positions_value = sum(
            pos.shares * prices.get(sym, pos.entry_price)
            for sym, pos in self.positions.items()
        )
        return self.cash + positions_value

    def get_summary(self, prices: Optional[dict] = None) -> dict:
        """Get a summary of the portfolio state."""
        prices = prices or {}
        total_value = self.get_portfolio_value(prices)
        total_pnl = total_value - self.initial_capital
        return_pct = (total_pnl / self.initial_capital) * 100

        positions_summary = []
        for sym, pos in self.positions.items():
            current_price = prices.get(sym, pos.entry_price)
            positions_summary.append({
                **pos.to_dict(),
                "current_price": current_price,
                "unrealized_pnl": pos.unrealized_pnl(current_price),
            })

        return {
            "total_value": total_value,
            "cash": self.cash,
            "total_pnl": total_pnl,
            "return_pct": return_pct,
            "positions": positions_summary,
            "num_positions": len(self.positions),
            "total_trades": len(self.trade_history),
        }

    def get_trade_stats(self) -> dict:
        """Calculate trading statistics from history."""
        closed_trades = [t for t in self.trade_history if t["action"] == "CLOSE"]
        if not closed_trades:
            return {"total_trades": 0}

        pnls = [t["pnl"] for t in closed_trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        return {
            "total_trades": len(closed_trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": len(wins) / len(closed_trades) if closed_trades else 0,
            "avg_win": sum(wins) / len(wins) if wins else 0,
            "avg_loss": sum(losses) / len(losses) if losses else 0,
            "total_pnl": sum(pnls),
            "best_trade": max(pnls) if pnls else 0,
            "worst_trade": min(pnls) if pnls else 0,
        }
