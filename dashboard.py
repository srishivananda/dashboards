#!/usr/bin/env python3
# Import necessary libraries
import requests
import yaml
import time
from rich.console import Console
from rich.live import Live
from datetime import datetime
import concurrent.futures

# Load website list from config.yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

websites = config['websites']
timeout_seconds = config.get('timeout_seconds', 10)
refresh_interval_seconds = config.get('refresh_interval_seconds', 60)
max_history_length = config.get('max_history_length', 20)

# Initialize rich console for colorful terminal output
console = Console()

# Function to check the status of a website
# Returns True if the website is up (status code 200), otherwise False
def check_status(website):
    try:
        response = requests.get(website, timeout=timeout_seconds)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Initialize a dictionary to keep track of the status history of each website
def initialize_status_history(websites):
    return {website: [] for website in websites}

# Main loop to continuously check the status of websites
status_history = initialize_status_history(websites)
with Live(console=console, refresh_per_second=1):
    while True:
        # Run health checks in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(check_status, websites)
            for website, is_up in zip(websites, results):
                status_history[website].append(is_up)
                if len(status_history[website]) > max_history_length:
                    status_history[website] = status_history[website][-max_history_length:]
        # Clear the console for the next update
        console.clear()
        # Print the status of each website
        for website, statuses in status_history.items():
            status_line = f"{website:<50}: " + " ".join(
                f"[{'green' if status else 'red'}]●[/{'green' if status else 'red'}]" for status in statuses
            )
            console.print(status_line)
        # Wait for configured seconds before the next check
        time.sleep(refresh_interval_seconds)
