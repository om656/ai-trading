"""Text command processor for the AI trading agent."""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class CommandProcessor:
    """Processes text commands and routes them to the appropriate agent actions."""

    COMMANDS = {
        "buy": "Execute a buy order. Usage: buy <SYMBOL> [shares]",
        "sell": "Execute a sell order. Usage: sell <SYMBOL>",
        "analyze": "Analyze a symbol. Usage: analyze <SYMBOL>",
        "sentiment": "Get sentiment for a symbol. Usage: sentiment <SYMBOL>",
        "predict": "Get LSTM prediction. Usage: predict <SYMBOL>",
        "portfolio": "Show portfolio summary.",
        "positions": "Show open positions.",
        "history": "Show trade history.",
        "stats": "Show trading statistics.",
        "risk": "Show risk status.",
        "watch": "Add symbol to watchlist. Usage: watch <SYMBOL>",
        "unwatch": "Remove from watchlist. Usage: unwatch <SYMBOL>",
        "price": "Get current price. Usage: price <SYMBOL>",
        "scan": "Scan watchlist for signals.",
        "help": "Show available commands.",
        "status": "Show system status.",
        "ask": "Ask the AI a question. Usage: ask <question>",
    }

    def __init__(self, agent):
        self.agent = agent

    def process(self, command_text: str) -> str:
        """Process a text command and return a response."""
        command_text = command_text.strip()
        if not command_text:
            return "Empty command. Type 'help' for available commands."

        parts = command_text.split(maxsplit=2)
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        handler = getattr(self, f"_cmd_{cmd}", None)
        if handler:
            return handler(args)

        # If no exact command match, treat as a question to the AI
        return self._cmd_ask([command_text])

    def _cmd_help(self, args: list) -> str:
        lines = ["Available Commands:", "=" * 40]
        for cmd, desc in self.COMMANDS.items():
            lines.append(f"  {cmd:12s} - {desc}")
        return "\n".join(lines)

    def _cmd_buy(self, args: list) -> str:
        if not args:
            return "Usage: buy <SYMBOL> [shares]"
        symbol = args[0].upper()
        result = self.agent.execute_trade(symbol, "BUY", reason="Manual buy command")
        return self._format_trade_result(result)

    def _cmd_sell(self, args: list) -> str:
        if not args:
            return "Usage: sell <SYMBOL>"
        symbol = args[0].upper()
        result = self.agent.execute_trade(symbol, "SELL", reason="Manual sell command")
        return self._format_trade_result(result)

    def _cmd_analyze(self, args: list) -> str:
        if not args:
            return "Usage: analyze <SYMBOL>"
        symbol = args[0].upper()
        analysis = self.agent.analyze_symbol(symbol)
        return self._format_analysis(analysis)

    def _cmd_sentiment(self, args: list) -> str:
        if not args:
            return "Usage: sentiment <SYMBOL>"
        symbol = args[0].upper()
        result = self.agent.get_sentiment(symbol)
        return f"Sentiment for {symbol}: {result['label']} (score: {result['score']:.3f})"

    def _cmd_predict(self, args: list) -> str:
        if not args:
            return "Usage: predict <SYMBOL>"
        symbol = args[0].upper()
        prediction = self.agent.predict_price(symbol)
        return self._format_prediction(prediction)

    def _cmd_portfolio(self, args: list) -> str:
        summary = self.agent.get_portfolio_summary()
        return self._format_portfolio(summary)

    def _cmd_positions(self, args: list) -> str:
        summary = self.agent.get_portfolio_summary()
        positions = summary.get("positions", [])
        if not positions:
            return "No open positions."
        lines = ["Open Positions:", "-" * 50]
        for pos in positions:
            pnl = pos.get("unrealized_pnl", 0)
            lines.append(
                f"  {pos['symbol']:6s} | {pos['shares']} shares @ ${pos['entry_price']:.2f} "
                f"| Current: ${pos.get('current_price', 0):.2f} | PnL: ${pnl:.2f}"
            )
        return "\n".join(lines)

    def _cmd_history(self, args: list) -> str:
        history = self.agent.portfolio.trade_history
        if not history:
            return "No trade history."
        lines = ["Trade History:", "-" * 60]
        for trade in history[-20:]:  # Last 20 trades
            ts = str(trade.get("timestamp", ""))[:19]
            lines.append(
                f"  {ts} | {trade['action']:5s} | "
                f"{trade['symbol']:6s} | {trade.get('shares', 0)} shares @ "
                f"${trade.get('price', trade.get('exit_price', 0)):.2f}"
            )
        return "\n".join(lines)

    def _cmd_stats(self, args: list) -> str:
        stats = self.agent.portfolio.get_trade_stats()
        if stats.get("total_trades", 0) == 0:
            return "No completed trades yet."
        return (
            f"Trading Statistics:\n"
            f"  Total trades: {stats['total_trades']}\n"
            f"  Win rate: {stats['win_rate']:.1%}\n"
            f"  Avg win: ${stats['avg_win']:.2f}\n"
            f"  Avg loss: ${stats['avg_loss']:.2f}\n"
            f"  Total PnL: ${stats['total_pnl']:.2f}\n"
            f"  Best trade: ${stats['best_trade']:.2f}\n"
            f"  Worst trade: ${stats['worst_trade']:.2f}"
        )

    def _cmd_risk(self, args: list) -> str:
        dd = self.agent.risk_manager.check_drawdown()
        return (
            f"Risk Status:\n"
            f"  Current drawdown: {dd['current_drawdown']:.2%}\n"
            f"  Max allowed: {dd['max_allowed']:.2%}\n"
            f"  Circuit breaker: {'ACTIVE' if dd['circuit_breaker'] else 'OFF'}\n"
            f"  Peak capital: ${dd['peak_capital']:.2f}\n"
            f"  Current capital: ${dd['current_capital']:.2f}"
        )

    def _cmd_price(self, args: list) -> str:
        if not args:
            return "Usage: price <SYMBOL>"
        symbol = args[0].upper()
        data = self.agent.market_data.get_realtime_price(symbol)
        if "error" in data:
            return f"Error getting price for {symbol}: {data['error']}"
        return f"{symbol}: ${data['price']:.2f} (prev close: ${data['previous_close']:.2f})"

    def _cmd_watch(self, args: list) -> str:
        if not args:
            return f"Current watchlist: {', '.join(self.agent.market_data.watchlist)}"
        symbol = args[0].upper()
        if symbol not in self.agent.market_data.watchlist:
            self.agent.market_data.watchlist.append(symbol)
        return f"Added {symbol} to watchlist. Current: {', '.join(self.agent.market_data.watchlist)}"

    def _cmd_unwatch(self, args: list) -> str:
        if not args:
            return "Usage: unwatch <SYMBOL>"
        symbol = args[0].upper()
        if symbol in self.agent.market_data.watchlist:
            self.agent.market_data.watchlist.remove(symbol)
            return f"Removed {symbol} from watchlist."
        return f"{symbol} not in watchlist."

    def _cmd_scan(self, args: list) -> str:
        signals = self.agent.scan_watchlist()
        if not signals:
            return "No signals found."
        lines = ["Watchlist Scan Results:", "-" * 50]
        for sig in signals:
            lines.append(f"  {sig['symbol']:6s} | Signal: {sig['signal']:12s} | Reason: {sig.get('reason', 'N/A')}")
        return "\n".join(lines)

    def _cmd_status(self, args: list) -> str:
        return self.agent.get_status()

    def _cmd_ask(self, args: list) -> str:
        if not args:
            return "Usage: ask <question>"
        question = " ".join(args)
        return self.agent.ask_llm(question)

    @staticmethod
    def _format_trade_result(result: dict) -> str:
        action = result.get("action", "UNKNOWN")
        symbol = result.get("symbol", "")
        if action == "BUY":
            return (
                f"BUY {result.get('shares', 0)} shares of {symbol} "
                f"at ${result.get('price', 0):.2f} | Stop: ${result.get('stop_loss', 0):.2f}"
            )
        elif action == "SELL":
            pnl = result.get("result", {}).get("pnl", 0)
            return f"SOLD {symbol} at ${result.get('price', 0):.2f} | PnL: ${pnl:.2f}"
        elif action == "BLOCKED":
            return f"Trade BLOCKED for {symbol}: {result.get('reason', 'Unknown')}"
        elif action == "HOLD":
            return f"HOLD {symbol}: {result.get('reason', '')}"
        return f"{action} {symbol}: {result}"

    @staticmethod
    def _format_analysis(analysis: dict) -> str:
        lines = [
            f"Analysis for {analysis.get('symbol', 'N/A')}:",
            f"  Price: ${analysis.get('price', 0):.2f}",
            f"  Sentiment: {analysis.get('sentiment', {}).get('label', 'N/A')} "
            f"({analysis.get('sentiment', {}).get('score', 0):.3f})",
            f"  LSTM Signal: {analysis.get('lstm_signal', 'N/A')}",
            f"  Combined Signal: {analysis.get('combined_signal', 'N/A')}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _format_prediction(prediction: dict) -> str:
        if "error" in prediction:
            return f"Prediction error: {prediction['error']}"
        return (
            f"LSTM Prediction for {prediction.get('symbol', 'N/A')}:\n"
            f"  Current price: ${prediction.get('current_price', 0):.2f}\n"
            f"  Predicted: ${prediction.get('predicted_price', 0):.2f}\n"
            f"  Change: {prediction.get('change_pct', 0):.2%}\n"
            f"  Signal: {prediction.get('signal', 'N/A')}"
        )

    @staticmethod
    def _format_portfolio(summary: dict) -> str:
        return (
            f"Portfolio Summary:\n"
            f"  Total value: ${summary.get('total_value', 0):.2f}\n"
            f"  Cash: ${summary.get('cash', 0):.2f}\n"
            f"  Total PnL: ${summary.get('total_pnl', 0):.2f}\n"
            f"  Return: {summary.get('return_pct', 0):.2f}%\n"
            f"  Open positions: {summary.get('num_positions', 0)}\n"
            f"  Total trades: {summary.get('total_trades', 0)}"
        )
