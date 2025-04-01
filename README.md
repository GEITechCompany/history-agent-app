# Deep Search Agent for Client Information (History Agent App)

A powerful search tool for extracting client information across multiple CSV files. This agent is designed to search through your entire client database and provide comprehensive results.

## Features

- **Multi-file search** - Search across all CSV files in a directory
- **Fuzzy matching** - Find results even with typos or slight name variations
- **Date range filtering** - Find records within a specific date range
- **Column filtering** - Filter results by specific column values
- **Export functionality** - Export search results to CSV or JSON
- **Web interface** - User-friendly web interface for easy searching
- **Command-line interface** - For batch processing and automation

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

For basic searches:

```bash
python deep_search_agent.py "Anna Wong"
```

With fuzzy matching:

```bash
python deep_search_agent.py "Ana Wong" --fuzzy
```

Filtering by date range:

```bash
python deep_search_agent.py "Wong" --start-date 2023-01-01 --end-date 2023-12-31
```

Export results:

```bash
python deep_search_agent.py "Anna Wong" --export results.csv
```

### Advanced Usage

Combine multiple search criteria:

```bash
python deep_search_agent.py "Wong" --fuzzy --threshold 80 --filter "Status:Active" "City:Mississauga" --export results.json --format json
```

For a full list of options:

```bash
python deep_search_agent.py --help
```

### Web Interface

Start the web interface:

```bash
python web_search_interface.py
```

Then open your browser to http://localhost:5000 to access the search interface.

## Advanced Configuration

### Fuzzy Matching Threshold

Adjust the fuzzy matching threshold (0-100) to control how strict or lenient the matching should be:

```bash
python deep_search_agent.py "Ana Wong" --fuzzy --threshold 85
```

Higher values require closer matches, while lower values allow more variation.

### Custom Date Columns

Specify which columns contain date values:

```bash
python deep_search_agent.py --start-date 2023-01-01 --date-columns "BOOKING DATE" "INTAKE DATE"
```

## Examples

1. Find all clients named "Wong" with fuzzy matching and export to CSV:

```bash
python deep_search_agent.py "Wong" --fuzzy --export wong_clients.csv
```

2. Find all bookings in November 2023:

```bash
python deep_search_agent.py --start-date 2023-11-01 --end-date 2023-11-30 --date-columns "BOOKING DATE"
```

3. Find all active clients in Mississauga:

```bash
python deep_search_agent.py --filter "Status:Active" "City:Mississauga"
```

## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue if you have suggestions for improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
