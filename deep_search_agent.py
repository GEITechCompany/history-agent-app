import pandas as pd
import os
import re
import argparse
import json
import csv
from datetime import datetime
from dateutil.parser import parse as date_parse
from colorama import Fore, Style, init
from fuzzywuzzy import fuzz, process
from tqdm import tqdm
import concurrent.futures
import math
import sys
import traceback

# Initialize colorama for colored terminal output
init()

class DeepSearchAgent:
    def __init__(self, debug=False):
        self.csv_files = self._get_csv_files()
        self.dataframes = {}
        self.debug = debug
        self.load_csv_files()
    
    def _get_csv_files(self):
        """Get all CSV files in the current directory"""
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
        
        # Check if GKeep_Structured.csv exists, if not try to create it
        if 'GKeep_Structured.csv' not in csv_files and 'GKeep (Simple).csv' in csv_files:
            try:
                self._ensure_gkeep_structured()
                # Add the newly created file to the list if it now exists
                if os.path.exists('GKeep_Structured.csv'):
                    csv_files.append('GKeep_Structured.csv')
            except Exception as e:
                print(f"Error creating structured GKeep data: {str(e)}")
        
        # Check if consolidated schedules exists, if not try to create it
        if 'consolidated_schedules.csv' not in csv_files and os.path.exists('exported_sheets_actual'):
            try:
                self._ensure_consolidated_schedules()
                # Add the newly created file to the list if it now exists
                if os.path.exists('consolidated_schedules.csv'):
                    csv_files.append('consolidated_schedules.csv')
            except Exception as e:
                print(f"Error creating consolidated schedules: {str(e)}")
        
        return csv_files
    
    def _ensure_gkeep_structured(self):
        """Ensure structured GKeep data exists by running the adapter if needed"""
        if not os.path.exists('GKeep_Structured.csv') and os.path.exists('gkeep_adapter.py'):
            print(f"{Fore.CYAN}Creating structured data from GKeep (Simple).csv...{Style.RESET_ALL}")
            try:
                # Import the gkeep_adapter module dynamically
                import importlib.util
                spec = importlib.util.spec_from_file_location("gkeep_adapter", "gkeep_adapter.py")
                gkeep_adapter = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(gkeep_adapter)
                
                # Run the extraction function
                gkeep_adapter.extract_gkeep_data()
                print(f"{Fore.GREEN}Successfully created GKeep_Structured.csv{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Failed to create structured GKeep data: {str(e)}{Style.RESET_ALL}")
                raise
    
    def _ensure_consolidated_schedules(self):
        """Ensure consolidated schedule data exists by running the processor if needed"""
        if not os.path.exists('consolidated_schedules.csv') and os.path.exists('daily_schedule_processor.py'):
            print(f"{Fore.CYAN}Creating consolidated schedule data from exported sheets...{Style.RESET_ALL}")
            try:
                # Import the daily_schedule_processor module dynamically
                import importlib.util
                spec = importlib.util.spec_from_file_location("daily_schedule_processor", "daily_schedule_processor.py")
                daily_schedule_processor = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(daily_schedule_processor)
                
                # Run the processing function
                daily_schedule_processor.process_daily_schedules()
                print(f"{Fore.GREEN}Successfully created consolidated_schedules.csv{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Failed to create consolidated schedules: {str(e)}{Style.RESET_ALL}")
                raise
    
    def load_csv_files(self):
        """Load all CSV files into pandas dataframes"""
        for file in self.csv_files:
            try:
                if self.debug:
                    print(f"Loading file: {file}")
                    file_size = os.path.getsize(file)
                    print(f"File size: {file_size} bytes")
                
                # Skip the original GKeep file since we're using the structured version
                if file == 'GKeep (Simple).csv' and 'GKeep_Structured.csv' in self.csv_files:
                    if self.debug:
                        print(f"Skipping {file} in favor of GKeep_Structured.csv")
                    continue
                
                # Load the CSV file
                df = pd.read_csv(file)
                
                if self.debug:
                    print(f"Successfully loaded {file}")
                    print(f"Shape: {df.shape}")
                    print(f"Columns: {df.columns.tolist()}")
                
                self.dataframes[file] = df
            except Exception as e:
                if self.debug:
                    print(f"Error loading {file}: {str(e)}")
                    traceback.print_exc()
    
    def exact_search(self, query, case_sensitive=False, columns=None):
        """
        Perform an exact search across all CSV files.
        
        Args:
            query (str): Search query
            case_sensitive (bool): Whether to be case sensitive
            columns (list): Specific columns to search in
            
        Returns:
            list: List of matching records
        """
        results = []
        
        for file_name, df in self.dataframes.items():
            if self.debug:
                print(f"Searching in {file_name} with {len(df)} rows")
            
            # Get columns to search in
            search_columns = columns if columns else df.columns
            search_columns = [col for col in search_columns if col in df.columns]
            
            if not search_columns:
                if self.debug:
                    print(f"No valid columns to search in {file_name}")
                continue
            
            if self.debug:
                print(f"Searching in columns: {search_columns}")
            
            # Prepare query for comparison
            query_for_comparison = query if case_sensitive else query.lower()
            
            # Perform exact search on each row
            for idx, row in df.iterrows():
                match_found = False
                matching_value = ""
                
                for col in search_columns:
                    if pd.isna(row[col]):
                        continue
                    
                    cell_value = row[col]
                    if not isinstance(cell_value, str):
                        cell_value = str(cell_value)
                    
                    cell_for_comparison = cell_value if case_sensitive else cell_value.lower()
                    
                    if query_for_comparison in cell_for_comparison:
                        match_found = True
                        matching_value = cell_value
                        break
                
                if match_found:
                    if self.debug:
                        print(f"Match found in {file_name}, row {idx}, value: {matching_value}")
                    
                    # Create a record with all information from the row
                    record = {col: row[col] for col in df.columns}
                    record['file'] = file_name
                    record['matching_value'] = matching_value
                    results.append(record)
        
        return results
    
    def fuzzy_search(self, query, threshold=70, columns=None):
        """
        Perform a fuzzy search across all CSV files.
        
        Args:
            query (str): Search query
            threshold (int): Minimum score for fuzzy matching (0-100)
            columns (list): Specific columns to search in
            
        Returns:
            list: List of matching records
        """
        results = []
        
        for file_name, df in self.dataframes.items():
            if self.debug:
                print(f"Searching in {file_name} with {len(df)} rows")
            
            # Get columns to search in
            search_columns = columns if columns else df.columns
            search_columns = [col for col in search_columns if col in df.columns]
            
            if not search_columns:
                if self.debug:
                    print(f"No valid columns to search in {file_name}")
                continue
            
            if self.debug:
                print(f"Searching in columns: {search_columns}")
            
            # Perform fuzzy search on each row
            for idx, row in df.iterrows():
                match_found = False
                highest_score = 0
                matching_value = ""
                
                for col in search_columns:
                    if pd.isna(row[col]) or not isinstance(row[col], str):
                        continue
                    
                    score = fuzz.ratio(query.lower(), str(row[col]).lower())
                    
                    if score > threshold and score > highest_score:
                        highest_score = score
                        match_found = True
                        matching_value = row[col]
                
                if match_found:
                    if self.debug:
                        print(f"Match found in {file_name}, row {idx}, score: {highest_score}, value: {matching_value}")
                    
                    # Create a record with all information from the row
                    record = {col: row[col] for col in df.columns}
                    record['file'] = file_name
                    record['match_score'] = highest_score
                    record['matching_value'] = matching_value
                    results.append(record)
        
        return results
    
    def date_range_search(self, start_date=None, end_date=None, date_columns=None):
        """
        Search for entries within a date range.
        
        Args:
            start_date (str): Start date in format YYYY-MM-DD
            end_date (str): End date in format YYYY-MM-DD
            date_columns (list): List of column names that may contain dates
            
        Returns:
            dict: Results organized by file and matches
        """
        results = {}
        
        # Convert string dates to datetime objects
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                print(f"{Fore.RED}Invalid start date format. Use YYYY-MM-DD.{Style.RESET_ALL}")
                return {}
        else:
            start_dt = datetime.min
            
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                print(f"{Fore.RED}Invalid end date format. Use YYYY-MM-DD.{Style.RESET_ALL}")
                return {}
        else:
            end_dt = datetime.max
        
        for csv_file, df in self.dataframes.items():
            file_matches = []
            
            # Determine date columns if not specified
            if not date_columns:
                potential_date_cols = []
                for column in df.columns:
                    # Check first few non-null values to see if they might be dates
                    for val in df[column].dropna().head(5):
                        if isinstance(val, str) and self._is_date(val):
                            potential_date_cols.append(column)
                            break
            else:
                potential_date_cols = [col for col in date_columns if col in df.columns]
            
            # Skip file if no date columns found
            if not potential_date_cols:
                if self.debug:
                    print(f"{Fore.YELLOW}No date columns found in {csv_file}{Style.RESET_ALL}")
                continue
            elif self.debug:
                print(f"{Fore.CYAN}Searching date columns in {csv_file}: {', '.join(potential_date_cols)}{Style.RESET_ALL}")
                
            # Iterate through each row
            for idx, row in df.iterrows():
                date_found = False
                row_matches = {}
                
                # Check each potential date column
                for column in potential_date_cols:
                    cell_value = str(row[column])
                    
                    # Skip empty values and NaN
                    if cell_value.lower() == 'nan' or cell_value == '':
                        continue
                    
                    # Try to parse the date
                    try:
                        date_value = self._parse_date(cell_value)
                        
                        # Check if date is within range
                        if start_dt <= date_value <= end_dt:
                            date_found = True
                            if self.debug:
                                print(f"{Fore.GREEN}Date match found in {csv_file}, row {idx}, column {column}: {cell_value}{Style.RESET_ALL}")
                    except:
                        if self.debug:
                            print(f"{Fore.YELLOW}Could not parse date in {csv_file}, row {idx}, column {column}: {cell_value}{Style.RESET_ALL}")
                        continue
                
                # If date in range found, add all columns to results
                if date_found:
                    for column in df.columns:
                        row_matches[column] = str(row[column])
                    
                    row_matches['_row_index'] = idx
                    file_matches.append(row_matches)
            
            # If any matches found in this file, add to results
            if file_matches:
                results[csv_file] = file_matches
                if self.debug:
                    print(f"{Fore.GREEN}Found {len(file_matches)} date matches in {csv_file}{Style.RESET_ALL}")
            elif self.debug:
                print(f"{Fore.YELLOW}No date matches found in {csv_file}{Style.RESET_ALL}")
        
        return results
    
    def combined_search(self, query=None, fuzzy=False, min_score=70, 
                      start_date=None, end_date=None, date_columns=None,
                      filters=None, case_sensitive=False):
        """
        Perform a combined search with various criteria.
        
        Args:
            query (str): Search query
            fuzzy (bool): Whether to use fuzzy matching
            min_score (int): Minimum score for fuzzy matching
            start_date (str): Start date for date filtering
            end_date (str): End date for date filtering
            date_columns (list): Column names containing dates
            filters (dict): Additional column:value filters
            case_sensitive (bool): Whether to be case sensitive
            
        Returns:
            list: List of matching records
        """
        results = []
        
        # If we have a query, perform search
        if query:
            if fuzzy:
                results = self.fuzzy_search(query, threshold=min_score)
            else:
                results = self.exact_search(query, case_sensitive=case_sensitive)
        
        # Apply date filtering if dates are provided
        if (start_date or end_date) and results:
            results = self.filter_by_date_range(results, start_date, end_date)
        
        # Apply additional filters if provided
        if filters and results:
            filtered_results = []
            
            for record in results:
                match_all = True
                
                for column, filter_value in filters.items():
                    if column in record:
                        record_value = str(record[column]).lower()
                        filter_value = str(filter_value).lower()
                        
                        if filter_value not in record_value:
                            match_all = False
                            break
                    else:
                        match_all = False
                        break
                
                if match_all:
                    filtered_results.append(record)
            
            results = filtered_results
        
        return results
    
    def export_results(self, results, output_file):
        """
        Export results to a file.
        
        Args:
            results (list): List of records to export
            output_file (str): Output file path
            
        Returns:
            None
        """
        if not results:
            print(f"{Fore.YELLOW}No results to export.{Style.RESET_ALL}")
            return
        
        # Determine the file format from the extension
        file_format = os.path.splitext(output_file)[1].lower()
        
        if file_format == '.json':
            # Export to JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
        else:
            # Default to CSV
            df = pd.DataFrame(results)
            df.to_csv(output_file, index=False)
        
        print(f"{Fore.GREEN}Exported {len(results)} results to {output_file}{Style.RESET_ALL}")
    
    def display_results(self, results, query=None, max_columns=None, show_scores=False):
        """
        Display search results in a formatted way.
        
        Args:
            results (list): List of records to display
            query (str): Original search query
            max_columns (int): Maximum number of columns to display
            show_scores (bool): Whether to show match scores for fuzzy matches
            
        Returns:
            None
        """
        if not results:
            print(f"{Fore.YELLOW}No results found{' for query: ' + query if query else ''}.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}Found {len(results)} results{' for query: ' + query if query else ''}{Style.RESET_ALL}")
        
        for i, result in enumerate(results, 1):
            print(f"\n{Fore.CYAN}Result {i}/{len(results)}:{Style.RESET_ALL}")
            
            # Extract file name and match information
            file_name = result.get('file', 'Unknown file')
            match_score = result.get('match_score', None)
            matching_value = result.get('matching_value', None)
            
            print(f"{Fore.YELLOW}Source: {file_name}{Style.RESET_ALL}")
            
            if match_score and show_scores:
                print(f"{Fore.YELLOW}Match score: {match_score}%{Style.RESET_ALL}")
                
            if matching_value:
                print(f"{Fore.YELLOW}Matching value: {matching_value}{Style.RESET_ALL}")
            
            # Determine which columns to display
            columns_to_display = list(result.keys())
            
            # Remove metadata fields
            for field in ['file', 'match_score', 'matching_value']:
                if field in columns_to_display:
                    columns_to_display.remove(field)
            
            # Limit number of columns if requested
            if max_columns and len(columns_to_display) > max_columns:
                columns_to_display = columns_to_display[:max_columns]
                print(f"{Fore.YELLOW}(Showing {max_columns} of {len(result)} fields){Style.RESET_ALL}")
            
            # Display each column
            for col in columns_to_display:
                value = result[col]
                if pd.notna(value):  # Skip NaN values
                    print(f"{Fore.GREEN}{col}{Style.RESET_ALL}: {value}")
    
    def _is_date(self, value):
        """Check if a string might be a date"""
        try:
            self._parse_date(value)
            return True
        except:
            return False
            
    def _parse_date(self, value):
        """Parse a string into a datetime object"""
        try:
            # Try standard datetime parsing
            return date_parse(value)
        except:
            # Try various common formats
            formats = [
                '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d',
                '%m/%d/%y', '%d/%m/%y', '%Y/%m/%d',
                '%m-%d-%Y', '%d-%m-%Y', '%Y.%m.%d',
                '%m.%d.%Y', '%d.%m.%Y', '%b %d, %Y',
                '%B %d, %Y', '%d %b %Y', '%d %B %Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except:
                    continue
                    
            raise ValueError(f"Could not parse date: {value}")
    
    def _values_match(self, value1, value2):
        """Check if two values match, handling different types and formats"""
        if value1 is None or value2 is None:
            return False
            
        # Convert to strings for comparison
        str1 = str(value1).lower().strip()
        str2 = str(value2).lower().strip()
        
        # Check for exact match
        if str1 == str2:
            return True
            
        # Check for contained match (value2 is contained in value1)
        if str2 in str1:
            return True
            
        # Check if both are dates that match
        try:
            date1 = self._parse_date(str1)
            date2 = self._parse_date(str2)
            return date1.date() == date2.date()
        except:
            pass
            
        return False
        
    def filter_by_date_range(self, results, start_date, end_date):
        """
        Filter results by date range.
        
        Args:
            results (list): List of records to filter
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            list: Filtered list of records
        """
        if not results or not (start_date or end_date):
            return results
        
        filtered_results = []
        
        # Convert start_date and end_date to datetime objects
        start = pd.to_datetime(start_date) if start_date else None
        end = pd.to_datetime(end_date) if end_date else None
        
        for record in results:
            # Check all date-like columns in the record
            date_found = False
            
            for field, value in record.items():
                if pd.isna(value):
                    continue
                    
                # Skip non-date fields and check if the value is date-like
                try:
                    date_value = pd.to_datetime(value)
                    
                    # Filter by date range
                    if (start is None or date_value >= start) and (end is None or date_value <= end):
                        date_found = True
                        break
                except:
                    # Not a valid date format, skip
                    continue
            
            # Add record if a date within the range was found or if no date columns were found
            if date_found:
                filtered_results.append(record)
        
        return filtered_results

    def analyze_file(self, file_name):
        """
        Analyze the structure of a CSV file.
        
        Args:
            file_name (str): Name of the file to analyze
            
        Returns:
            None
        """
        if file_name not in self.dataframes:
            print(f"{Fore.RED}File not found or could not be loaded: {file_name}{Style.RESET_ALL}")
            
            # Try to load the file directly
            try:
                df = pd.read_csv(file_name)
                print(f"{Fore.GREEN}Successfully loaded {file_name}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error loading file: {str(e)}{Style.RESET_ALL}")
                return
        else:
            df = self.dataframes[file_name]
        
        print(f"{Fore.CYAN}File analysis for {file_name}:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Shape: {df.shape}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Columns: {df.columns.tolist()}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}First few rows:{Style.RESET_ALL}")
        print(df.head())
        
        # For GKeep file, show more context if it has only one column
        if file_name == 'GKeep (Simple).csv' and df.shape[1] == 1:
            print(f"{Fore.CYAN}\nSample of raw text content:{Style.RESET_ALL}")
            with open(file_name, 'r', encoding='utf-8') as f:
                print(f.read(1000) + "...")

def main():
    parser = argparse.ArgumentParser(description='Deep Search Agent for client information')
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('--fuzzy', action='store_true', help='Use fuzzy matching')
    parser.add_argument('--date-range', nargs=2, metavar=('START_DATE', 'END_DATE'), 
                       help='Filter results by date range (YYYY-MM-DD format)')
    parser.add_argument('--columns', nargs='+', help='Specific columns to search in')
    parser.add_argument('--export', help='Export results to a file (csv or json)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--analyze-file', help='Analyze the structure of a specific CSV file')
    
    args = parser.parse_args()
    
    # Initialize colorama
    init()
    
    agent = DeepSearchAgent(debug=args.debug)
    
    if args.analyze_file:
        agent.analyze_file(args.analyze_file)
    elif args.query:
        results = []
        
        if args.fuzzy:
            print(f"{Fore.CYAN}Performing fuzzy search for: {args.query}{Style.RESET_ALL}")
            results = agent.fuzzy_search(args.query, columns=args.columns)
        else:
            print(f"{Fore.CYAN}Performing exact search for: {args.query}{Style.RESET_ALL}")
            results = agent.exact_search(args.query, columns=args.columns)
        
        if args.date_range:
            results = agent.filter_by_date_range(results, args.date_range[0], args.date_range[1])
        
        if not results:
            print(f"{Fore.YELLOW}No results found for: {args.query}{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}Found {len(results)} results for: {args.query}{Style.RESET_ALL}")
            for i, result in enumerate(results, 1):
                print(f"\n{Fore.CYAN}Result {i}/{len(results)}:{Style.RESET_ALL}")
                for k, v in result.items():
                    if pd.notna(v):  # Only print non-NaN values
                        print(f"{Fore.GREEN}{k}{Style.RESET_ALL}: {v}")
        
            if args.export:
                agent.export_results(results, args.export)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 