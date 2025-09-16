# Leveraged Grid + DCA Hybrid Trading Bot

A sophisticated Python-based trading bot that combines leveraged grid trading with Dollar Cost Averaging (DCA) strategies for Bybit cryptocurrency exchange.

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd dca
python setup.py
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your API keys and settings
nano .env  # or use your preferred editor
```

### 3. Start Trading (Demo Mode)
```bash
python main.py start --demo
```

### 4. Check Status
```bash
python main.py status
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
GRID_LOWER_PRICE=50000
GRID_UPPER_PRICE=70000
GRID_LEVELS=20
GRID_ORDER_SIZE=0.01  # BTC amount per order
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

## 🎯 Features

### Core Trading Strategies
- **Grid Trading**: Automated buy/sell orders at predetermined price levels
- **DCA (Dollar Cost Averaging)**: Trend-following strategy with configurable triggers
- **Hybrid Approach**: Combines both strategies for optimal market coverage

### Risk Management
- **Kill Switch**: Emergency stop to close all positions
- **Maximum Drawdown**: Automatic stop at configured loss threshold
- **Breakeven Orders**: Move stop-loss to entry price when profitable
- **Partial Profit Taking**: Take profits at predetermined levels

### Monitoring & Logging
- **Comprehensive Logging**: All trades, fills, and risk events
- **Real-time Status**: Live monitoring of bot performance
- **Performance Metrics**: Detailed PnL and risk statistics
- **Alert System**: Telegram notifications for critical events

### Backtesting
- **Historical Analysis**: Test strategies on past data
- **Performance Metrics**: Win rate, profit factor, Sharpe ratio
- **Risk Assessment**: Maximum drawdown and volatility analysis

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

# View performance
python main.py performance

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
1. **Setup**: Define price range and number of levels
2. **Execution**: Place buy orders below current price, sell orders above
3. **Management**: Automatically replace filled orders with opposite orders
4. **Profit**: Capture price movements within the grid range

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
│   └── backtest.py        # Backtesting framework
├── main.py                # CLI interface
├── setup.py               # Setup script
├── requirements.txt       # Python dependencies
├── env.example           # Environment template
└── README.md             # This file
```

### Dependencies
- `pybit`: Bybit API client
- `pandas`: Data manipulation
- `numpy`: Numerical computations
- `loguru`: Advanced logging
- `rich`: Beautiful CLI output
- `typer`: CLI framework
- `python-dotenv`: Environment management

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
- Check the logs in the `logs/` directory
- Review configuration in `.env` file
- Test with demo mode first
- Use the `status` command to monitor bot health

### Common Issues
1. **API Connection**: Verify API keys and network connection
2. **Insufficient Balance**: Ensure adequate account balance
3. **Invalid Configuration**: Check all environment variables
4. **Permission Errors**: Verify API key permissions

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
- [Grid Trading Strategy Guide](https://example.com/grid-trading)
- [Risk Management Best Practices](https://example.com/risk-management)

---

**Happy Trading! 🚀**

Remember: Always trade responsibly and never risk more than you can afford to lose.
