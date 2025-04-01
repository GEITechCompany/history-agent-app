import pandas as pd
import os
import re
import argparse
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init()

def search_csv_files(search_query, directory='.'):
    """
    Search through all CSV files in the directory for the search query.
    
    Args:
        search_query (str): The client name or information to search for
        directory (str): Directory to search in, defaults to current directory
    
    Returns:
        dict: Results organized by file and matches
    """
    results = {}
    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    
    # Case-insensitive search pattern
    pattern = re.compile(search_query, re.IGNORECASE)
    
    for csv_file in csv_files:
        file_path = os.path.join(directory, csv_file)
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Dictionary to store matches for this file
            file_matches = []
            
            # Iterate through each row and column
            for idx, row in df.iterrows():
                row_matches = {}
                match_found = False
                
                # Check each column for matches
                for column in df.columns:
                    cell_value = str(row[column])
                    if pattern.search(cell_value):
                        match_found = True
                        # Mark matched text
                        row_matches[column] = cell_value
                    else:
                        row_matches[column] = cell_value
                
                # If any match found in this row, add to results
                if match_found:
                    row_matches['_row_index'] = idx
                    file_matches.append(row_matches)
            
            # If any matches found in this file, add to results
            if file_matches:
                results[csv_file] = file_matches
                
        except Exception as e:
            print(f"Error processing {csv_file}: {str(e)}")
    
    return results

def display_results(results, search_query):
    """
    Display the search results in a user-friendly format.
    
    Args:
        results (dict): Results organized by file and matches
        search_query (str): The original search query
    """
    if not results:
        print(f"{Fore.YELLOW}No results found for '{search_query}'{Style.RESET_ALL}")
        return
    
    total_matches = sum(len(matches) for matches in results.values())
    print(f"{Fore.GREEN}Found {total_matches} matches for '{search_query}' across {len(results)} files:{Style.RESET_ALL}\n")
    
    for file_name, matches in results.items():
        print(f"{Fore.CYAN}=== {file_name} ({len(matches)} matches) ==={Style.RESET_ALL}")
        
        for match in matches:
            print(f"{Fore.YELLOW}Row {match.get('_row_index', 'N/A')}:{Style.RESET_ALL}")
            
            # Get all columns except the internal row index
            display_columns = {k: v for k, v in match.items() if k != '_row_index'}
            
            # Display each column value, highlighting the matched text
            for column, value in display_columns.items():
                pattern = re.compile(f"({search_query})", re.IGNORECASE)
                highlighted_value = pattern.sub(f"{Fore.RED}\\1{Style.RESET_ALL}", str(value))
                print(f"  {Fore.GREEN}{column}{Style.RESET_ALL}: {highlighted_value}")
            
            print("")  # Empty line between matches
        
        print("")  # Empty line between files

def main():
    parser = argparse.ArgumentParser(description="Search for client information across CSV files.")
    parser.add_argument("query", help="The search query (e.g., 'Anna Wong')")
    parser.add_argument("--dir", help="Directory to search in (default: current directory)", default=".")
    
    args = parser.parse_args()
    
    print(f"{Fore.CYAN}Searching for '{args.query}' in all CSV files...{Style.RESET_ALL}")
    results = search_csv_files(args.query, args.dir)
    display_results(results, args.query)

if __name__ == "__main__":
    main() 