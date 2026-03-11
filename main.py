"""AI Trading System - Main Entry Point.

Supports interactive CLI mode and automated scanning mode.
Usage:
    python main.py              # Interactive command mode
    python main.py --scan       # Auto-scan watchlist
    python main.py --status     # Show system status
"""

import argparse
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_agent():
    """Create and return the AI trading agent."""
    from src.ai_agent import AITradingAgent
    from src.config import Config
    return AITradingAgent(
        paper_trading=Config.PAPER_TRADING,
        use_transformer=False,
    )


def interactive_mode(agent):
    """Run the agent in interactive command mode."""
    print("\n" + "=" * 50)
    print("  AI Trading Agent - Interactive Mode")
    print("  Type 'help' for commands, 'quit' to exit")
    print("=" * 50 + "\n")

    while True:
        try:
            command = input("trading> ").strip()
            if command.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break
            if not command:
                continue
            response = agent.process_command(command)
            print(response)
            print()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            break


def scan_mode(agent):
    """Run a single watchlist scan and print results."""
    print("Scanning watchlist for trading signals...\n")
    response = agent.process_command("scan")
    print(response)


def main():
    parser = argparse.ArgumentParser(description="AI Trading System")
    parser.add_argument("--scan", action="store_true", help="Scan watchlist for signals")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--command", "-c", type=str, help="Execute a single command")
    args = parser.parse_args()

    agent = create_agent()

    if args.status:
        print(agent.process_command("status"))
    elif args.scan:
        scan_mode(agent)
    elif args.command:
        print(agent.process_command(args.command))
    else:
        interactive_mode(agent)


if __name__ == "__main__":
    main()