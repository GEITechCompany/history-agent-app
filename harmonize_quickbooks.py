#!/usr/bin/env python3
import os
import sys
import argparse
import time
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init()

def main():
    """
    Harmonize QuickBooks CSV files with the workspace.
    This script processes QuickBooks data files and integrates them with the system.
    """
    start_time = time.time()
    
    parser = argparse.ArgumentParser(description='Harmonize QuickBooks CSV files with the workspace')
    parser.add_argument('--summary', action='store_true', help='Generate a summary report of the QuickBooks data')
    parser.add_argument('--update-search', action='store_true', help='Update the deep search agent with QuickBooks data')
    parser.add_argument('--query', type=str, help='Search query to run against the combined data')
    parser.add_argument('--year', type=str, help='Filter by year (e.g., 2022, 2023, etc.)')
    parser.add_argument('--customer', type=str, help='Filter by customer name')
    parser.add_argument('--no-clean', action='store_true', help='Skip data cleaning (use existing processed files)')
    args = parser.parse_args()
    
    print(f"{Fore.CYAN}Starting QuickBooks data harmonization process...{Style.RESET_ALL}")
    
    # Check for QuickBooks files
    qb_files = [f for f in os.listdir('.') if f.endswith('QB.csv')]
    if not qb_files:
        print(f"{Fore.RED}No QuickBooks files found in the workspace. Exiting.{Style.RESET_ALL}")
        return
    
    print(f"{Fore.GREEN}Found {len(qb_files)} QuickBooks files: {qb_files}{Style.RESET_ALL}")
    
    # Step 1: Process QuickBooks files and generate consolidated data (unless --no-clean is specified)
    if args.no_clean and os.path.exists('consolidated_quickbooks.csv') and os.path.exists('quickbooks.db'):
        print(f"{Fore.YELLOW}Using existing processed QuickBooks data (--no-clean specified){Style.RESET_ALL}")
        success = True
    else:
        try:
            import quickbooks_processor
            processor = quickbooks_processor.QuickBooksProcessor()
            success = processor.process_all_files()
            
            if not success:
                print(f"{Fore.RED}Failed to process QuickBooks files. Exiting.{Style.RESET_ALL}")
                return
                
            # Generate summary if requested
            if args.summary:
                processor.generate_summary_report()
        
        except ImportError:
            print(f"{Fore.RED}Error: quickbooks_processor.py not found or has errors. Please ensure it exists in the workspace.{Style.RESET_ALL}")
            return
        except Exception as e:
            print(f"{Fore.RED}Error processing QuickBooks data: {str(e)}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
            return
    
    # Step 2: Update the deep search agent if requested
    if args.update_search:
        try:
            import deep_search_agent
            print(f"{Fore.CYAN}Updating deep search agent with QuickBooks data...{Style.RESET_ALL}")
            
            # Create a search agent instance and load the files
            agent = deep_search_agent.DeepSearchAgent(debug=True)
            
            print(f"{Fore.GREEN}Successfully updated deep search agent with QuickBooks data{Style.RESET_ALL}")
            
            # Run a search if query provided
            if args.query:
                print(f"{Fore.CYAN}Running search query: '{args.query}'...{Style.RESET_ALL}")
                
                # Prepare filters if any
                filters = {}
                if args.year:
                    filters['Year'] = args.year
                if args.customer:
                    filters['Customer'] = args.customer
                
                # Run combined search
                results = agent.combined_search(
                    query=args.query,
                    fuzzy=True,
                    min_score=70,
                    filters=filters
                )
                
                # Display results
                agent.display_results(results, query=args.query, show_scores=True)
                
                # Save results to a CSV file
                output_file = f"search_results_{args.query.replace(' ', '_')}.csv"
                agent.export_results(results, output_file)
                print(f"{Fore.GREEN}Search results saved to {output_file}{Style.RESET_ALL}")
        
        except ImportError:
            print(f"{Fore.RED}Error: deep_search_agent.py not found or has errors. Please ensure it exists in the workspace.{Style.RESET_ALL}")
            return
        except Exception as e:
            print(f"{Fore.RED}Error updating search agent: {str(e)}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
            return
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"{Fore.GREEN}QuickBooks data harmonization complete! (Execution time: {execution_time:.2f} seconds){Style.RESET_ALL}")
    print("\nUse this data in the system with:")
    print("  - Deep search agent for searching across all data sources")
    print("  - SQLite database for direct SQL queries (quickbooks.db)")
    print("  - Consolidated CSV for spreadsheet analysis (consolidated_quickbooks.csv)")
    print("\nTry the query_quickbooks.py utility for pre-built financial analyses")
    print("Example: python3 query_quickbooks.py --revenue-by-year")

if __name__ == "__main__":
    main() 