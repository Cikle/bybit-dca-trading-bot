# Leveraged Grid + DCA Hybrid Trading Bot

A sophisticated Python-based trading bot that combines leveraged grid trading with Dollar Cost Averaging (DCA) strategies for Bybit cryptocurrency exchange. Features automatic recovery, health monitoring, and robust error handling for 24/7 operation.
(Only tested in Demo!)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/Cikle/bybit-dca-trading-bot.git
cd dca
python setup.py
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp env.example .env  # Windows: copy env.example .env

# Edit .env with your API keys and settings
nano .env  # or use your preferred editor
```

### 3. Request Demo Funds (Optional)
```bash
# Request demo trading funds from Bybit
python main.py demo-funds --amount 10000
```

### 4. Start Trading (Demo Mode)
```bash
# Starts bot with auto-recovery enabled
python main.py start --demo
```

### 5. Check Status
```bash
# Check bot status
python main.py status

# Or use the health monitor
python monitor_bot.py
```

## 📋 Prerequisites

- Python 3.8 or higher
- Bybit account (demo and/or live)
- Bybit API keys with trading permissions

## ⚙️ Configuration

### Environment Variables (.env)

#### Bybit API Configuration
```env
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_DEMO_MODE=true  # Set to false for live trading
```

#### Trading Configuration
```env
SYMBOL=BTCUSDT
LEVERAGE=10
INITIAL_CAPITAL=1000  # USD
```

#### Grid Trading Parameters
```env
# Option 1: Automatic calculation (recommended)
GRID_RANGE_PERCENT=3.0  # 3% range around current price (auto-calculated)
GRID_LEVELS=20
GRID_ORDER_SIZE=0.01  # Order size (adjust based on your symbol)

# Option 2: Manual price range
GRID_LOWER_PRICE=50000  # Lower bound (optional if using GRID_RANGE_PERCENT)
GRID_UPPER_PRICE=70000  # Upper bound (optional if using GRID_RANGE_PERCENT)
```

#### DCA Trading Parameters
```env
DCA_ENABLED=true
DCA_TRIGGER_PERCENT=2.0  # Price drop % to trigger DCA
DCA_ORDER_SIZE=0.02  # BTC amount per DCA order
DCA_MAX_ORDERS=5  # Maximum DCA orders per trend
```

#### Risk Management
```env
KILL_SWITCH_ENABLED=true
MAX_DRAWDOWN_PERCENT=20.0
BREAKEVEN_ENABLED=true
PARTIAL_PROFIT_ENABLED=true
PARTIAL_PROFIT_PERCENT=50.0  # Take 50% profit at 2x entry
```

#### Strategy Parameters (Used by both live trading and backtesting)
```env
GRID_WIN_RATE=80  # Percentage (80% = 8 out of 10 trades win)
GRID_PROFIT_PERCENT=0.7  # Fixed profit percentage for grid trades
GRID_LOSS_PERCENT=0.15  # Fixed loss percentage for grid trades
DCA_WIN_RATE=65  # Percentage (65% = 13 out of 20 DCA trades win)
DCA_PROFIT_PERCENT=1.0  # Fixed profit percentage for DCA trades
DCA_LOSS_PERCENT=0.2  # Fixed loss percentage for DCA trades
SLIPPAGE_PERCENT=0.01  # Fixed slippage percentage
```

## 🎯 Features

### Core Trading Strategies
- **Grid Trading**: Automated buy/sell orders at predetermined price levels with automatic price range calculation
- **DCA (Dollar Cost Averaging)**: Trend-following strategy with configurable triggers
- **Hybrid Approach**: Combines both strategies for optimal market coverage

### 🛡️ Auto-Recovery System
- **Automatic Restart**: Bot automatically restarts if it crashes (within 5 seconds)
- **Self-Healing**: Automatically reconnects to Bybit if connection is lost
- **Health Monitoring**: Continuous health checks every 5 seconds
- **Error Recovery**: Handles API errors gracefully with automatic retries
- **Rate Limiting**: Prevents infinite restart loops (max 10 restarts per hour)
- **24/7 Operation**: Designed to run continuously without manual intervention

### Risk Management
- **Kill Switch**: Emergency stop to close all positions
- **Maximum Drawdown**: Automatic stop at configured loss threshold
- **Breakeven Orders**: Move stop-loss to entry price when profitable
- **Partial Profit Taking**: Take profits at predetermined levels

### Monitoring & Logging
- **Comprehensive Logging**: All trades, fills, and risk events with rotation
- **Real-time Status**: Live monitoring of bot performance
- **Performance Metrics**: Detailed PnL and risk statistics
- **Health Checks**: Built-in health monitoring system
- **Alert System**: Telegram notifications for critical events (optional)

### Backtesting
- **Historical Analysis**: Test strategies on past data
- **Performance Metrics**: Win rate, profit factor, Sharpe ratio
- **Risk Assessment**: Maximum drawdown and volatility analysis
- **CSV Export**: Export backtest results for further analysis

## 📊 CLI Commands

### Start Bot
```bash
# Demo mode (default)
python main.py start --demo

# Live mode
python main.py start --live

# Custom config file
python main.py start --config custom.env
```

### Monitor Bot
```bash
# Check status
python main.py status

# View performance metrics
python main.py performance

# Health check (standalone script)
python monitor_bot.py

# Stop bot
python main.py stop
```

### Emergency Controls
```bash
# Emergency stop (triggers kill switch)
python main.py emergency
```

### Setup & Maintenance
```bash
# Run initial setup
python main.py setup

# Backtest strategy
python main.py backtest --start 2024-01-01 --end 2024-12-31

# Export backtest results to CSV
python main.py backtest --start 2024-01-01 --end 2024-12-31 --export results.csv

# Request demo funds
python main.py demo-funds --amount 10000
```

## 🏗️ Architecture

### Core Components
- **TradingBot**: Main orchestrator class
- **BybitClient**: API wrapper for Bybit exchange
- **GridEngine**: Grid trading logic
- **DCAEngine**: DCA trading logic
- **RiskManager**: Risk management and monitoring
- **BacktestEngine**: Historical strategy testing

### Configuration Management
- **Config**: Centralized configuration from environment variables
- **Logger**: Structured logging with rotation and filtering
- **Database**: SQLite for state persistence (optional)

## 📈 Strategy Overview

### Grid Trading
1. **Setup**: Define price range (automatic via `GRID_RANGE_PERCENT` or manual bounds) and number of levels
2. **Execution**: Place buy orders below current price, sell orders above
3. **Management**: Automatically replace filled orders with opposite orders
4. **Profit**: Capture price movements within the grid range with configurable win rate and profit/loss percentages

### DCA Trading
1. **Trigger**: Monitor for significant price movements
2. **Execution**: Place market orders in trend direction
3. **Scaling**: Increase position size with each trigger
4. **Management**: Stop at maximum order limit

### Risk Management
1. **Monitoring**: Continuous risk metric calculation
2. **Protection**: Automatic stop-loss and position sizing
3. **Recovery**: Breakeven and partial profit mechanisms
4. **Emergency**: Kill switch for immediate position closure

## 🔧 Development

### Project Structure
```
dca/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── logger.py          # Logging system
│   ├── bybit_client.py    # Bybit API wrapper
│   ├── grid_engine.py     # Grid trading logic
│   ├── dca_engine.py      # DCA trading logic
│   ├── risk_manager.py    # Risk management
│   ├── trading_bot.py     # Main bot class
│   ├── backtest.py        # Backtesting framework
│   └── database.py        # Database persistence (SQLite)
├── main.py                # CLI interface with auto-recovery
├── monitor_bot.py         # Health monitoring script
├── setup.py               # Setup script
├── requirements.txt       # Python dependencies
├── env.example           # Environment template
├── logs/                  # Log files directory
├── data/                  # Data directory
└── README.md             # This file
```

### Dependencies
- `pybit>=5.7.0`: Bybit API client
- `python-dotenv>=1.0.0`: Environment management
- `pandas>=2.0.0`: Data manipulation
- `numpy>=1.24.0`: Numerical computations
- `sqlalchemy>=2.0.0`: Database ORM
- `loguru>=0.7.0`: Advanced logging
- `rich>=13.0.0`: Beautiful CLI output
- `typer>=0.9.0`: CLI framework
- `requests>=2.31.0`: HTTP requests
- `websocket-client>=1.6.0`: WebSocket support
- `python-telegram-bot>=20.0`: Telegram notifications (optional)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run setup
python setup.py
```

## ⚠️ Risk Disclaimer

**IMPORTANT**: This software is for educational and research purposes only. Cryptocurrency trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results.

### Key Risks
- **Leverage Risk**: High leverage amplifies both gains and losses
- **Market Risk**: Cryptocurrency markets are highly volatile
- **Technical Risk**: Software bugs or API failures may cause losses
- **Liquidation Risk**: Positions may be liquidated if margin requirements are not met

### Recommendations
1. **Start Small**: Begin with demo mode and small capital
2. **Test Thoroughly**: Run extensive backtests before live trading
3. **Monitor Closely**: Never leave the bot unattended for extended periods
4. **Set Limits**: Use appropriate risk management settings
5. **Stay Informed**: Keep up with market conditions and news

## 📞 Support

### Getting Help
- Check the logs in the `logs/` directory (`trading_bot.log`, `trades.log`, `errors.log`)
- Review configuration in `.env` file
- Test with demo mode first (`python main.py start --demo`)
- Use the `status` command or `monitor_bot.py` to monitor bot health
- View real-time logs: `tail -f logs/trading_bot.log` (Linux/Mac) or use a text editor

### Common Issues
1. **API Connection**: Verify API keys and network connection
2. **Insufficient Balance**: Request demo funds with `python main.py demo-funds` or ensure adequate account balance
3. **Invalid Configuration**: Check all environment variables in `.env` file
4. **Permission Errors**: Verify API key permissions in Bybit dashboard
5. **Bot Crashes**: The auto-recovery system should restart automatically. If persistent, check logs for errors

## 💝 Sponsorship

If this project has been helpful to you and you'd like to support its continued development, please consider sponsoring:

- **GitHub Sponsors**: [Sponsor me on GitHub](https://github.com/sponsors/cikle)
- **Donations**: If you'd like to contribute in other ways, feel free to reach out!

Your support helps maintain and improve this project. Thank you! 🙏

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📚 Additional Resources

- [Bybit API Documentation](https://bybit-exchange.github.io/docs/)
- See `AUTO_RECOVERY_README.md` for detailed auto-recovery system documentation

---

**Happy Trading! 🚀**

Remember: Always trade responsibly and never risk more than you can afford to lose.
