#!/usr/bin/env python3
"""
Main CLI interface for the Leveraged Grid + DCA Hybrid Trading Bot
"""

import sys
import time
import signal
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.config import Config
from src.trading_bot import TradingBot
from src.logger import setup_logger

app = typer.Typer(help="Leveraged Grid + DCA Hybrid Trading Bot for Bybit")
console = Console()

# Global bot instance
bot: Optional[TradingBot] = None

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    console.print("\n[yellow]Received interrupt signal. Stopping bot...[/yellow]")
    if bot:
        bot.stop()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@app.command()
def start(
    demo: bool = typer.Option(True, "--demo/--live", help="Run in demo mode (default) or live mode"),
    config_file: Optional[str] = typer.Option(None, "--config", help="Path to custom config file")
):
    """Start the trading bot"""
    global bot
    
    try:
        # Load configuration
        config = Config.load()
        
        # Override demo mode setting based on demo flag
        config.bybit.demo_mode = demo
        
        # Validate configuration
        if not config.validate():
            console.print("[red]❌ Configuration validation failed[/red]")
            raise typer.Exit(1)
        
        # Setup logger
        setup_logger(config.logging)
        
        # Create and start bot
        bot = TradingBot(config)
        
        # Display startup information
        display_startup_info(config, demo)
        
        # Start the bot
        if bot.start():
            console.print("[green]✅ Bot started successfully![/green]")
            console.print("[yellow]Press Ctrl+C to stop the bot[/yellow]")
            
            # Keep the main thread alive
            try:
                while bot.is_running():
                    time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping bot...[/yellow]")
                bot.stop()
        else:
            console.print("[red]❌ Failed to start bot[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def stop():
    """Stop the trading bot"""
    global bot
    
    if bot and bot.is_running():
        if bot.stop():
            console.print("[green]✅ Bot stopped successfully[/green]")
        else:
            console.print("[red]❌ Failed to stop bot[/red]")
            raise typer.Exit(1)
    else:
        console.print("[yellow]⚠️ Bot is not running[/yellow]")

@app.command()
def status():
    """Show current bot status"""
    global bot
    
    if not bot:
        console.print("[yellow]⚠️ Bot is not initialized[/yellow]")
        return
    
    try:
        status_info = bot.get_status()
        display_status(status_info)
        
    except Exception as e:
        console.print(f"[red]❌ Error getting status: {e}[/red]")

@app.command()
def performance():
    """Show performance metrics"""
    global bot
    
    if not bot:
        console.print("[yellow]⚠️ Bot is not initialized[/yellow]")
        return
    
    try:
        metrics = bot.get_performance_metrics()
        display_performance(metrics)
        
    except Exception as e:
        console.print(f"[red]❌ Error getting performance: {e}[/red]")

@app.command()
def emergency():
    """Emergency stop - trigger kill switch"""
    global bot
    
    if not bot:
        console.print("[yellow]⚠️ Bot is not initialized[/yellow]")
        return
    
    # Confirm emergency stop
    confirm = typer.confirm("Are you sure you want to trigger emergency stop? This will close all positions!")
    if not confirm:
        console.print("[yellow]Emergency stop cancelled[/yellow]")
        return
    
    try:
        if bot.emergency_stop():
            console.print("[red]🚨 Emergency stop executed successfully[/red]")
        else:
            console.print("[red]❌ Failed to execute emergency stop[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error in emergency stop: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def backtest(
    start_date: str = typer.Option("2024-01-01", "--start", help="Start date for backtest (YYYY-MM-DD)"),
    end_date: str = typer.Option("2024-12-31", "--end", help="End date for backtest (YYYY-MM-DD)"),
    export: Optional[str] = typer.Option(None, "--export", help="Export results to CSV file")
):
    """Run backtest on historical data"""
    try:
        # Load configuration
        config = Config.load()
        
        # Update backtest dates
        config.backtest.start_date = start_date
        config.backtest.end_date = end_date
        
        # Setup logger
        setup_logger(config.logging)
        
        # Create backtest engine
        from src.backtest import BacktestEngine
        backtest_engine = BacktestEngine(config)
        
        console.print(f"[blue]Loading data from {start_date} to {end_date}...[/blue]")
        
        # Load data
        if not backtest_engine.load_data():
            console.print("[red]❌ Failed to load historical data[/red]")
            raise typer.Exit(1)
        
        console.print("[blue]Running backtest...[/blue]")
        
        # Run backtest
        result = backtest_engine.run_backtest()
        
        # Display results
        display_backtest_results(result)
        
        # Export if requested
        if export:
            backtest_engine.export_results(export)
            console.print(f"[green]✅ Results exported to {export}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error running backtest: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def demo_funds(
    amount: str = typer.Option("10000", "--amount", help="Amount of USDT to request")
):
    """Request demo trading funds"""
    try:
        # Load configuration
        config = Config.load()
        
        # Setup logger
        setup_logger(config.logging)
        
        # Create client
        from src.bybit_client import BybitClient
        client = BybitClient(config.bybit, config.trading)
        
        # Connect and request funds
        if client.connect():
            if client.request_demo_funds(amount):
                console.print(f"[green]✅ Successfully requested {amount} USDT demo funds[/green]")
            else:
                console.print("[red]❌ Failed to request demo funds[/red]")
                raise typer.Exit(1)
        else:
            console.print("[red]❌ Failed to connect to Bybit[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error requesting demo funds: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def setup():
    """Run initial setup"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, "setup.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✅ Setup completed successfully![/green]")
            console.print(result.stdout)
        else:
            console.print("[red]❌ Setup failed[/red]")
            console.print(result.stderr)
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error running setup: {e}[/red]")
        raise typer.Exit(1)

def display_startup_info(config: Config, demo: bool):
    """Display startup information"""
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        f"[bold blue]Leveraged Grid + DCA Hybrid Trading Bot[/bold blue]\n"
        f"[green]Mode:[/green] {'DEMO' if demo else 'LIVE'}\n"
        f"[green]Symbol:[/green] {config.trading.symbol}\n"
        f"[green]Leverage:[/green] {config.trading.leverage}x\n"
        f"[green]Initial Capital:[/green] ${config.trading.initial_capital}",
        title="Bot Configuration",
        border_style="blue"
    ))
    
    # Grid configuration
    console.print(Panel.fit(
        f"[green]Grid Range:[/green] ${config.grid.lower_price} - ${config.grid.upper_price}\n"
        f"[green]Grid Levels:[/green] {config.grid.levels}\n"
        f"[green]Order Size:[/green] {config.grid.order_size} {config.trading.symbol.replace('USDT', '')}",
        title="Grid Configuration",
        border_style="green"
    ))
    
    # DCA configuration
    if config.dca.enabled:
        console.print(Panel.fit(
            f"[green]DCA Enabled:[/green] Yes\n"
            f"[green]Trigger Percent:[/green] {config.dca.trigger_percent}%\n"
            f"[green]Max Orders:[/green] {config.dca.max_orders}\n"
            f"[green]Order Size:[/green] {config.dca.order_size} {config.trading.symbol.replace('USDT', '')}",
            title="DCA Configuration",
            border_style="yellow"
        ))
    
    # Risk management
    console.print(Panel.fit(
        f"[green]Kill Switch:[/green] {'Enabled' if config.risk.kill_switch_enabled else 'Disabled'}\n"
        f"[green]Max Drawdown:[/green] {config.risk.max_drawdown_percent}%\n"
        f"[green]Breakeven:[/green] {'Enabled' if config.risk.breakeven_enabled else 'Disabled'}\n"
        f"[green]Partial Profit:[/green] {'Enabled' if config.risk.partial_profit_enabled else 'Disabled'}",
        title="Risk Management",
        border_style="red"
    ))
    
    console.print("="*60 + "\n")

def display_status(status_info: dict):
    """Display bot status"""
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        f"[green]Status:[/green] {'🟢 Running' if status_info.get('running') else '🔴 Stopped'}\n"
        f"[green]Connected:[/green] {'✅ Yes' if status_info.get('connected') else '❌ No'}",
        title="Bot Status",
        border_style="blue"
    ))
    
    # Grid status
    grid_status = status_info.get('grid_status', {})
    console.print(Panel.fit(
        f"[green]Active:[/green] {'Yes' if grid_status.get('active') else 'No'}\n"
        f"[green]Total Levels:[/green] {grid_status.get('total_levels', 0)}\n"
        f"[green]Active Orders:[/green] {grid_status.get('active_orders', 0)}\n"
        f"[green]Filled Orders:[/green] {grid_status.get('filled_orders', 0)}\n"
        f"[green]Current Price:[/green] ${grid_status.get('current_price', 0):.2f}",
        title="Grid Status",
        border_style="green"
    ))
    
    # DCA status
    dca_status = status_info.get('dca_status', {})
    if dca_status.get('enabled'):
        console.print(Panel.fit(
            f"[green]Active:[/green] {'Yes' if dca_status.get('active') else 'No'}\n"
            f"[green]Trend Direction:[/green] {dca_status.get('trend_direction', 'none')}\n"
            f"[green]Active Orders:[/green] {dca_status.get('active_orders', 0)}\n"
            f"[green]Filled Orders:[/green] {dca_status.get('filled_orders', 0)}",
            title="DCA Status",
            border_style="yellow"
        ))
    
    # Risk status
    risk_status = status_info.get('risk_status', {})
    console.print(Panel.fit(
        f"[green]Kill Switch:[/green] {'🚨 TRIGGERED' if risk_status.get('kill_switch_triggered') else '✅ Normal'}\n"
        f"[green]Current Drawdown:[/green] {risk_status.get('current_drawdown', 0):.2f}%\n"
        f"[green]Max Drawdown:[/green] {risk_status.get('max_drawdown_reached', 0):.2f}%",
        title="Risk Status",
        border_style="red"
    ))
    
    console.print("="*60 + "\n")

def display_performance(metrics: dict):
    """Display performance metrics"""
    if "error" in metrics:
        console.print(f"[red]❌ Error: {metrics['error']}[/red]")
        return
    
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        f"[green]Initial Capital:[/green] ${metrics.get('initial_capital', 0):.2f}\n"
        f"[green]Current Balance:[/green] ${metrics.get('current_balance', 0):.2f}\n"
        f"[green]Total Return:[/green] {metrics.get('total_return_percent', 0):.2f}%\n"
        f"[green]Unrealized PnL:[/green] ${metrics.get('unrealized_pnl', 0):.2f}\n"
        f"[green]Realized PnL:[/green] ${metrics.get('realized_pnl', 0):.2f}",
        title="Performance Metrics",
        border_style="blue"
    ))
    
    console.print(Panel.fit(
        f"[green]Max Drawdown:[/green] {metrics.get('max_drawdown', 0):.2f}%\n"
        f"[green]Current Drawdown:[/green] {metrics.get('current_drawdown', 0):.2f}%\n"
        f"[green]Margin Ratio:[/green] {metrics.get('margin_ratio', 0):.2f}%",
        title="Risk Metrics",
        border_style="red"
    ))
    
    console.print("="*60 + "\n")

def display_backtest_results(result):
    """Display backtest results"""
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        f"[green]Period:[/green] {result.start_date} to {result.end_date}\n"
        f"[green]Initial Capital:[/green] ${result.initial_capital:.2f}\n"
        f"[green]Final Capital:[/green] ${result.final_capital:.2f}\n"
        f"[green]Total Return:[/green] {result.total_return:.2f}%\n"
        f"[green]Max Drawdown:[/green] {result.max_drawdown:.2f}%",
        title="Backtest Results",
        border_style="blue"
    ))
    
    console.print(Panel.fit(
        f"[green]Total Trades:[/green] {result.total_trades}\n"
        f"[green]Winning Trades:[/green] {result.winning_trades}\n"
        f"[green]Losing Trades:[/green] {result.losing_trades}\n"
        f"[green]Win Rate:[/green] {result.win_rate:.2f}%\n"
        f"[green]Profit Factor:[/green] {result.profit_factor:.2f}",
        title="Trade Statistics",
        border_style="green"
    ))
    
    console.print(Panel.fit(
        f"[green]Average Win:[/green] ${result.avg_win:.2f}\n"
        f"[green]Average Loss:[/green] ${result.avg_loss:.2f}\n"
        f"[green]Sharpe Ratio:[/green] {result.sharpe_ratio:.2f}",
        title="Performance Metrics",
        border_style="yellow"
    ))
    
    console.print("="*60 + "\n")

if __name__ == "__main__":
    app()
