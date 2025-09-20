"""
Risk Management System
"""

import time
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from src.config import RiskConfig, TradingConfig
from src.bybit_client import BybitClient
from src.logger import get_logger

@dataclass
class RiskMetrics:
    """Risk metrics for monitoring"""
    current_balance: float
    equity: float
    margin_used: float
    unrealized_pnl: float
    realized_pnl: float
    max_drawdown: float
    current_drawdown: float
    margin_ratio: float

class RiskManager:
    """Risk management system"""
    
    def __init__(self, bybit_client: BybitClient, risk_config: RiskConfig, trading_config: TradingConfig):
        self.bybit_client = bybit_client
        self.risk_config = risk_config
        self.trading_config = trading_config
        self.logger = get_logger()
        
        self.kill_switch_triggered = False
        self.breakeven_orders: Dict[str, str] = {}  # position_id -> order_id
        self.partial_profit_orders: Dict[str, str] = {}  # position_id -> order_id
        self.peak_balance = 0.0
        self.max_drawdown_reached = 0.0
        
        # Callbacks for risk events
        self.kill_switch_callback: Optional[Callable] = None
        self.breakeven_callback: Optional[Callable] = None
        self.partial_profit_callback: Optional[Callable] = None
    
    def set_kill_switch_callback(self, callback: Callable):
        """Set callback for kill switch events"""
        self.kill_switch_callback = callback
    
    def set_breakeven_callback(self, callback: Callable):
        """Set callback for breakeven events"""
        self.breakeven_callback = callback
    
    def set_partial_profit_callback(self, callback: Callable):
        """Set callback for partial profit events"""
        self.partial_profit_callback = callback
    
    def get_risk_metrics(self) -> Optional[RiskMetrics]:
        """Get current risk metrics"""
        try:
            # Get account balance
            balance_info = self.bybit_client.get_account_balance()
            if not balance_info:
                return None
            
            # Get positions
            positions = self.bybit_client.get_positions()
            if not positions:
                return None
            
            # Calculate metrics
            current_balance = 0.0
            equity = 0.0
            margin_used = 0.0
            unrealized_pnl = 0.0
            realized_pnl = 0.0
            
            # Process balance info
            for coin in balance_info.get('list', []):
                if coin['coin'] == 'USDT':
                    current_balance = float(coin['walletBalance'])
                    equity = float(coin['equity'])
                    break
            
            # Process positions
            for position in positions:
                if position['symbol'] == self.trading_config.symbol:
                    unrealized_pnl += float(position.get('unrealisedPnl', 0))
                    realized_pnl += float(position.get('cumRealisedPnl', 0))
                    margin_used += float(position.get('positionIM', 0))
            
            # Calculate drawdown
            if current_balance > self.peak_balance:
                self.peak_balance = current_balance
            
            current_drawdown = (self.peak_balance - current_balance) / self.peak_balance * 100 if self.peak_balance > 0 else 0
            if current_drawdown > self.max_drawdown_reached:
                self.max_drawdown_reached = current_drawdown
            
            # Calculate margin ratio
            margin_ratio = (margin_used / equity * 100) if equity > 0 else 0
            
            return RiskMetrics(
                current_balance=current_balance,
                equity=equity,
                margin_used=margin_used,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
                max_drawdown=self.max_drawdown_reached,
                current_drawdown=current_drawdown,
                margin_ratio=margin_ratio
            )
            
        except Exception as e:
            self.logger.error(f"Error getting risk metrics: {e}")
            return None
    
    def check_risk_limits(self) -> bool:
        """Check all risk limits and trigger appropriate actions"""
        try:
            if self.kill_switch_triggered:
                return False
            
            metrics = self.get_risk_metrics()
            if not metrics:
                return True
            
            # Check maximum drawdown
            if metrics.current_drawdown >= self.risk_config.max_drawdown_percent:
                self.logger.log_risk_event(
                    "MAX_DRAWDOWN_REACHED",
                    f"Current drawdown: {metrics.current_drawdown:.2f}% (limit: {self.risk_config.max_drawdown_percent}%)",
                    "CRITICAL"
                )
                self.trigger_kill_switch("Maximum drawdown reached")
                return False
            
            # Check margin ratio (liquidation risk)
            if metrics.margin_ratio > 80:  # 80% margin usage
                self.logger.log_risk_event(
                    "HIGH_MARGIN_USAGE",
                    f"Margin ratio: {metrics.margin_ratio:.2f}%",
                    "WARNING"
                )
            
            # Check for breakeven opportunities
            if self.risk_config.breakeven_enabled:
                self._check_breakeven_opportunities(metrics)
            
            # Check for partial profit opportunities
            if self.risk_config.partial_profit_enabled:
                self._check_partial_profit_opportunities(metrics)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking risk limits: {e}")
            return True
    
    def trigger_kill_switch(self, reason: str):
        """Trigger kill switch to close all positions"""
        try:
            if self.kill_switch_triggered:
                return
            
            self.kill_switch_triggered = True
            
            self.logger.log_risk_event(
                "KILL_SWITCH_TRIGGERED",
                f"Reason: {reason}",
                "CRITICAL"
            )
            
            # Close all positions
            positions = self.bybit_client.get_positions()
            if positions:
                for position in positions:
                    if position['symbol'] == self.trading_config.symbol and float(position['size']) > 0:
                        # Close position with market order
                        side = "Sell" if position['side'] == "Buy" else "Buy"
                        # FIXED: Use absolute value of position size to ensure correct quantity
                        position_size = abs(float(position['size']))
                        self.bybit_client.place_order(
                            side=side,
                            order_type="Market",
                            qty=position_size
                        )
            
            # Cancel all open orders
            open_orders = self.bybit_client.get_open_orders()
            if open_orders:
                for order in open_orders:
                    if order['symbol'] == self.trading_config.symbol:
                        self.bybit_client.cancel_order(order['orderId'])
            
            # Call kill switch callback
            if self.kill_switch_callback:
                self.kill_switch_callback(reason)
            
        except Exception as e:
            self.logger.error(f"Error triggering kill switch: {e}")
    
    def _check_breakeven_opportunities(self, metrics: RiskMetrics):
        """Check for breakeven opportunities"""
        try:
            positions = self.bybit_client.get_positions()
            if not positions:
                return
            
            for position in positions:
                if position['symbol'] == self.trading_config.symbol and float(position['size']) > 0:
                    position_id = position['positionIdx']
                    unrealized_pnl = float(position.get('unrealisedPnl', 0))
                    
                    # Check if position is profitable and breakeven order not already placed
                    if unrealized_pnl > 0 and position_id not in self.breakeven_orders:
                        self._place_breakeven_order(position)
                        
        except Exception as e:
            self.logger.error(f"Error checking breakeven opportunities: {e}")
    
    def _place_breakeven_order(self, position: Dict):
        """Place breakeven order"""
        try:
            position_id = position['positionIdx']
            entry_price = float(position['avgPrice'])
            size = position['size']
            side = "Sell" if position['side'] == "Buy" else "Buy"
            
            # Place breakeven order at entry price
            # FIXED: Use absolute value of position size to avoid negative quantities
            order_quantity = abs(float(size))
            self.logger.info(f"Placing breakeven order: {side} {order_quantity} at ${entry_price}")
            
            order_id = self.bybit_client.place_order(
                side=side,
                order_type="Limit",
                qty=order_quantity,
                price=entry_price
            )
            
            if order_id:
                self.breakeven_orders[position_id] = order_id
                
                self.logger.log_risk_event(
                    "BREAKEVEN_ORDER_PLACED",
                    f"Position: {position_id}, Price: {entry_price}",
                    "INFO"
                )
                
                # Call breakeven callback
                if self.breakeven_callback:
                    self.breakeven_callback(position_id, entry_price)
                        
        except Exception as e:
            self.logger.error(f"Error placing breakeven order: {e}")
    
    def _check_partial_profit_opportunities(self, metrics: RiskMetrics):
        """Check for partial profit opportunities"""
        try:
            positions = self.bybit_client.get_positions()
            if not positions:
                return
            
            for position in positions:
                if position['symbol'] == self.trading_config.symbol and float(position['size']) > 0:
                    position_id = position['positionIdx']
                    entry_price = float(position['avgPrice'])
                    current_price = float(position['markPrice'])
                    unrealized_pnl = float(position.get('unrealisedPnl', 0))
                    
                    # Check if position has 2x profit and partial profit order not already placed
                    profit_multiplier = 2.0  # 2x entry price
                    if (position['side'] == "Buy" and current_price >= entry_price * profit_multiplier) or \
                       (position['side'] == "Sell" and current_price <= entry_price / profit_multiplier):
                        
                        if position_id not in self.partial_profit_orders:
                            self._place_partial_profit_order(position)
                        
        except Exception as e:
            self.logger.error(f"Error checking partial profit opportunities: {e}")
    
    def _place_partial_profit_order(self, position: Dict):
        """Place partial profit order"""
        try:
            position_id = position['positionIdx']
            size = float(position['size'])
            partial_size = size * (self.risk_config.partial_profit_percent / 100)
            side = "Sell" if position['side'] == "Buy" else "Buy"
            
            # Place partial profit order with market order
            order_id = self.bybit_client.place_order(
                side=side,
                order_type="Market",
                qty=partial_size
            )
            
            if order_id:
                self.partial_profit_orders[position_id] = order_id
                
                self.logger.log_risk_event(
                    "PARTIAL_PROFIT_ORDER_PLACED",
                    f"Position: {position_id}, Size: {partial_size} ({self.risk_config.partial_profit_percent}%)",
                    "INFO"
                )
                
                # Call partial profit callback
                if self.partial_profit_callback:
                    self.partial_profit_callback(position_id, partial_size)
                        
        except Exception as e:
            self.logger.error(f"Error placing partial profit order: {e}")
    
    def reset_kill_switch(self):
        """Reset kill switch (for testing purposes)"""
        self.kill_switch_triggered = False
        self.logger.info("Kill switch reset")
    
    def is_kill_switch_triggered(self) -> bool:
        """Check if kill switch is triggered"""
        return self.kill_switch_triggered
    
    def get_risk_status(self) -> Dict[str, any]:
        """Get current risk status"""
        metrics = self.get_risk_metrics()
        
        return {
            "kill_switch_triggered": self.kill_switch_triggered,
            "breakeven_enabled": self.risk_config.breakeven_enabled,
            "partial_profit_enabled": self.risk_config.partial_profit_enabled,
            "max_drawdown_percent": self.risk_config.max_drawdown_percent,
            "current_drawdown": metrics.current_drawdown if metrics else 0,
            "max_drawdown_reached": self.max_drawdown_reached,
            "breakeven_orders": len(self.breakeven_orders),
            "partial_profit_orders": len(self.partial_profit_orders)
        }
