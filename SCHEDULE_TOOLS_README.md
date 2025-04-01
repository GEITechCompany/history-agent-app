# Daily Schedule Data Organization Tools

This directory contains several tools for organizing, analyzing, and visualizing the daily schedule data from the exported sheets. These tools provide different ways to work with the 663 jobs collected from 290 schedule files.

## Available Tools

1. **Excel Workbook Organizer** (`schedule_organizer.py`)
   - Creates a structured Excel workbook with multiple sheets
   - Organizes data by date, client, and includes summary statistics
   - Provides a comprehensive overview suitable for reporting

2. **SQLite Database** (`schedule_database.py`) 
   - Creates a searchable database of all schedule data
   - Enables complex SQL queries for advanced analysis
   - Includes indexing for improved search performance

3. **Web Interface** (`schedule_web_interface.py`)
   - Provides a browser-based interface to search and explore the data
   - Includes visualizations of jobs by date and client
   - Allows exporting filtered data to CSV or Excel

## Prerequisites

These tools require several Python packages. Install them using:

```bash
pip3 install pandas openpyxl flask matplotlib seaborn
```

## How to Use

### Step 1: Ensure Consolidated Data Exists

Make sure the consolidated schedule data has been created:

```bash
python3 daily_schedule_processor.py
```

This will process all daily schedule files and create `consolidated_schedules.csv`.

### Step 2: Choose Your Preferred Organization Method

#### For Excel Workbook:

```bash
python3 schedule_organizer.py
```

This creates `organized_schedules.xlsx` with the following sheets:
- All Jobs: Complete listing of all jobs
- Jobs by Date: Chronological listing of jobs
- Jobs by Client: Jobs grouped by client
- Summary Statistics: Key metrics and insights

#### For SQLite Database:

```bash
python3 schedule_database.py
```

This creates `schedules.db` that you can query using any SQLite client. Example queries are provided in the script output.

#### For Web Interface:

```bash
python3 schedule_web_interface.py
```

Then open a web browser and navigate to http://127.0.0.1:5000

The web interface allows you to:
- Search for specific terms across all data
- Filter by date ranges
- View visualizations of job distributions
- Export filtered results

## Usage Examples

### Example 1: Find all jobs for a specific client

Using the web interface:
1. Enter the client name in the search box
2. Select the appropriate client column
3. Click "Search"

Using SQL queries:
```sql
SELECT * FROM jobs WHERE client LIKE '%ClientName%'
```

### Example 2: Find jobs between specific dates

Using the web interface:
1. Select the date column from the dropdown
2. Enter the start and end dates
3. Click "Search"

Using SQL queries:
```sql
SELECT * FROM jobs WHERE job_date BETWEEN '2023-01-01' AND '2023-12-31'
```

### Example 3: Analyze busiest days

The Excel workbook includes a "Summary Statistics" sheet with the top 10 busiest days.

Using SQL queries:
```sql
SELECT job_date, COUNT(*) as job_count 
FROM jobs 
GROUP BY job_date 
ORDER BY job_count DESC 
LIMIT 10
```

## Modifying the Tools

These tools are designed to be easily modified:

- To add new visualizations: Edit `schedule_web_interface.py` and add new chart types
- To change database structure: Modify the column detection in `schedule_database.py`
- To add new Excel reports: Edit the sheet creation in `schedule_organizer.py`

## Troubleshooting

If you encounter issues:

1. **Missing data**: Ensure the `consolidated_schedules.csv` file exists
2. **Import errors**: Check that all required packages are installed
3. **Visualization issues**: Ensure your data has proper date and client columns

## Further Assistance

For more help or to request additional features, please contact the development team. 