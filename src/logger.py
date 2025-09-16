"""
Logging configuration and utilities
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
from typing import Optional
from src.config import LoggingConfig

class TradingLogger:
    """Custom logger for trading bot"""
    
    def __init__(self, config: LoggingConfig):
        self.config = config
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger configuration"""
        # Remove default handler
        logger.remove()
        
        # Create logs directory if it doesn't exist
        log_file_path = Path(self.config.file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Console handler with colors
        logger.add(
            sys.stdout,
            level=self.config.level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )
        
        # File handler with rotation
        logger.add(
            self.config.file,
            level=self.config.level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention=f"{self.config.retention_days} days",
            compression="zip"
        )
        
        # Separate file for trade logs
        trade_log_file = log_file_path.parent / "trades.log"
        logger.add(
            str(trade_log_file),
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            rotation="1 day",
            retention=f"{self.config.retention_days} days",
            compression="zip",
            filter=lambda record: "TRADE" in record["message"]
        )
        
        # Separate file for error logs
        error_log_file = log_file_path.parent / "errors.log"
        logger.add(
            str(error_log_file),
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention=f"{self.config.retention_days} days",
            compression="zip"
        )
    
    def log_trade(self, action: str, symbol: str, side: str, quantity: float, price: float, order_id: Optional[str] = None):
        """Log trade actions"""
        message = f"TRADE | {action} | {symbol} | {side} | Qty: {quantity} | Price: {price}"
        if order_id:
            message += f" | OrderID: {order_id}"
        logger.info(message)
    
    def log_pnl(self, symbol: str, pnl: float, total_pnl: float):
        """Log PnL updates"""
        logger.info(f"PNL | {symbol} | Current: {pnl:.2f} | Total: {total_pnl:.2f}")
    
    def log_risk_event(self, event_type: str, message: str, severity: str = "WARNING"):
        """Log risk management events"""
        logger.warning(f"RISK | {event_type} | {message} | Severity: {severity}")
    
    def log_account_update(self, balance: float, equity: float, margin: float):
        """Log account balance updates"""
        logger.info(f"ACCOUNT | Balance: {balance:.2f} | Equity: {equity:.2f} | Margin: {margin:.2f}")
    
    def log_grid_update(self, symbol: str, active_orders: int, filled_orders: int):
        """Log grid status updates"""
        logger.info(f"GRID | {symbol} | Active: {active_orders} | Filled: {filled_orders}")
    
    def log_dca_update(self, symbol: str, dca_level: int, trigger_price: float):
        """Log DCA status updates"""
        logger.info(f"DCA | {symbol} | Level: {dca_level} | Trigger: {trigger_price:.2f}")
    
    def log_backtest_result(self, start_date: str, end_date: str, total_return: float, max_drawdown: float, win_rate: float):
        """Log backtest results"""
        logger.info(f"BACKTEST | {start_date} to {end_date} | Return: {total_return:.2f}% | Max DD: {max_drawdown:.2f}% | Win Rate: {win_rate:.2f}%")
    
    # Expose standard logger methods
    def info(self, message: str):
        """Log info message"""
        logger.info(message)
    
    def error(self, message: str):
        """Log error message"""
        logger.error(message)
    
    def warning(self, message: str):
        """Log warning message"""
        logger.warning(message)
    
    def debug(self, message: str):
        """Log debug message"""
        logger.debug(message)

# Global logger instance
trading_logger: Optional[TradingLogger] = None

def get_logger() -> TradingLogger:
    """Get the global logger instance"""
    global trading_logger
    if trading_logger is None:
        from src.config import Config
        config = Config.load()
        trading_logger = TradingLogger(config.logging)
    return trading_logger

def setup_logger(config: LoggingConfig) -> TradingLogger:
    """Setup and return logger instance"""
    global trading_logger
    trading_logger = TradingLogger(config)
    return trading_logger
