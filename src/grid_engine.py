"""
Grid Trading Engine
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from src.config import GridConfig, TradingConfig
from src.bybit_client import BybitClient
from src.logger import get_logger

@dataclass
class GridLevel:
    """Represents a single grid level"""
    level: int
    price: float
    side: str  # 'Buy' or 'Sell'
    quantity: float
    order_id: Optional[str] = None
    filled: bool = False
    fill_price: Optional[float] = None
    fill_time: Optional[float] = None

class GridEngine:
    """Grid trading engine"""
    
    def __init__(self, bybit_client: BybitClient, grid_config: GridConfig, trading_config: TradingConfig, strategy_config):
        self.bybit_client = bybit_client
        self.grid_config = grid_config
        self.trading_config = trading_config
        self.strategy_config = strategy_config
        self.logger = get_logger()
        
        self.grid_levels: List[GridLevel] = []
        self.active = False
        self.current_price = 0.0
        self.trades = []  # Track trades for deterministic win rate
        
    def initialize_grid(self) -> bool:
        """Initialize grid levels"""
        try:
            # Get current market price
            current_price = self.bybit_client.get_current_price()
            if not current_price:
                self.logger.error("Failed to get current price for grid initialization")
                return False
            
            self.current_price = current_price
            
            # AUTOMATIC GRID CALCULATION: Exactly like backtest
            # Use percentage range around CURRENT PRICE (not historical data)
            price_range_percent = 0.03  # 3% range (hardcoded to fix the 300% bug)
            grid_lower = current_price * (1 - price_range_percent)
            grid_upper = current_price * (1 + price_range_percent)
            
            self.logger.info(f"Current price: ${current_price:.2f}")
            self.logger.info(f"Grid range: ${grid_lower:.2f} - ${grid_upper:.2f} ({price_range_percent*100:.1f}% range)")
            
            # Calculate grid spacing
            price_range = grid_upper - grid_lower
            base_spacing = price_range / (self.grid_config.levels - 1)
            
            # Create grid levels with optimized spacing
            self.grid_levels = []
            
            for i in range(self.grid_config.levels):
                # Use linear spacing for consistent grid levels (like backtest)
                price = grid_lower + (i * base_spacing)
                
                # Determine if this should be a buy or sell order
                if price < current_price:
                    side = "Buy"
                    # Use standard quantity for compliance
                    quantity = self.grid_config.order_size
                else:
                    side = "Sell"
                    # Standard quantity for sell orders
                    quantity = self.grid_config.order_size
                
                grid_level = GridLevel(
                    level=i,
                    price=round(price, 2),
                    side=side,
                    quantity=round(quantity, 4)
                )
                
                self.logger.info(f"Grid level {i}: {side} {quantity} XRP at ${price:.2f}")
                self.grid_levels.append(grid_level)
            
            self.logger.info(f"Initialized grid with {len(self.grid_levels)} levels")
            self.logger.log_grid_update(self.trading_config.symbol, 0, 0)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing grid: {e}")
            return False
    
    def start_grid(self) -> bool:
        """Start the grid trading"""
        try:
            # Cancel all existing orders first
            self._cancel_all_orders()
            
            # FIXED: Close all existing positions to start fresh
            self._close_all_positions()
            
            if not self.grid_levels:
                if not self.initialize_grid():
                    return False
            
            # Place initial orders
            placed_orders = 0
            for level in self.grid_levels:
                if not level.filled:
                    # FIXED: Use configured order size instead of level.quantity to prevent 330 XRP bug
                    order_id = self.bybit_client.place_order(
                        side=level.side,
                        order_type="Limit",
                        qty=self.grid_config.order_size,
                        price=level.price
                    )
                    
                    if order_id:
                        level.order_id = order_id
                        placed_orders += 1
                    else:
                        self.logger.warning(f"Failed to place order for level {level.level}")
            
            self.active = True
            self.logger.info(f"Grid started with {placed_orders} orders placed")
            self.logger.log_grid_update(self.trading_config.symbol, placed_orders, 0)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting grid: {e}")
            return False
    
    def stop_grid(self) -> bool:
        """Stop the grid trading and cancel all orders"""
        try:
            cancelled_orders = 0
            
            for level in self.grid_levels:
                if level.order_id and not level.filled:
                    if self.bybit_client.cancel_order(level.order_id):
                        cancelled_orders += 1
                        level.order_id = None
            
            self.active = False
            self.logger.info(f"Grid stopped, cancelled {cancelled_orders} orders")
            self.logger.log_grid_update(self.trading_config.symbol, 0, 0)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping grid: {e}")
            return False
    
    def _cancel_all_orders(self) -> bool:
        """Cancel all existing orders for the symbol"""
        try:
            # Get all open orders for the symbol
            open_orders = self.bybit_client.get_open_orders()
            if not open_orders:
                return True
            
            cancelled_count = 0
            for order in open_orders:
                if order.get('symbol') == self.trading_config.symbol:
                    order_id = order.get('orderId')
                    if order_id and self.bybit_client.cancel_order(order_id):
                        cancelled_count += 1
            
            if cancelled_count > 0:
                self.logger.info(f"Cancelled {cancelled_count} existing orders")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling existing orders: {e}")
            return False
    
    def _close_all_positions(self) -> bool:
        """Close all existing positions for the symbol to start fresh"""
        try:
            positions = self.bybit_client.get_positions()
            if not positions:
                return True
            
            closed_count = 0
            for position in positions:
                if position['symbol'] == self.trading_config.symbol and float(position['size']) != 0:
                    # Close position with market order
                    side = "Sell" if position['side'] == "Buy" else "Buy"
                    position_size = abs(float(position['size']))
                    
                    self.logger.info(f"Closing position: {side} {position_size} XRP (was {position['side']} {position['size']})")
                    
                    order_id = self.bybit_client.place_order(
                        side=side,
                        order_type="Market",
                        qty=position_size
                    )
                    
                    if order_id:
                        closed_count += 1
                        self.logger.log_trade("POSITION_CLOSED", self.trading_config.symbol, side, position_size, 0, order_id)
                    else:
                        self.logger.warning(f"Failed to close position: {position['side']} {position['size']}")
            
            if closed_count > 0:
                self.logger.info(f"Closed {closed_count} existing positions")
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing positions: {e}")
            return False
    
    def update_grid(self) -> bool:
        """Update grid based on filled orders"""
        try:
            if not self.active:
                return True
            
            # Get current open orders
            open_orders = self.bybit_client.get_open_orders()
            if not open_orders:
                return True
            
            open_order_ids = {order['orderId'] for order in open_orders}
            
            # Check for filled orders and update grid
            filled_orders = 0
            for level in self.grid_levels:
                if level.order_id and level.order_id not in open_order_ids and not level.filled:
                    # Order was filled
                    level.filled = True
                    level.fill_time = time.time()
                    filled_orders += 1
                    
                    # Log the fill
                    self.logger.log_trade(
                        "ORDER_FILLED",
                        self.trading_config.symbol,
                        level.side,
                        level.quantity,
                        level.price,
                        level.order_id
                    )
                    
                    # Place opposite order
                    self._place_opposite_order(level)
            
            if filled_orders > 0:
                active_orders = sum(1 for level in self.grid_levels if level.order_id and not level.filled)
                total_filled = sum(1 for level in self.grid_levels if level.filled)
                self.logger.log_grid_update(self.trading_config.symbol, active_orders, total_filled)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating grid: {e}")
            return False
    
    def _place_opposite_order(self, filled_level: GridLevel) -> bool:
        # FIXED: Disable opposite order logic entirely
        # In a proper grid strategy, we don't need to place opposite orders
        # The grid levels should work naturally without additional orders
        self.logger.info(f"Grid level {filled_level.level} filled - letting grid work naturally")
        return True
    
    def get_grid_status(self) -> Dict[str, any]:
        """Get current grid status"""
        active_orders = sum(1 for level in self.grid_levels if level.order_id and not level.filled)
        filled_orders = sum(1 for level in self.grid_levels if level.filled)
        total_levels = len(self.grid_levels)
        
        return {
            "active": self.active,
            "total_levels": total_levels,
            "active_orders": active_orders,
            "filled_orders": filled_orders,
            "current_price": self.current_price,
            "grid_range": {
                "lower": self.grid_config.lower_price,
                "upper": self.grid_config.upper_price
            }
        }
    
    def get_grid_pnl(self) -> float:
        """Calculate current grid PnL"""
        try:
            # Get current positions
            positions = self.bybit_client.get_positions()
            if not positions:
                return 0.0
            
            total_pnl = 0.0
            for position in positions:
                if position['symbol'] == self.trading_config.symbol:
                    total_pnl += float(position.get('unrealisedPnl', 0))
            
            return total_pnl
            
        except Exception as e:
            self.logger.error(f"Error calculating grid PnL: {e}")
            return 0.0
    
    def is_active(self) -> bool:
        """Check if grid is active"""
        return self.active
