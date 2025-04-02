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

## QuickBooks Data Integration

The application now includes robust support for QuickBooks CSV exports. This feature allows you to analyze and search through financial data from multiple years in a consolidated way.

### Importing QuickBooks Data

Simply place your QuickBooks CSV exports in the workspace directory with the naming format `YYYY QB.csv` (e.g., `2022 QB.csv`, `2023 QB.csv`).

### Processing QuickBooks Data

Use the QuickBooks processor to generate consolidated data:

```bash
python harmonize_quickbooks.py --summary
```

This will:
1. Process all QuickBooks CSV files (supports multiple years)
2. Combine them into a unified dataset with year tracking
3. Create a SQLite database for more complex SQL queries
4. Generate a summary report of your financial data

### Searching QuickBooks Data

Search for specific customer information or financial details:

```bash
python harmonize_quickbooks.py --update-search --query "Window Cleaning" --year 2023
```

Or search by customer name:

```bash
python harmonize_quickbooks.py --update-search --query "Smith" --customer
```

The QuickBooks data is also automatically incorporated into the Deep Search Agent, allowing you to search across all your business data at once.

### Running SQL Queries on Financial Data

The integration creates a SQLite database (quickbooks.db) that you can use for more complex financial analysis:

```bash
sqlite3 quickbooks.db "SELECT Customer, Year, \"Exterior Window Cleaning\" as Revenue FROM quickbooks WHERE Year = '2022' ORDER BY CAST(\"Exterior Window Cleaning\" AS NUMERIC) DESC LIMIT 10;"
```

This is particularly useful for:
- Revenue analysis by service category
- Year-over-year growth reporting
- Customer spending analysis
- Identifying top customers by service category
- Seasonal trend analysis

### Financial Analysis Utility

For advanced financial analysis, use the included `query_quickbooks.py` utility:

```bash
# Show revenue by year with chart generation
python query_quickbooks.py --revenue-by-year

# View top services by revenue
python query_quickbooks.py --top-services 7

# Find top customers for a specific year
python query_quickbooks.py --top-customers 8 --year 2022

# Analyze a specific service performance over time
python query_quickbooks.py --service "Exterior Window Cleaning"

# Run a custom SQL query
python query_quickbooks.py --custom-query "SELECT Customer, Total FROM quickbooks ORDER BY CAST(Total AS NUMERIC) DESC LIMIT 5"
```

The utility generates both textual output and visual charts for easier interpretation of the financial data.

### Financial Insights

The summary report provides key insights into your business data:
- Total revenue by year
- Top service categories by revenue
- Top customers by spending
- Revenue breakdown by service category

These insights can help with business decision-making, identifying growth opportunities, and focusing on profitable service categories.

## QuickBooks Data Integration Utility

This utility allows you to integrate QuickBooks data with the History Agent system for seamless financial analysis.

### Features

* **Data Harmonization**: Process QuickBooks CSV files (named like "2022 QB.csv") and convert them into a standardized format
* **Consolidated Database**: Store all financial data in a SQLite database for easy querying
* **Financial Analysis**: Run pre-built financial analyses to gain insights from your QuickBooks data
* **Visual Reports**: Generate charts for revenue trends, top services, and top customers
* **Deep Search Integration**: Search across financial data alongside other system data

### How to Use

1. **Process QuickBooks Files**:
   ```
   python3 harmonize_quickbooks.py --summary
   ```
   This will process all QuickBooks CSV files (named like "YYYY QB.csv") and generate a consolidated database and summary report.

2. **Analyze Financial Data**:
   ```
   python3 query_quickbooks.py --revenue-by-year
   python3 query_quickbooks.py --top-services 5
   python3 query_quickbooks.py --top-customers --year 2022
   python3 query_quickbooks.py --service "Exterior Window Cleaning"
   ```

3. **List Available Services**:
   ```
   python3 query_quickbooks.py --list-services
   ```

4. **Run Custom SQL Queries**:
   ```
   python3 query_quickbooks.py --custom-query "SELECT * FROM quickbooks LIMIT 5"
   ```

### Options

* `--summary`: Generate a summary report of the processed data
* `--no-clean`: Skip data processing and use existing processed files
* `--update-search`: Update the deep search agent with QuickBooks data
* `--query`: Run a search query against the data
* `--year`: Filter results by year
* `--verbose`: Show detailed logs during processing

## Recent Optimizations and Improvements

The system has recently undergone several optimizations and bug fixes:

### Performance Improvements
- Added caching for frequently accessed data
- Optimized SQLite queries for faster financial analysis
- Improved data loading with proper type conversion
- Added progress tracking for long-running operations

### Bug Fixes
- Fixed handling of 'nan' values in financial data
- Resolved matplotlib warnings by properly handling string data types
- Added robust error handling throughout the system
- Fixed PyArrow integration for better pandas performance

### New Features
- Added the `--no-clean` option to skip reprocessing when data hasn't changed
- Added `--list-services` command to show all available service categories
- Added logging for better debugging and troubleshooting
- Added execution time reporting for performance monitoring

### Requirements
- Added PyArrow support for improved pandas performance
- Updated matplotlib to fix visualization issues
- Added proper type handling for financial data

To use the latest improvements, make sure to update your dependencies:
```
pip install -r requirements.txt
```

## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue if you have suggestions for improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
