#!/usr/bin/env python3
"""
Terminal Dashboard - A tool to monitor website uptime with a colorful terminal display.
"""
import requests
import yaml
import time
import logging
import warnings
import argparse
import os
import shutil  # For getting terminal size
import math  # For ceiling division
from typing import Dict, List, Tuple, Any, Optional

# Suppress urllib3 OpenSSL warnings
warnings.filterwarnings('ignore', message='.*OpenSSL.*')

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.table import Table
from datetime import datetime
import concurrent.futures

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='dashboard.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

class WebsiteMonitor:
    """Class to monitor website status and display results in terminal."""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """Initialize the monitor with configuration."""
        self.config = self._load_config(config_path)
        self.websites = self.config['websites']
        # Support both naming conventions from config
        self.check_interval = self.config.get('check_interval', self.config.get('refresh_interval_seconds', 60))
        self.timeout = self.config.get('timeout', self.config.get('timeout_seconds', 10))
        self.history_size = self.config.get('history_size', self.config.get('max_history_length', 10))
        self.status_history: Dict[str, List[Dict[str, Any]]] = self._initialize_status_history()
        self.console = Console()
        self.session = requests.Session()  # Use session for connection pooling
        self.last_terminal_size = self._get_terminal_size()  # Store initial terminal size
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Provide a minimal default config if loading fails
            return {'websites': ['https://www.google.com'], 'check_interval': 60, 'timeout': 10, 'history_size': 10}
    
    def _initialize_status_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize the status history dictionary."""
        return {website: [] for website in self.websites}
    
    def _get_terminal_size(self) -> Tuple[int, int]:
        """Get the current terminal size (columns, rows)."""
        try:
            columns, rows = shutil.get_terminal_size()
            return columns, rows
        except Exception as e:
            logger.warning(f"Failed to get terminal size: {e}. Using default size.")
            return 80, 24  # Default fallback size
    
    def _calculate_visible_websites_count(self) -> int:
        """Calculate how many websites can fit in the current terminal window."""
        _, rows = self._get_terminal_size()
        
        # Account for header (2 lines), table header (2 lines), and footer space (1 line)
        available_rows = rows - 5
        
        # Ensure at least one website is shown
        return max(1, available_rows)
    
    def check_status(self, website: str) -> Dict[str, Any]:
        """Check the status of a website and return detailed results."""
        start_time = time.time()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        
        try:
            response = self.session.get(website, timeout=self.timeout, headers=headers)
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return {
                'timestamp': datetime.now(),
                'status_code': response.status_code,
                'response_time': response_time,
                'is_error': False,
                'is_up': 200 <= response.status_code < 400  # Consider 2xx and 3xx as UP
            }
        except Exception as e:
            logger.error(f"Error checking {website}: {str(e)}")
            return {
                'timestamp': datetime.now(),
                'status_code': None,
                'response_time': None,
                'is_error': True,
                'error_message': str(e),
                'is_up': False  # Any exception means the site is DOWN
            }
    
    def update_status_history(self, website: str, status: Dict[str, Any]) -> None:
        """Update the status history for a website, maintaining the history size limit."""
        self.status_history[website].append(status)
        # Keep only the most recent entries based on history_size
        if len(self.status_history[website]) > self.history_size:
            self.status_history[website].pop(0)
    
    def run_health_checks(self) -> None:
        """Run health checks for all websites in parallel."""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_website = {executor.submit(self.check_status, website): website for website in self.websites}
            for future in concurrent.futures.as_completed(future_to_website):
                website = future_to_website[future]
                try:
                    status = future.result()
                    self.update_status_history(website, status)
                    # Log the result
                    log_level = logging.INFO if status['is_up'] else logging.WARNING
                    logger.log(log_level, f"{website} - Status: {'UP' if status['is_up'] else 'DOWN'} - "
                              f"Code: {status['status_code']} - Time: {status['response_time']} ms")
                except Exception as e:
                    logger.error(f"{website} - Error in health check: {e}")
    
    def display_status(self) -> None:
        """Display the status of all websites in the terminal."""
        self.console.clear()
        
        # Get current terminal size
        current_terminal_size = self._get_terminal_size()
        
        # Display header with current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.console.print(f"[bold]Website Status Dashboard[/bold] - Last updated: {current_time}")
        
        # Calculate how many websites can be displayed
        visible_count = self._calculate_visible_websites_count()
        total_websites = len(self.websites)
        
        # Display info about visible/total websites
        self.console.print(f"Showing {min(visible_count, total_websites)} of {total_websites} websites - Resize terminal to see more/less")
        self.console.print("=" * 80)
        
        # Create a table for better columnar display
        table = Table(show_header=True, header_style="bold")
        table.add_column("Website", style="dim", width=50)
        table.add_column("Status", justify="left")
        table.add_column("Latency", justify="right")
        table.add_column("History", justify="left")
        
        # Get a slice of websites based on visible count
        visible_websites = list(self.status_history.keys())[:visible_count]
        
        # Display status for visible websites
        for website in visible_websites:
            statuses = self.status_history[website]
            if not statuses:
                table.add_row(
                    website,
                    "[yellow]No data yet[/yellow]",
                    "",
                    ""
                )
            else:
                latest = statuses[-1]
                
                # Format the status indicator
                if latest['is_up']:
                    status_indicator = f"[green]UP[/green] ({latest['status_code']})"
                else:
                    status_indicator = f"[red]DOWN[/red]({latest['status_code']})"
                
                # Format response time if available
                time_info = f"{latest['response_time']:.2f} ms" if latest['response_time'] else "N/A"
                
                # Create history indicators
                history_indicators = " ".join(
                    f"[{'green' if status['is_up'] else 'red'}]●[/{'green' if status['is_up'] else 'red'}]" 
                    for status in statuses
                )
                
                table.add_row(
                    website,
                    status_indicator,
                    time_info,
                    history_indicators
                )
        
        # Display the table
        self.console.print(table)
        
        # Update last terminal size
        self.last_terminal_size = current_terminal_size
    
    def _has_terminal_size_changed(self) -> bool:
        """Check if the terminal size has changed since the last check."""
        current_size = self._get_terminal_size()
        has_changed = current_size != self.last_terminal_size
        if has_changed:
            logger.info(f"Terminal size changed from {self.last_terminal_size} to {current_size}")
        return has_changed
    
    def run(self) -> None:
        """Run the monitor continuously."""
        logger.info("Starting Website Monitor")
        try:
            # Initial health check and display
            self.run_health_checks()
            self.display_status()
            
            last_health_check = time.time()
            
            with Live(console=self.console, refresh_per_second=1, auto_refresh=False) as live:
                while True:
                    current_time = time.time()
                    
                    # Update on health check interval or terminal resize
                    if (current_time - last_health_check >= self.check_interval or 
                        self._has_terminal_size_changed()):
                        self.run_health_checks()
                        self.display_status()
                        last_health_check = current_time
                        live.refresh()
                    
                    time.sleep(0.5)
                    
        except KeyboardInterrupt:
            logger.info("Stopping Website Monitor")
            print("\nStopping monitor...")
        except Exception as e:
            logger.error(f"Unexpected error in monitor: {e}")
            self.console.print(f"[red]Error: {e}[/red]")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Terminal Dashboard for website monitoring')
    parser.add_argument('-c', '--config', default='config.yaml', help='Path to config file')
    parser.add_argument('-i', '--interval', type=int, help='Check interval in seconds')
    parser.add_argument('-t', '--timeout', type=int, help='Request timeout in seconds')
    parser.add_argument('-s', '--history-size', type=int, help='Number of history entries to display')
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # Create the monitor
    monitor = WebsiteMonitor(config_path=args.config)
    
    # Override config with command line arguments if provided
    if args.interval:
        monitor.check_interval = args.interval
    if args.timeout:
        monitor.timeout = args.timeout
    if args.history_size:
        monitor.history_size = args.history_size
    
    # Run the monitor
    monitor.run()

if __name__ == "__main__":
    main()
