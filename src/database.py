"""
Database module for state persistence
"""

import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from src.config import DatabaseConfig
from src.logger import get_logger

class Database:
    """SQLite database wrapper for trading bot state"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.logger = get_logger()
        self.connection: Optional[sqlite3.Connection] = None
        
    def connect(self) -> bool:
        """Connect to database"""
        try:
            # Extract database path from URL
            db_path = self.config.url.replace("sqlite:///", "")
            
            # Create directory if it doesn't exist
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            
            # Create tables
            self._create_tables()
            
            self.logger.info(f"Connected to database: {db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Disconnected from database")
    
    def _create_tables(self):
        """Create database tables"""
        try:
            cursor = self.connection.cursor()
            
            # Bot state table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_state (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Trade history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    trade_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    balance REAL NOT NULL,
                    equity REAL NOT NULL,
                    unrealized_pnl REAL NOT NULL,
                    realized_pnl REAL NOT NULL,
                    drawdown REAL NOT NULL,
                    margin_ratio REAL NOT NULL
                )
            """)
            
            # Grid levels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS grid_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level INTEGER NOT NULL,
                    price REAL NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    order_id TEXT,
                    filled BOOLEAN DEFAULT FALSE,
                    fill_price REAL,
                    fill_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # DCA levels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dca_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level INTEGER NOT NULL,
                    trigger_price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    order_id TEXT,
                    filled BOOLEAN DEFAULT FALSE,
                    fill_price REAL,
                    fill_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            self.logger.info("Database tables created successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            raise
    
    def save_bot_state(self, key: str, value: Any) -> bool:
        """Save bot state"""
        try:
            cursor = self.connection.cursor()
            
            # Convert value to string
            value_str = str(value)
            
            cursor.execute("""
                INSERT OR REPLACE INTO bot_state (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value_str))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving bot state: {e}")
            return False
    
    def get_bot_state(self, key: str) -> Optional[str]:
        """Get bot state"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT value FROM bot_state WHERE key = ?", (key,))
            result = cursor.fetchone()
            
            return result['value'] if result else None
            
        except Exception as e:
            self.logger.error(f"Error getting bot state: {e}")
            return None
    
    def save_trade(self, order_id: str, symbol: str, side: str, quantity: float, 
                   price: float, trade_type: str, status: str) -> bool:
        """Save trade to history"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO trade_history 
                (order_id, symbol, side, quantity, price, trade_type, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (order_id, symbol, side, quantity, price, trade_type, status))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving trade: {e}")
            return False
    
    def get_trade_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trade history"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM trade_history 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"Error getting trade history: {e}")
            return []
    
    def save_performance_metrics(self, balance: float, equity: float, unrealized_pnl: float,
                                realized_pnl: float, drawdown: float, margin_ratio: float) -> bool:
        """Save performance metrics"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO performance_metrics 
                (balance, equity, unrealized_pnl, realized_pnl, drawdown, margin_ratio)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (balance, equity, unrealized_pnl, realized_pnl, drawdown, margin_ratio))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving performance metrics: {e}")
            return False
    
    def get_performance_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get performance metrics history"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM performance_metrics 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return []
    
    def save_grid_level(self, level: int, price: float, side: str, quantity: float,
                       order_id: Optional[str] = None) -> bool:
        """Save grid level"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO grid_levels (level, price, side, quantity, order_id)
                VALUES (?, ?, ?, ?, ?)
            """, (level, price, side, quantity, order_id))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving grid level: {e}")
            return False
    
    def update_grid_level(self, order_id: str, filled: bool, fill_price: Optional[float] = None) -> bool:
        """Update grid level status"""
        try:
            cursor = self.connection.cursor()
            
            if filled:
                cursor.execute("""
                    UPDATE grid_levels 
                    SET filled = TRUE, fill_price = ?, fill_time = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                """, (fill_price, order_id))
            else:
                cursor.execute("""
                    UPDATE grid_levels 
                    SET order_id = NULL
                    WHERE order_id = ?
                """, (order_id,))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating grid level: {e}")
            return False
    
    def get_grid_levels(self) -> List[Dict[str, Any]]:
        """Get all grid levels"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM grid_levels ORDER BY level")
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"Error getting grid levels: {e}")
            return []
    
    def save_dca_level(self, level: int, trigger_price: float, quantity: float,
                      order_id: Optional[str] = None) -> bool:
        """Save DCA level"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO dca_levels (level, trigger_price, quantity, order_id)
                VALUES (?, ?, ?, ?)
            """, (level, trigger_price, quantity, order_id))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving DCA level: {e}")
            return False
    
    def update_dca_level(self, order_id: str, filled: bool, fill_price: Optional[float] = None) -> bool:
        """Update DCA level status"""
        try:
            cursor = self.connection.cursor()
            
            if filled:
                cursor.execute("""
                    UPDATE dca_levels 
                    SET filled = TRUE, fill_price = ?, fill_time = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                """, (fill_price, order_id))
            else:
                cursor.execute("""
                    UPDATE dca_levels 
                    SET order_id = NULL
                    WHERE order_id = ?
                """, (order_id,))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating DCA level: {e}")
            return False
    
    def get_dca_levels(self) -> List[Dict[str, Any]]:
        """Get all DCA levels"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM dca_levels ORDER BY level")
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"Error getting DCA levels: {e}")
            return []
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data"""
        try:
            cursor = self.connection.cursor()
            
            # Clean up old performance metrics
            cursor.execute("""
                DELETE FROM performance_metrics 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days))
            
            # Clean up old trade history (keep filled trades)
            cursor.execute("""
                DELETE FROM trade_history 
                WHERE status != 'FILLED' 
                AND created_at < datetime('now', '-{} days')
            """.format(days))
            
            self.connection.commit()
            self.logger.info(f"Cleaned up data older than {days} days")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
