#!/usr/bin/env python3
"""
Terminal Dashboard - A tool to monitor website uptime with a colorful terminal display.
"""
import requests
import yaml
import time
import logging
import warnings

# Suppress urllib3 OpenSSL warnings
warnings.filterwarnings('ignore', message='.*OpenSSL.*')

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from datetime import datetime
import concurrent.futures

# Load website list from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

websites = config['websites']

# Initialize rich console for colorful terminal output
console = Console()

# Function to check the status of a website
# Returns True if the website is up (status code 200), otherwise False
def check_status(website):
    try:
        response = requests.get(website, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Initialize a dictionary to keep track of the status history of each website
def initialize_status_history(websites):
    return {website: [] for website in websites}

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
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _initialize_status_history(self) -> Dict[str, List[Dict[str, Any]]]:
        return {website: [] for website in self.websites}

    def _get_terminal_size(self) -> Tuple[int, int]:
        # Implement terminal size detection
        pass

# Main loop to continuously check the status of websites
status_history = initialize_status_history(websites)
with Live(console=console, refresh_per_second=1):
    while True:
        # Run health checks in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(check_status, websites)
            for website, is_up in zip(websites, results):
                status_history[website].append(is_up)
        # Clear the console for the next update
        console.clear()
        # Print the status of each website
        for website, statuses in status_history.items():
            status_line = f"{website:<50}: " + " ".join(
                f"[{'green' if status else 'red'}]●[/{'green' if status else 'red'}]" for status in statuses
            )
            console.print(status_line)
        # Wait for 60 seconds before the next check
        time.sleep(60)
