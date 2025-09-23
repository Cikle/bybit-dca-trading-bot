#!/usr/bin/env python3
"""
Bot Health Monitor
Simple script to check if the trading bot is still running and healthy
"""

import time
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config
from src.trading_bot import TradingBot

def check_bot_health():
    """Check if bot is running and healthy"""
    try:
        # Load config
        config = Config.load()
        
        # Create bot instance
        bot = TradingBot(config)
        
        # Perform health check
        health = bot.health_check()
        
        print(f"🤖 Bot Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Check each component
        status_emoji = "✅" if health.get("bot_running") else "❌"
        print(f"{status_emoji} Bot Running: {health.get('bot_running', False)}")
        
        status_emoji = "✅" if health.get("main_thread_alive") else "❌"
        print(f"{status_emoji} Main Thread: {health.get('main_thread_alive', False)}")
        
        status_emoji = "✅" if health.get("bybit_connected") else "❌"
        print(f"{status_emoji} Bybit Connected: {health.get('bybit_connected', False)}")
        
        status_emoji = "✅" if health.get("api_connection") else "❌"
        print(f"{status_emoji} API Connection: {health.get('api_connection', False)}")
        
        status_emoji = "✅" if health.get("grid_active") else "❌"
        print(f"{status_emoji} Grid Active: {health.get('grid_active', False)}")
        
        status_emoji = "✅" if health.get("dca_active") else "❌"
        print(f"{status_emoji} DCA Active: {health.get('dca_active', False)}")
        
        status_emoji = "⚠️" if health.get("risk_switch_triggered") else "✅"
        print(f"{status_emoji} Risk Switch: {health.get('risk_switch_triggered', False)}")
        
        orders_count = health.get("open_orders_count", -1)
        if orders_count >= 0:
            status_emoji = "✅" if orders_count > 0 else "⚠️"
            print(f"{status_emoji} Open Orders: {orders_count}")
        else:
            print("❌ Open Orders: Unable to check")
        
        print("=" * 60)
        
        # Overall health assessment
        critical_issues = []
        if not health.get("bot_running"):
            critical_issues.append("Bot is not running")
        if not health.get("main_thread_alive"):
            critical_issues.append("Main thread is dead")
        if not health.get("bybit_connected"):
            critical_issues.append("Bybit connection lost")
        if not health.get("api_connection"):
            critical_issues.append("API connection failed")
        if health.get("risk_switch_triggered"):
            critical_issues.append("Risk switch triggered")
        
        if critical_issues:
            print("🚨 CRITICAL ISSUES DETECTED:")
            for issue in critical_issues:
                print(f"   - {issue}")
            print("\n💡 Recommendation: Restart the bot with 'python main.py start'")
            return False
        else:
            print("✅ Bot is healthy and running normally!")
            return True
            
    except Exception as e:
        print(f"❌ Error checking bot health: {e}")
        return False

if __name__ == "__main__":
    check_bot_health()
