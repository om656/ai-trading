# Main Advanced Trading System

"""
This is the main entry point for the advanced trading system.
Provides the advanced trading loop with automatic signal generation.
"""

import logging
import time

from advanced_nlp_sentiment import analyze_sentiment
from src.ai_agent import AITradingAgent
from src.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Run the advanced trading system with automated scanning."""
    agent = AITradingAgent(paper_trading=Config.PAPER_TRADING)

    print("Advanced Trading System Started")
    print(f"Mode: {'Paper' if Config.PAPER_TRADING else 'Live'} Trading")
    print(f"Watchlist: {', '.join(Config.DEFAULT_WATCHLIST)}")
    print(f"Scan interval: {Config.NEWS_POLL_INTERVAL}s")
    print("-" * 50)

    try:
        while True:
            logger.info("Running watchlist scan...")
            signals = agent.scan_watchlist()
            for signal in signals:
                sym = signal["symbol"]
                sig = signal["signal"]
                reason = signal.get("reason", "")
                logger.info("Signal: %s %s (%s)", sig, sym, reason)

                if sig in ("BUY", "STRONG_BUY", "SELL", "STRONG_SELL"):
                    result = agent.execute_trade(sym, sig, reason=reason)
                    logger.info("Trade result: %s", result.get("action"))

            # Check stop losses
            triggered = agent.executor.check_stop_losses()
            for t in triggered:
                logger.warning("Stop loss: %s", t)

            logger.info("Sleeping %ds until next scan...", Config.NEWS_POLL_INTERVAL)
            time.sleep(Config.NEWS_POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nShutting down...")
        summary = agent.get_portfolio_summary()
        print(f"Final portfolio value: ${summary['total_value']:.2f}")
        print(f"Total PnL: ${summary['total_pnl']:.2f}")


if __name__ == "__main__":
    main()
