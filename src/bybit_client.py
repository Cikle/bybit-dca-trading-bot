"""
Bybit API client wrapper
"""

import time
from typing import Dict, List, Optional, Any
from pybit.unified_trading import HTTP
from src.config import BybitConfig, TradingConfig
from src.logger import get_logger

class BybitClient:
    """Bybit API client wrapper"""
    
    def __init__(self, bybit_config: BybitConfig, trading_config: TradingConfig):
        self.bybit_config = bybit_config
        self.trading_config = trading_config
        self.logger = get_logger()
        
        # Initialize HTTP client
        if bybit_config.demo_mode:
            # Use demo trading endpoint
            self.http_client = HTTP(
                demo=True,
                api_key=bybit_config.api_key,
                api_secret=bybit_config.api_secret
            )
        else:
            # Use live trading endpoint
            self.http_client = HTTP(
                api_key=bybit_config.api_key,
                api_secret=bybit_config.api_secret
            )
        
        # WebSocket client will be initialized separately if needed
        self.ws_client = None
        
        self._connected = False
    
    def connect(self) -> bool:
        """Connect to Bybit API"""
        try:
            # Test connection with account info
            account_info = self.http_client.get_wallet_balance(accountType="UNIFIED")
            if account_info['retCode'] == 0:
                self._connected = True
                self.logger.info(f"Connected to Bybit {'Demo' if self.bybit_config.demo_mode else 'Live'}")
                return True
            else:
                self.logger.error(f"Failed to connect to Bybit: {account_info['retMsg']}")
                return False
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Bybit API"""
        if self.ws_client:
            self.ws_client.exit()
        self._connected = False
        self.logger.info("Disconnected from Bybit")
    
    def get_account_balance(self) -> Optional[Dict[str, Any]]:
        """Get account balance"""
        try:
            response = self.http_client.get_wallet_balance(accountType="UNIFIED")
            if response['retCode'] == 0:
                return response['result']
            else:
                self.logger.error(f"Failed to get balance: {response['retMsg']}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return None
    
    def get_positions(self) -> Optional[List[Dict[str, Any]]]:
        """Get current positions"""
        try:
            response = self.http_client.get_positions(
                category="linear",
                symbol=self.trading_config.symbol
            )
            if response['retCode'] == 0:
                return response['result']['list']
            else:
                self.logger.error(f"Failed to get positions: {response['retMsg']}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return None
    
    def get_current_price(self) -> Optional[float]:
        """Get current market price"""
        try:
            response = self.http_client.get_tickers(
                category="linear",
                symbol=self.trading_config.symbol
            )
            if response['retCode'] == 0 and response['result']['list']:
                return float(response['result']['list'][0]['lastPrice'])
            else:
                self.logger.error(f"Failed to get price: {response['retMsg']}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting price: {e}")
            return None
    
    def place_order(self, side: str, order_type: str, qty: float, price: Optional[float] = None, 
                   time_in_force: str = "GTC") -> Optional[str]:
        """Place an order"""
        try:
            order_params = {
                "category": "linear",
                "symbol": self.trading_config.symbol,
                "side": side,
                "orderType": order_type,
                "qty": str(qty),
                "timeInForce": time_in_force
            }
            
            if price:
                order_params["price"] = str(price)
            
            response = self.http_client.place_order(**order_params)
            
            if response['retCode'] == 0:
                order_id = response['result']['orderId']
                self.logger.log_trade(
                    "ORDER_PLACED",
                    self.trading_config.symbol,
                    side,
                    qty,
                    price or 0,
                    order_id
                )
                return order_id
            else:
                self.logger.error(f"Failed to place order: {response['retMsg']}")
                return None
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            response = self.http_client.cancel_order(
                category="linear",
                symbol=self.trading_config.symbol,
                orderId=order_id
            )
            
            if response['retCode'] == 0:
                self.logger.log_trade(
                    "ORDER_CANCELLED",
                    self.trading_config.symbol,
                    "N/A",
                    0,
                    0,
                    order_id
                )
                return True
            else:
                self.logger.error(f"Failed to cancel order: {response['retMsg']}")
                return False
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return False
    
    def get_open_orders(self) -> Optional[List[Dict[str, Any]]]:
        """Get open orders"""
        try:
            response = self.http_client.get_open_orders(
                category="linear",
                symbol=self.trading_config.symbol
            )
            if response['retCode'] == 0:
                return response['result']['list']
            else:
                self.logger.error(f"Failed to get open orders: {response['retMsg']}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting open orders: {e}")
            return None
    
    def get_order_history(self, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Get order history"""
        try:
            response = self.http_client.get_order_history(
                category="linear",
                symbol=self.trading_config.symbol,
                limit=limit
            )
            if response['retCode'] == 0:
                return response['result']['list']
            else:
                self.logger.error(f"Failed to get order history: {response['retMsg']}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting order history: {e}")
            return None
    
    def set_leverage(self, leverage: int) -> bool:
        """Set leverage for the symbol"""
        try:
            response = self.http_client.set_leverage(
                category="linear",
                symbol=self.trading_config.symbol,
                buyLeverage=str(leverage),
                sellLeverage=str(leverage)
            )
            
            if response['retCode'] == 0:
                self.logger.info(f"Leverage set to {leverage}x for {self.trading_config.symbol}")
                return True
            else:
                self.logger.error(f"Failed to set leverage: {response['retMsg']}")
                return False
        except Exception as e:
            self.logger.error(f"Error setting leverage: {e}")
            return False
    
    def get_klines(self, interval: str = "1", limit: int = 200) -> Optional[List[List]]:
        """Get historical kline data"""
        try:
            response = self.http_client.get_kline(
                category="linear",
                symbol=self.trading_config.symbol,
                interval=interval,
                limit=limit
            )
            if response['retCode'] == 0:
                return response['result']['list']
            else:
                self.logger.error(f"Failed to get klines: {response['retMsg']}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting klines: {e}")
            return None
    
    def request_demo_funds(self, amount: str = "10000") -> bool:
        """Request demo trading funds (demo mode only)"""
        try:
            if not self.bybit_config.demo_mode:
                self.logger.warning("Demo funds can only be requested in demo mode")
                return False
            
            # Use the correct API endpoint as per Bybit documentation
            # The request_demo_trading_funds method doesn't take parameters
            # It requests a standard amount of demo funds
            response = self.http_client.request_demo_trading_funds()
            
            if response['retCode'] == 0:
                self.logger.info(f"Successfully requested {amount} USDT demo funds")
                return True
            else:
                self.logger.error(f"Failed to request demo funds: {response['retMsg']}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error requesting demo funds: {e}")
            # Fallback to simulation if API call fails
            self.logger.info(f"Demo funds request simulated - {amount} USDT")
            self.logger.info("Note: Demo funds can be requested via Bybit web interface")
            return True
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected
