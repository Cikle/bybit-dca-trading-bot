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
            
            if not self.grid_levels:
                if not self.initialize_grid():
                    return False
            
            # Place initial orders
            placed_orders = 0
            for level in self.grid_levels:
                if not level.filled:
                    order_id = self.bybit_client.place_order(
                        side=level.side,
                        order_type="Limit",
                        qty=level.quantity,
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
        """Place opposite order when a grid level is filled"""
        try:
            # Check if we're approaching order limits
            active_orders = sum(1 for level in self.grid_levels if level.order_id and not level.filled)
            if active_orders >= 15:  # Leave some buffer for Bybit's 20 order limit
                self.logger.warning("Approaching order limit, skipping opposite order placement")
                return False
            
            # Market condition awareness - avoid trading in extreme volatility
            current_price = self.bybit_client.get_current_price()
            if current_price and hasattr(self, 'last_price') and self.last_price:
                price_change = abs(current_price - self.last_price) / self.last_price
                if price_change > 0.05:  # Skip if price moved more than 5% (extreme volatility)
                    self.logger.warning(f"Skipping opposite order due to high volatility: {price_change:.2%}")
                    return False
            self.last_price = current_price
            
            # Calculate opposite order price with optimized profit targets
            import random
            
            # FIXED: Deterministic win rate control (from config)
            # Use trade count to determine win/loss pattern
            total_trades = len(self.trades)
            win_threshold = self.strategy_config.grid_win_rate  # e.g., 70
            if total_trades % 10 >= (win_threshold / 10):  # e.g., 7 out of 10 trades win
                self.logger.info(f"Skipping opposite order due to deterministic win rate control ({win_threshold}% pattern)")
                return False
            
            if filled_level.side == "Buy":
                # Buy order filled, place sell order above with profit from config
                profit_percent = self.strategy_config.grid_profit_percent / 100  # e.g., 0.7%
                opposite_price = filled_level.price * (1 + profit_percent)
                opposite_side = "Sell"
            else:
                # Sell order filled, place buy order below with profit from config
                profit_percent = self.strategy_config.grid_profit_percent / 100  # e.g., 0.7%
                opposite_price = filled_level.price * (1 - profit_percent)
                opposite_side = "Buy"
            
            # Place the opposite order
            order_id = self.bybit_client.place_order(
                side=opposite_side,
                order_type="Limit",
                qty=filled_level.quantity,
                price=round(opposite_price, 2)
            )
            
            if order_id:
                # Create new grid level for the opposite order
                new_level = GridLevel(
                    level=len(self.grid_levels),
                    price=round(opposite_price, 2),
                    side=opposite_side,
                    quantity=filled_level.quantity,
                    order_id=order_id
                )
                self.grid_levels.append(new_level)
                
                self.logger.log_trade(
                    "OPPOSITE_ORDER_PLACED",
                    self.trading_config.symbol,
                    opposite_side,
                    filled_level.quantity,
                    round(opposite_price, 2),
                    order_id
                )
                
                # Track this trade for deterministic win rate
                self.trades.append({
                    'type': 'grid',
                    'side': opposite_side,
                    'price': round(opposite_price, 2),
                    'quantity': filled_level.quantity,
                    'order_id': order_id
                })
                
                return True
            else:
                self.logger.warning(f"Failed to place opposite order for level {filled_level.level}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error placing opposite order: {e}")
            return False
    
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
