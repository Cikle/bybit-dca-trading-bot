#!/usr/bin/env python3
"""
Auto-Recovery Trading Bot
This bot will automatically restart itself if it crashes and implement self-healing mechanisms
"""

import time
import sys
import os
import signal
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.config import Config
from src.trading_bot import TradingBot
from src.logger import setup_logger

class AutoRecoveryBot:
    """Trading bot with auto-recovery capabilities"""
    
    def __init__(self):
        self.config = None
        self.bot = None
        self.running = False
        self.restart_count = 0
        self.max_restarts_per_hour = 10
        self.restart_times = []
        self.last_health_check = 0
        self.health_check_interval = 30  # seconds
        self.recovery_thread = None
        
    def load_config(self):
        """Load configuration"""
        try:
            self.config = Config.load()
            setup_logger(self.config.logging)
            return True
        except Exception as e:
            print(f"❌ Failed to load config: {e}")
            return False
    
    def create_bot(self):
        """Create a new bot instance"""
        try:
            self.bot = TradingBot(self.config)
            return True
        except Exception as e:
            print(f"❌ Failed to create bot: {e}")
            return False
    
    def start_bot(self):
        """Start the trading bot"""
        try:
            if not self.bot:
                if not self.create_bot():
                    return False
            
            print(f"🚀 Starting trading bot (attempt #{self.restart_count + 1})...")
            success = self.bot.start()
            
            if success:
                print("✅ Bot started successfully!")
                self.running = True
                return True
            else:
                print("❌ Bot failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            return False
    
    def stop_bot(self):
        """Stop the trading bot"""
        try:
            if self.bot:
                print("🛑 Stopping trading bot...")
                self.bot.stop()
                self.running = False
                print("✅ Bot stopped")
        except Exception as e:
            print(f"❌ Error stopping bot: {e}")
    
    def health_check(self):
        """Perform health check on the bot"""
        try:
            if not self.bot:
                return False
            
            health = self.bot.health_check()
            
            # Check critical health indicators
            critical_issues = []
            if not health.get("bot_running"):
                critical_issues.append("Bot not running")
            if not health.get("main_thread_alive"):
                critical_issues.append("Main thread dead")
            if not health.get("bybit_connected"):
                critical_issues.append("Bybit disconnected")
            if not health.get("api_connection"):
                critical_issues.append("API connection failed")
            if health.get("risk_switch_triggered"):
                critical_issues.append("Risk switch triggered")
            
            if critical_issues:
                print(f"🚨 Health check failed: {', '.join(critical_issues)}")
                return False
            else:
                return True
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def can_restart(self):
        """Check if we can restart (rate limiting)"""
        now = time.time()
        
        # Remove restart times older than 1 hour
        self.restart_times = [t for t in self.restart_times if now - t < 3600]
        
        # Check if we've exceeded restart limit
        if len(self.restart_times) >= self.max_restarts_per_hour:
            print(f"⚠️ Too many restarts ({len(self.restart_times)}) in the last hour. Waiting...")
            return False
        
        return True
    
    def restart_bot(self, reason="Unknown"):
        """Restart the bot with recovery mechanisms"""
        if not self.can_restart():
            return False
        
        self.restart_count += 1
        self.restart_times.append(time.time())
        
        print(f"🔄 Restarting bot (reason: {reason}) - Attempt #{self.restart_count}")
        
        # Stop current bot
        self.stop_bot()
        
        # Wait a bit before restarting
        time.sleep(5)
        
        # Try to restart
        return self.start_bot()
    
    def self_heal(self):
        """Attempt to heal the bot without full restart"""
        try:
            print("🔧 Attempting self-healing...")
            
            if not self.bot:
                return False
            
            # Try to reconnect to Bybit
            if not self.bot.bybit_client.is_connected():
                print("🔌 Reconnecting to Bybit...")
                if self.bot.bybit_client.connect():
                    print("✅ Reconnected to Bybit")
                else:
                    print("❌ Failed to reconnect to Bybit")
                    return False
            
            # Check if grid is still active
            if not self.bot.grid_engine.is_active():
                print("🔄 Restarting grid engine...")
                if self.bot.grid_engine.start_grid():
                    print("✅ Grid engine restarted")
                else:
                    print("❌ Failed to restart grid engine")
                    return False
            
            # Check if DCA is still active
            if not self.bot.dca_engine.is_active():
                print("🔄 Restarting DCA engine...")
                if self.bot.dca_engine.start_dca():
                    print("✅ DCA engine restarted")
                else:
                    print("❌ Failed to restart DCA engine")
                    return False
            
            print("✅ Self-healing completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Self-healing failed: {e}")
            return False
    
    def recovery_loop(self):
        """Main recovery loop that monitors and heals the bot"""
        print("🛡️ Auto-recovery system started")
        
        while True:
            try:
                time.sleep(self.health_check_interval)
                
                if not self.running:
                    continue
                
                # Perform health check
                if not self.health_check():
                    print("🚨 Health check failed, attempting recovery...")
                    
                    # Try self-healing first
                    if self.self_heal():
                        print("✅ Self-healing successful")
                        continue
                    
                    # If self-healing fails, restart the bot
                    if not self.restart_bot("Health check failed"):
                        print("❌ Failed to restart bot after health check failure")
                        # Wait longer before next attempt
                        time.sleep(60)
                
            except Exception as e:
                print(f"❌ Error in recovery loop: {e}")
                time.sleep(30)
    
    def run(self):
        """Main run loop with auto-recovery"""
        print("🤖 Auto-Recovery Trading Bot Starting...")
        print("=" * 60)
        
        # Load configuration
        if not self.load_config():
            print("❌ Failed to load configuration")
            return False
        
        # Start recovery thread
        self.recovery_thread = threading.Thread(target=self.recovery_loop, daemon=True)
        self.recovery_thread.start()
        
        # Main bot loop
        while True:
            try:
                # Start the bot
                if not self.start_bot():
                    print("❌ Failed to start bot, waiting before retry...")
                    time.sleep(30)
                    continue
                
                # Monitor the bot
                while self.running and self.bot and self.bot.is_running():
                    time.sleep(5)
                
                # Bot stopped, try to restart
                if self.running:
                    print("🔄 Bot stopped unexpectedly, attempting restart...")
                    if not self.restart_bot("Bot stopped unexpectedly"):
                        print("❌ Failed to restart bot, waiting before retry...")
                        time.sleep(60)
                
            except KeyboardInterrupt:
                print("\n🛑 Received interrupt signal, shutting down...")
                self.stop_bot()
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                self.stop_bot()
                time.sleep(30)
        
        print("👋 Auto-Recovery Bot stopped")
        return True

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print("\n🛑 Received interrupt signal. Shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run auto-recovery bot
    auto_bot = AutoRecoveryBot()
    auto_bot.run()
