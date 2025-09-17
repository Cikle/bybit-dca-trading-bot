"""
Main Trading Bot Class
"""

import time
import threading
from typing import Optional, Dict, Any
from src.config import Config
from src.bybit_client import BybitClient
from src.grid_engine import GridEngine
from src.dca_engine import DCAEngine
from src.risk_manager import RiskManager
from src.logger import get_logger

class TradingBot:
    """Main trading bot class"""
    
    def __init__(self, config: Config):
        self.config = config
        self.trading_config = config.trading  # Add this for account status logging
        self.logger = get_logger()
        
        # Initialize components
        self.bybit_client = BybitClient(config.bybit, config.trading)
        self.grid_engine = GridEngine(self.bybit_client, config.grid, config.trading, config.strategy)
        self.dca_engine = DCAEngine(self.bybit_client, config.dca, config.trading, config.strategy)
        self.risk_manager = RiskManager(self.bybit_client, config.risk, config.trading)
        
        # Bot state
        self.running = False
        self.main_thread: Optional[threading.Thread] = None
        self.update_interval = 5  # seconds
        
        # Set up risk manager callbacks
        self.risk_manager.set_kill_switch_callback(self._on_kill_switch)
        self.risk_manager.set_breakeven_callback(self._on_breakeven)
        self.risk_manager.set_partial_profit_callback(self._on_partial_profit)
    
    def start(self) -> bool:
        """Start the trading bot"""
        try:
            if self.running:
                self.logger.warning("Bot is already running")
                return True
            
            # Connect to Bybit
            if not self.bybit_client.connect():
                self.logger.error("Failed to connect to Bybit")
                return False
            
            # Set leverage (optional for demo accounts)
            if not self.bybit_client.set_leverage(self.config.trading.leverage):
                self.logger.warning("Failed to set leverage - this is normal for demo accounts")
                # Continue anyway as leverage might already be set
            
            # Start grid engine
            if not self.grid_engine.start_grid():
                self.logger.error("Failed to start grid engine")
                return False
            
            # Start DCA engine
            if not self.dca_engine.start_dca():
                self.logger.error("Failed to start DCA engine")
                return False
            
            # Start main loop
            self.running = True
            self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
            self.main_thread.start()
            
            self.logger.info("Trading bot started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the trading bot"""
        try:
            if not self.running:
                self.logger.warning("Bot is not running")
                return True
            
            self.running = False
            
            # Stop engines
            self.grid_engine.stop_grid()
            self.dca_engine.stop_dca()
            
            # Disconnect from Bybit
            self.bybit_client.disconnect()
            
            # Wait for main thread to finish
            if self.main_thread and self.main_thread.is_alive():
                self.main_thread.join(timeout=10)
            
            self.logger.info("Trading bot stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")
            return False
    
    def emergency_stop(self) -> bool:
        """Emergency stop - trigger kill switch"""
        try:
            self.logger.critical("EMERGENCY STOP TRIGGERED")
            self.risk_manager.trigger_kill_switch("Emergency stop requested")
            return self.stop()
            
        except Exception as e:
            self.logger.error(f"Error in emergency stop: {e}")
            return False
    
    def _main_loop(self):
        """Main trading loop"""
        try:
            while self.running:
                # Check risk limits
                if not self.risk_manager.check_risk_limits():
                    self.logger.critical("Risk limits exceeded, stopping bot")
                    self.running = False
                    break
                
                # Update grid engine
                self.grid_engine.update_grid()
                
                # Update DCA engine
                self.dca_engine.update_dca()
                
                # Log account status
                self._log_account_status()
                
                # Sleep before next update
                time.sleep(self.update_interval)
                
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            self.running = False
    
    def _log_account_status(self):
        """Log current account status"""
        try:
            # Get account balance
            balance_info = self.bybit_client.get_account_balance()
            if balance_info:
                for coin in balance_info.get('list', []):
                    if coin['coin'] == 'USDT':
                        balance = float(coin['walletBalance'])
                        equity = float(coin['equity'])
                        margin = float(coin['usedMargin'])
                        
                        self.logger.log_account_update(balance, equity, margin)
                        break
            
            # Get positions and log PnL
            positions = self.bybit_client.get_positions()
            if positions:
                for position in positions:
                    if position['symbol'] == self.trading_config.symbol:
                        unrealized_pnl = float(position.get('unrealisedPnl', 0))
                        realized_pnl = float(position.get('cumRealisedPnl', 0))
                        total_pnl = unrealized_pnl + realized_pnl
                        
                        self.logger.log_pnl(self.config.trading.symbol, unrealized_pnl, total_pnl)
                        break
                        
        except Exception as e:
            self.logger.error(f"Error logging account status: {e}")
    
    def _on_kill_switch(self, reason: str):
        """Handle kill switch event"""
        self.logger.critical(f"Kill switch activated: {reason}")
        self.running = False
    
    def _on_breakeven(self, position_id: str, price: float):
        """Handle breakeven event"""
        self.logger.info(f"Breakeven order placed for position {position_id} at {price}")
    
    def _on_partial_profit(self, position_id: str, size: float):
        """Handle partial profit event"""
        self.logger.info(f"Partial profit order placed for position {position_id}, size: {size}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        try:
            # Get risk metrics
            risk_metrics = self.risk_manager.get_risk_metrics()
            
            return {
                "running": self.running,
                "connected": self.bybit_client.is_connected(),
                "grid_status": self.grid_engine.get_grid_status(),
                "dca_status": self.dca_engine.get_dca_status(),
                "risk_status": self.risk_manager.get_risk_status(),
                "risk_metrics": {
                    "current_balance": risk_metrics.current_balance if risk_metrics else 0,
                    "equity": risk_metrics.equity if risk_metrics else 0,
                    "unrealized_pnl": risk_metrics.unrealized_pnl if risk_metrics else 0,
                    "current_drawdown": risk_metrics.current_drawdown if risk_metrics else 0
                } if risk_metrics else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {"error": str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            # Get risk metrics
            risk_metrics = self.risk_manager.get_risk_metrics()
            if not risk_metrics:
                return {"error": "Unable to get risk metrics"}
            
            # Calculate performance metrics
            initial_capital = self.config.trading.initial_capital
            current_balance = risk_metrics.current_balance
            total_return = ((current_balance - initial_capital) / initial_capital) * 100
            
            return {
                "initial_capital": initial_capital,
                "current_balance": current_balance,
                "total_return_percent": total_return,
                "unrealized_pnl": risk_metrics.unrealized_pnl,
                "realized_pnl": risk_metrics.realized_pnl,
                "max_drawdown": risk_metrics.max_drawdown,
                "current_drawdown": risk_metrics.current_drawdown,
                "margin_ratio": risk_metrics.margin_ratio
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}
    
    def is_running(self) -> bool:
        """Check if bot is running"""
        return self.running
