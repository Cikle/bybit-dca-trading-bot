"""
Configuration management for the trading bot
"""

import os
from typing import Optional
from dotenv import load_dotenv
from dataclasses import dataclass

# Load environment variables
load_dotenv()

@dataclass
class BybitConfig:
    """Bybit API configuration"""
    api_key: str
    api_secret: str
    demo_mode: bool = True
    
    @classmethod
    def from_env(cls) -> 'BybitConfig':
        return cls(
            api_key=os.getenv('BYBIT_API_KEY', ''),
            api_secret=os.getenv('BYBIT_API_SECRET', ''),
            demo_mode=os.getenv('BYBIT_DEMO_MODE', 'true').lower() == 'true'
        )

@dataclass
class TradingConfig:
    """Trading configuration"""
    symbol: str
    leverage: int
    initial_capital: float
    
    @classmethod
    def from_env(cls) -> 'TradingConfig':
        return cls(
            symbol=os.getenv('SYMBOL', 'BTCUSDT'),
            leverage=int(os.getenv('LEVERAGE', '10')),
            initial_capital=float(os.getenv('INITIAL_CAPITAL', '1000'))
        )

@dataclass
class GridConfig:
    """Grid trading configuration"""
    lower_price: float
    upper_price: float
    levels: int
    order_size: float
    range_percent: float  # For automatic calculation
    
    @classmethod
    def from_env(cls) -> 'GridConfig':
        return cls(
            lower_price=float(os.getenv('GRID_LOWER_PRICE', '50000')),
            upper_price=float(os.getenv('GRID_UPPER_PRICE', '70000')),
            levels=int(os.getenv('GRID_LEVELS', '20')),
            order_size=float(os.getenv('GRID_ORDER_SIZE', '0.01')),
            range_percent=float(os.getenv('GRID_RANGE_PERCENT', '3.0'))
        )

@dataclass
class DCAConfig:
    """DCA trading configuration"""
    enabled: bool
    trigger_percent: float
    order_size: float
    max_orders: int
    
    @classmethod
    def from_env(cls) -> 'DCAConfig':
        return cls(
            enabled=os.getenv('DCA_ENABLED', 'true').lower() == 'true',
            trigger_percent=float(os.getenv('DCA_TRIGGER_PERCENT', '2.0')),
            order_size=float(os.getenv('DCA_ORDER_SIZE', '0.02')),
            max_orders=int(os.getenv('DCA_MAX_ORDERS', '5'))
        )

@dataclass
class RiskConfig:
    """Risk management configuration"""
    kill_switch_enabled: bool
    max_drawdown_percent: float
    breakeven_enabled: bool
    partial_profit_enabled: bool
    partial_profit_percent: float
    
    @classmethod
    def from_env(cls) -> 'RiskConfig':
        return cls(
            kill_switch_enabled=os.getenv('KILL_SWITCH_ENABLED', 'true').lower() == 'true',
            max_drawdown_percent=float(os.getenv('MAX_DRAWDOWN_PERCENT', '20.0')),
            breakeven_enabled=os.getenv('BREAKEVEN_ENABLED', 'true').lower() == 'true',
            partial_profit_enabled=os.getenv('PARTIAL_PROFIT_ENABLED', 'true').lower() == 'true',
            partial_profit_percent=float(os.getenv('PARTIAL_PROFIT_PERCENT', '50.0'))
        )

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str
    file: str
    retention_days: int
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            file=os.getenv('LOG_FILE', 'logs/trading_bot.log'),
            retention_days=int(os.getenv('LOG_RETENTION_DAYS', '30'))
        )

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        return cls(
            url=os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
        )

@dataclass
class AlertConfig:
    """Alert configuration"""
    enabled: bool
    telegram_bot_token: Optional[str]
    telegram_chat_id: Optional[str]
    
    @classmethod
    def from_env(cls) -> 'AlertConfig':
        return cls(
            enabled=os.getenv('ALERTS_ENABLED', 'true').lower() == 'true',
            telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID')
        )

@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    start_date: str
    end_date: str
    initial_capital: float
    
    @classmethod
    def from_env(cls) -> 'BacktestConfig':
        return cls(
            start_date=os.getenv('BACKTEST_START_DATE', '2024-01-01'),
            end_date=os.getenv('BACKTEST_END_DATE', '2024-12-31'),
            initial_capital=float(os.getenv('BACKTEST_INITIAL_CAPITAL', '1000'))
        )

@dataclass
class Config:
    """Main configuration class"""
    bybit: BybitConfig
    trading: TradingConfig
    grid: GridConfig
    dca: DCAConfig
    risk: RiskConfig
    logging: LoggingConfig
    database: DatabaseConfig
    alert: AlertConfig
    backtest: BacktestConfig
    
    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from environment variables"""
        return cls(
            bybit=BybitConfig.from_env(),
            trading=TradingConfig.from_env(),
            grid=GridConfig.from_env(),
            dca=DCAConfig.from_env(),
            risk=RiskConfig.from_env(),
            logging=LoggingConfig.from_env(),
            database=DatabaseConfig.from_env(),
            alert=AlertConfig.from_env(),
            backtest=BacktestConfig.from_env()
        )
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.bybit.api_key or not self.bybit.api_secret:
            print("❌ Bybit API credentials not configured")
            return False
        
        # Note: Grid prices are now calculated automatically, so we don't validate them here
        
        if self.trading.leverage < 1 or self.trading.leverage > 100:
            print("❌ Leverage must be between 1 and 100")
            return False
        
        return True
