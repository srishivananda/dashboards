# Terminal Dashboard

This project is a terminal-based dashboard that monitors the uptime status of specified websites. It displays the status of each website in a color-coded format, updating every minute.

## Features

- **Parallel Health Checks**: Uses Python's `concurrent.futures` to perform website status checks in parallel, improving efficiency.
- **Color-Coded Output**: Utilizes the `rich` library to provide a visually appealing terminal output with color-coded status indicators.
- **Configurable Website List**: Websites to be monitored are specified in a `config.yaml` file, allowing easy updates.
- **Compact Display**: Displays website status in a compact format without using tables, making it suitable for terminal viewing.

## Requirements

- Python 3.x
- `requests` library for HTTP requests
- `PyYAML` for parsing YAML configuration files
- `rich` library for terminal styling

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```

2. Navigate to the project directory:
   ```bash
   cd dashboard
   ```

3. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

4. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

5. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Update the `config.yaml` file with the list of websites you want to monitor.

2. Run the dashboard script:
   ```bash
   python dashboard.py
   ```

The terminal will display the status of each website, updating every minute with a color-coded indicator for each check.

## License

This project is licensed under the MIT License.
