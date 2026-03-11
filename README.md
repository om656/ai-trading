# AI Trading System

## Overview
AI-powered trading platform combining LSTM deep learning, sentiment analysis, and LLM reasoning (via Ollama/LLaMA) for intelligent trade decisions. Supports paper trading, real-time market data via yfinance, and an interactive text command interface.

## Features

### Core Trading
- **Real-time market data** via yfinance (prices, OHLCV, ATR, RSI)
- **Sentiment analysis** (VADER + optional FinBERT transformer)
- **LSTM-GRU price prediction** (deep learning ensemble model)
- **Automatic signal generation** (combined LSTM + sentiment)
- **Trade execution** (paper & live modes)
- **Risk management** (Kelly Criterion, drawdown controls, circuit breakers)
- **Portfolio tracking** (real-time positions and P&L)

### AI & Machine Learning
- **LSTM-GRU ensemble model** for price forecasting
- **Multi-feature engineering** (returns, moving averages, volatility, RSI)
- **LLM integration** via Ollama (LLaMA, Mistral, etc.) for natural language reasoning
- **Text command interface** for interactive trading

### Risk Management
- **Kelly Criterion** optimal position sizing
- **ATR-based dynamic stop losses**
- **Trailing stops** (profit protection)
- **Drawdown controls** with circuit breakers
- **Daily loss limits**
- **Position exposure limits**

### Analysis & Monitoring
- **News sentiment analysis** (NewsAPI + RSS feeds)
- **Watchlist scanning** with signal generation
- **Correlation analysis** (multi-asset)
- **Trade history** and statistics
- **System status dashboard**

## Requirements
- Python 3.10+
- 4GB RAM (minimum)
- 2GB disk space
- Internet connection
- GPU optional (20-50x faster for LSTM training)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/om656/ai-trading.git
   cd ai-trading
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration**: Create a `.env` file with your settings:
   ```bash
   NEWS_API_KEY=your_newsapi_key
   PAPER_TRADING=true
   INITIAL_CAPITAL=100000
   OLLAMA_MODEL=llama3
   ```

4. **(Optional) Install Ollama** for LLM reasoning:
   ```bash
   # See https://ollama.ai for installation
   ollama run llama3
   ```

## Usage

### Interactive Mode
```bash
python main.py
```

### Commands
| Command | Description |
|---------|-------------|
| `buy AAPL` | Buy shares of AAPL |
| `sell AAPL` | Sell position in AAPL |
| `analyze AAPL` | Full analysis (sentiment + LSTM + LLM) |
| `predict AAPL` | LSTM price prediction |
| `sentiment AAPL` | Sentiment analysis for a symbol |
| `price AAPL` | Get current price |
| `portfolio` | Show portfolio summary |
| `positions` | Show open positions |
| `stats` | Trading statistics |
| `risk` | Risk status and drawdown |
| `scan` | Scan watchlist for signals |
| `watch TSLA` | Add symbol to watchlist |
| `ask <question>` | Ask the AI agent a question |
| `status` | System status overview |
| `help` | Show all commands |

### Automated Scanning
```bash
python main_advanced_trading_system.py
```

### Single Command
```bash
python main.py --command "analyze AAPL"
python main.py --status
python main.py --scan
```

## Architecture

```
src/
├── ai_agent.py           # Main AI agent (coordinates all components)
├── lstm_model.py          # LSTM-GRU ensemble prediction model
├── sentiment_analyzer.py  # Multi-model NLP sentiment analysis
├── market_data.py         # yfinance market data fetcher
├── risk_manager.py        # Professional risk management
├── portfolio.py           # Portfolio and position tracking
├── trade_executor.py      # Paper/live trade execution
├── command_processor.py   # Text command interface
├── news_fetcher.py        # Multi-source news fetcher
├── config.py              # Configuration management
├── hybrid_ai_agent.py     # Legacy LSTM-GRU agent
└── trading_system.py      # Legacy news-based trading
```

## Running Tests
```bash
pip install pytest
python -m pytest tests/ -v
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing
We welcome contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.