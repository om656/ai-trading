"""
News Backtester
===============
Backtests trading strategies driven by news sentiment on historical data.

Workflow
--------
1. Load historical price data for a symbol.
2. Replay historical news articles with their published timestamps.
3. Generate buy/sell signals from the :class:`~src.news_impact_analyzer.NewsImpactAnalyzer`.
4. Simulate trades and calculate performance metrics.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_PD_OK = False
try:
    import pandas as pd
    _PD_OK = True
except ImportError:
    logger.warning("pandas not available – backtester limited functionality.")

_YF_OK = False
try:
    import yfinance as yf
    _YF_OK = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Trade:
    """Represents a simulated trade."""
    symbol: str
    direction: str          # "long" | "short"
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    pnl: float = 0.0
    pnl_pct: float = 0.0
    news_trigger: str = ""  # title of triggering article


@dataclass
class BacktestResult:
    """Aggregated results of a backtest run."""
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return_pct: float
    annualized_return_pct: float
    win_rate_pct: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    trades: list = field(default_factory=list)
    equity_curve: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Backtester
# ---------------------------------------------------------------------------

class NewsBacktester:
    """
    Event-driven backtester that replays news articles chronologically
    and simulates trades based on sentiment signals.

    Parameters
    ----------
    symbol : str
        Ticker symbol to backtest.
    initial_capital : float
        Starting capital in USD.
    position_size_pct : float
        Fraction of capital to risk per trade (0 < x ≤ 1).
    sentiment_threshold : float
        Minimum |impact_score| to trigger a trade.
    hold_hours : int
        Number of hours to hold a position before exit.
    """

    def __init__(
        self,
        symbol: str = "AAPL",
        initial_capital: float = 10_000.0,
        position_size_pct: float = 0.10,
        sentiment_threshold: float = 0.3,
        hold_hours: int = 24,
    ):
        self.symbol = symbol.upper()
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.sentiment_threshold = sentiment_threshold
        self.hold_hours = hold_hours

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        articles: list,
        start_date: str,
        end_date: str,
        price_data: Optional[object] = None,
    ) -> BacktestResult:
        """
        Execute a backtest.

        Parameters
        ----------
        articles : list[NewsArticle]
            Historical articles in any order (sorted internally).
        start_date : str
            "YYYY-MM-DD" start of backtest window.
        end_date : str
            "YYYY-MM-DD" end of backtest window.
        price_data : pd.DataFrame | None
            Pre-loaded OHLCV data. If None and yfinance is available,
            data is downloaded automatically.

        Returns
        -------
        BacktestResult
        """
        from src.news_impact_analyzer import NewsImpactAnalyzer

        prices = price_data if price_data is not None else self._download_prices(
            start_date, end_date
        )
        if prices is None or (hasattr(prices, "__len__") and len(prices) == 0):
            logger.error("No price data available for %s.", self.symbol)
            return self._empty_result(start_date, end_date)

        analyzer = NewsImpactAnalyzer(use_transformers=False)
        impacts = analyzer.analyze_batch(articles)

        # Filter to date range
        start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
        impacts = [
            i for i in impacts
            if i.article.published_at
            and start_dt <= i.article.published_at <= end_dt
        ]
        impacts.sort(key=lambda x: x.article.published_at)

        # Simulate trades
        capital = self.initial_capital
        trades: list = []
        equity_curve: list = [capital]

        for impact in impacts:
            if abs(impact.impact_score) < self.sentiment_threshold:
                continue

            entry_time = impact.article.published_at
            exit_time = entry_time + timedelta(hours=self.hold_hours)

            entry_price = self._price_at(prices, entry_time)
            exit_price = self._price_at(prices, exit_time)

            if entry_price is None or exit_price is None or entry_price == 0:
                continue

            direction = "long" if impact.direction == "bullish" else "short"
            qty = (capital * self.position_size_pct) / entry_price

            if direction == "long":
                pnl = qty * (exit_price - entry_price)
            else:
                pnl = qty * (entry_price - exit_price)

            pnl_pct = (exit_price - entry_price) / entry_price * 100
            if direction == "short":
                pnl_pct = -pnl_pct

            capital += pnl
            equity_curve.append(capital)

            trades.append(Trade(
                symbol=self.symbol,
                direction=direction,
                entry_time=entry_time,
                exit_time=exit_time,
                entry_price=entry_price,
                exit_price=exit_price,
                quantity=qty,
                pnl=round(pnl, 2),
                pnl_pct=round(pnl_pct, 4),
                news_trigger=impact.article.title[:80],
            ))

        return self._compute_metrics(
            trades=trades,
            equity_curve=equity_curve,
            start_date=start_date,
            end_date=end_date,
        )

    def generate_report(self, result: BacktestResult) -> str:
        """Return a human-readable text report of backtest results."""
        lines = [
            "=" * 60,
            f"BACKTEST REPORT – {result.symbol}",
            f"Period: {result.start_date} → {result.end_date}",
            "=" * 60,
            f"Initial Capital   : ${result.initial_capital:,.2f}",
            f"Final Capital     : ${result.final_capital:,.2f}",
            f"Total Return      : {result.total_return_pct:+.2f}%",
            f"Annualized Return : {result.annualized_return_pct:+.2f}%",
            f"Sharpe Ratio      : {result.sharpe_ratio:.3f}",
            f"Max Drawdown      : {result.max_drawdown_pct:.2f}%",
            "-" * 60,
            f"Total Trades      : {result.total_trades}",
            f"Win Rate          : {result.win_rate_pct:.1f}%",
            f"Winning Trades    : {result.winning_trades}",
            f"Losing Trades     : {result.losing_trades}",
            f"Profit Factor     : {result.profit_factor:.3f}",
            "=" * 60,
        ]
        if result.trades:
            lines.append("\nTop Trades:")
            sorted_trades = sorted(result.trades, key=lambda t: abs(t.pnl), reverse=True)
            for t in sorted_trades[:5]:
                lines.append(
                    f"  [{t.direction.upper()}] {t.entry_time.strftime('%Y-%m-%d')} "
                    f"PnL={t.pnl:+.2f} ({t.pnl_pct:+.2f}%) "
                    f"| {t.news_trigger}"
                )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _download_prices(self, start_date: str, end_date: str) -> Optional[object]:
        if not _YF_OK:
            logger.warning("yfinance not available – cannot download price data.")
            return None
        if not _PD_OK:
            return None
        try:
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(start=start_date, end=end_date, interval="1h")
            return df
        except Exception as exc:
            logger.error("Price download error for %s: %s", self.symbol, exc)
            return None

    def _price_at(self, prices, dt: datetime) -> Optional[float]:
        """Return the closing price nearest to *dt*."""
        if not _PD_OK or prices is None:
            return None
        try:
            import pandas as pd
            if prices.index.tz is None:
                idx = prices.index.tz_localize("UTC")
            else:
                idx = prices.index.tz_convert("UTC")
            pos = idx.searchsorted(dt)
            pos = min(pos, len(prices) - 1)
            return float(prices["Close"].iloc[pos])
        except Exception:
            return None

    def _compute_metrics(
        self,
        trades: list,
        equity_curve: list,
        start_date: str,
        end_date: str,
    ) -> BacktestResult:
        total = len(trades)
        winners = [t for t in trades if t.pnl > 0]
        losers = [t for t in trades if t.pnl <= 0]
        win_rate = (len(winners) / total * 100) if total else 0.0

        gross_profit = sum(t.pnl for t in winners)
        gross_loss = abs(sum(t.pnl for t in losers))
        profit_factor = (gross_profit / gross_loss) if gross_loss else float("inf")

        final_capital = equity_curve[-1] if equity_curve else self.initial_capital
        total_return = (final_capital / self.initial_capital - 1) * 100

        # Annualized return
        try:
            days = (datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date)).days
            years = max(days / 365.25, 1 / 365.25)
            ann_return = ((final_capital / self.initial_capital) ** (1 / years) - 1) * 100
        except Exception:
            ann_return = total_return

        # Sharpe ratio (daily returns)
        if len(equity_curve) > 1:
            eq = np.array(equity_curve)
            daily_rets = np.diff(eq) / eq[:-1]
            sharpe = (float(daily_rets.mean()) / float(daily_rets.std() or 1)) * np.sqrt(252)
        else:
            sharpe = 0.0

        # Max drawdown
        if equity_curve:
            eq_arr = np.array(equity_curve)
            peak = np.maximum.accumulate(eq_arr)
            dd = (eq_arr - peak) / np.where(peak == 0, 1, peak) * 100
            max_dd = float(abs(dd.min()))
        else:
            max_dd = 0.0

        return BacktestResult(
            symbol=self.symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=round(final_capital, 2),
            total_return_pct=round(total_return, 2),
            annualized_return_pct=round(ann_return, 2),
            win_rate_pct=round(win_rate, 1),
            profit_factor=round(profit_factor, 3),
            sharpe_ratio=round(sharpe, 3),
            max_drawdown_pct=round(max_dd, 2),
            total_trades=total,
            winning_trades=len(winners),
            losing_trades=len(losers),
            trades=trades,
            equity_curve=equity_curve,
        )

    def _empty_result(self, start_date: str, end_date: str) -> BacktestResult:
        return BacktestResult(
            symbol=self.symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=self.initial_capital,
            total_return_pct=0.0,
            annualized_return_pct=0.0,
            win_rate_pct=0.0,
            profit_factor=0.0,
            sharpe_ratio=0.0,
            max_drawdown_pct=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
        )
