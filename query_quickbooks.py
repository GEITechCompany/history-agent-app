#!/usr/bin/env python3
"""
QuickBooks Database Query Utility

This utility provides convenient access to analyze data in the QuickBooks SQLite database.
It includes pre-built queries for common financial analysis tasks.
"""

import os
import sys
import sqlite3
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class QuickBooksAnalyzer:
    """Analyzer for QuickBooks financial data"""
    
    def __init__(self, db_path='quickbooks.db'):
        """Initialize the analyzer with the path to the QuickBooks database"""
        self.db_path = db_path
        if not os.path.exists(db_path):
            print(f"{Fore.RED}Error: Database file '{db_path}' not found.{Style.RESET_ALL}")
            print(f"Run 'python harmonize_quickbooks.py' first to create the database.")
            sys.exit(1)
    
    def execute_query(self, query, params=None):
        """Execute an SQL query and return the results as a pandas DataFrame"""
        try:
            conn = sqlite3.connect(self.db_path)
            if params:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except sqlite3.Error as e:
            print(f"{Fore.RED}SQLite error: {e}{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}Error executing query: {e}{Style.RESET_ALL}")
            return None
    
    def revenue_by_year(self):
        """Get total revenue by year"""
        query = """
        SELECT Year, SUM(CAST(Total AS NUMERIC)) as TotalRevenue
        FROM quickbooks
        WHERE Total IS NOT NULL AND Total != ''
        GROUP BY Year
        ORDER BY Year
        """
        df = self.execute_query(query)
        if df is not None and not df.empty:
            print(f"\n{Fore.CYAN}Revenue by Year:{Style.RESET_ALL}")
            for _, row in df.iterrows():
                print(f"  {row['Year']}: ${row['TotalRevenue']:,.2f}")
            
            # Create a bar chart
            plt.figure(figsize=(10, 6))
            plt.bar(df['Year'], df['TotalRevenue'], color='skyblue')
            plt.title('Total Revenue by Year')
            plt.xlabel('Year')
            plt.ylabel('Revenue ($)')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add revenue labels on top of bars
            for i, v in enumerate(df['TotalRevenue']):
                plt.text(i, v + 0.1, f'${v:,.0f}', ha='center')
                
            plt.tight_layout()
            plt.savefig('revenue_by_year.png')
            print(f"{Fore.GREEN}Chart saved as 'revenue_by_year.png'{Style.RESET_ALL}")
        return df
    
    def top_services(self, limit=10):
        """Get top services by revenue"""
        # This query dynamically checks all service columns
        query = """
        WITH service_revenue AS (
            SELECT 'Exterior Window Cleaning' as Service,
                SUM(CASE WHEN "Exterior Window Cleaning" IS NOT NULL AND "Exterior Window Cleaning" != '' 
                    THEN CAST("Exterior Window Cleaning" AS NUMERIC) ELSE 0 END) as Revenue
            FROM quickbooks
            UNION ALL
            SELECT 'Interior Window Cleaning' as Service,
                SUM(CASE WHEN "Interior Window Cleaning" IS NOT NULL AND "Interior Window Cleaning" != '' 
                    THEN CAST("Interior Window Cleaning" AS NUMERIC) ELSE 0 END) as Revenue
            FROM quickbooks
            UNION ALL
            SELECT 'Eaves Cleaning' as Service,
                SUM(CASE WHEN "Eaves Cleaning" IS NOT NULL AND "Eaves Cleaning" != '' 
                    THEN CAST("Eaves Cleaning" AS NUMERIC) ELSE 0 END) as Revenue
            FROM quickbooks
            UNION ALL
            SELECT 'Track Cleaning' as Service,
                SUM(CASE WHEN "Track Cleaning" IS NOT NULL AND "Track Cleaning" != '' 
                    THEN CAST("Track Cleaning" AS NUMERIC) ELSE 0 END) as Revenue
            FROM quickbooks
            UNION ALL
            SELECT 'Screen Cleaning' as Service,
                SUM(CASE WHEN "Screen Cleaning" IS NOT NULL AND "Screen Cleaning" != '' 
                    THEN CAST("Screen Cleaning" AS NUMERIC) ELSE 0 END) as Revenue
            FROM quickbooks
            UNION ALL
            SELECT 'Eavestrough Cleaning' as Service,
                SUM(CASE WHEN "Eavestrough Cleaning" IS NOT NULL AND "Eavestrough Cleaning" != '' 
                    THEN CAST("Eavestrough Cleaning" AS NUMERIC) ELSE 0 END) as Revenue
            FROM quickbooks
            UNION ALL
            SELECT 'Power Washing' as Service,
                SUM(CASE WHEN "Power Washing" IS NOT NULL AND "Power Washing" != '' 
                    THEN CAST("Power Washing" AS NUMERIC) ELSE 0 END) as Revenue
            FROM quickbooks
        )
        SELECT Service, Revenue
        FROM service_revenue
        WHERE Revenue > 0
        ORDER BY Revenue DESC
        LIMIT ?
        """
        df = self.execute_query(query, (limit,))
        if df is not None and not df.empty:
            print(f"\n{Fore.CYAN}Top {limit} Services by Revenue:{Style.RESET_ALL}")
            for _, row in df.iterrows():
                print(f"  {row['Service']}: ${row['Revenue']:,.2f}")
            
            # Create a bar chart
            plt.figure(figsize=(12, 8))
            plt.barh(df['Service'], df['Revenue'], color='lightgreen')
            plt.title(f'Top {limit} Services by Revenue')
            plt.xlabel('Revenue ($)')
            plt.gca().invert_yaxis()  # Invert y-axis to show highest revenue at top
            plt.grid(axis='x', linestyle='--', alpha=0.7)
            
            # Add revenue labels
            for i, v in enumerate(df['Revenue']):
                plt.text(v + 0.1, i, f'${v:,.0f}', va='center')
                
            plt.tight_layout()
            plt.savefig('top_services.png')
            print(f"{Fore.GREEN}Chart saved as 'top_services.png'{Style.RESET_ALL}")
        return df
    
    def top_customers(self, year=None, limit=10):
        """Get top customers by revenue for a specific year or all years"""
        if year:
            query = """
            SELECT Customer, CAST(Total AS NUMERIC) as Revenue
            FROM quickbooks
            WHERE Total IS NOT NULL AND Total != '' AND Year = ?
            ORDER BY CAST(Total AS NUMERIC) DESC
            LIMIT ?
            """
            df = self.execute_query(query, (year, limit))
            title = f"Top {limit} Customers for {year}"
        else:
            query = """
            SELECT Customer, SUM(CAST(Total AS NUMERIC)) as Revenue
            FROM quickbooks
            WHERE Total IS NOT NULL AND Total != ''
            GROUP BY Customer
            ORDER BY Revenue DESC
            LIMIT ?
            """
            df = self.execute_query(query, (limit,))
            title = f"Top {limit} Customers (All Years)"
        
        if df is not None and not df.empty:
            print(f"\n{Fore.CYAN}{title}:{Style.RESET_ALL}")
            for _, row in df.iterrows():
                print(f"  {row['Customer']}: ${row['Revenue']:,.2f}")
            
            # Create a bar chart
            plt.figure(figsize=(12, 8))
            plt.barh(df['Customer'], df['Revenue'], color='salmon')
            plt.title(title)
            plt.xlabel('Revenue ($)')
            plt.gca().invert_yaxis()  # Invert y-axis to show highest revenue at top
            plt.grid(axis='x', linestyle='--', alpha=0.7)
            
            # Add revenue labels
            for i, v in enumerate(df['Revenue']):
                plt.text(v + 0.1, i, f'${v:,.0f}', va='center')
                
            plt.tight_layout()
            filename = f"top_customers{'_' + year if year else ''}.png"
            plt.savefig(filename)
            print(f"{Fore.GREEN}Chart saved as '{filename}'{Style.RESET_ALL}")
        return df
    
    def service_by_year(self, service):
        """Get revenue for a specific service by year"""
        # Use parameterized column names by constructing the query dynamically
        query = f"""
        SELECT Year, SUM(CAST("{service}" AS NUMERIC)) as Revenue
        FROM quickbooks
        WHERE "{service}" IS NOT NULL AND "{service}" != ''
        GROUP BY Year
        ORDER BY Year
        """
        df = self.execute_query(query)
        if df is not None and not df.empty:
            print(f"\n{Fore.CYAN}{service} Revenue by Year:{Style.RESET_ALL}")
            for _, row in df.iterrows():
                print(f"  {row['Year']}: ${row['Revenue']:,.2f}")
            
            # Create a bar chart
            plt.figure(figsize=(10, 6))
            plt.bar(df['Year'], df['Revenue'], color='lightblue')
            plt.title(f'{service} Revenue by Year')
            plt.xlabel('Year')
            plt.ylabel('Revenue ($)')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add revenue labels on top of bars
            for i, v in enumerate(df['Revenue']):
                plt.text(i, v + 0.1, f'${v:,.0f}', ha='center')
                
            plt.tight_layout()
            filename = f"{service.lower().replace(' ', '_')}_by_year.png"
            plt.savefig(filename)
            print(f"{Fore.GREEN}Chart saved as '{filename}'{Style.RESET_ALL}")
        return df
    
    def custom_query(self, query):
        """Execute a custom SQL query"""
        df = self.execute_query(query)
        if df is not None and not df.empty:
            print(f"\n{Fore.CYAN}Query Results:{Style.RESET_ALL}")
            print(df)
        return df

def main():
    """Main function to run the analyzer from command line"""
    parser = argparse.ArgumentParser(description='QuickBooks Database Query Utility')
    
    parser.add_argument('--revenue-by-year', action='store_true', 
                        help='Show total revenue by year')
    parser.add_argument('--top-services', type=int, nargs='?', const=10, metavar='LIMIT',
                        help='Show top services by revenue (default: top 10)')
    parser.add_argument('--top-customers', type=int, nargs='?', const=10, metavar='LIMIT',
                        help='Show top customers by revenue (default: top 10)')
    parser.add_argument('--year', type=str, help='Filter results by year (e.g., 2022)')
    parser.add_argument('--service', type=str, help='Show revenue for a specific service by year')
    parser.add_argument('--custom-query', type=str, help='Execute a custom SQL query')
    
    args = parser.parse_args()
    
    analyzer = QuickBooksAnalyzer()
    
    # Execute the requested analyses
    if args.revenue_by_year:
        analyzer.revenue_by_year()
    
    if args.top_services is not None:
        analyzer.top_services(args.top_services)
    
    if args.top_customers is not None:
        analyzer.top_customers(args.year, args.top_customers)
    
    if args.service:
        analyzer.service_by_year(args.service)
    
    if args.custom_query:
        analyzer.custom_query(args.custom_query)
    
    # If no specific analysis was requested, show help
    if not any([args.revenue_by_year, args.top_services is not None, 
                args.top_customers is not None, args.service, args.custom_query]):
        parser.print_help()
        print(f"\n{Fore.YELLOW}Example usage:{Style.RESET_ALL}")
        print("  python query_quickbooks.py --revenue-by-year")
        print("  python query_quickbooks.py --top-services 5")
        print("  python query_quickbooks.py --top-customers --year 2022")
        print("  python query_quickbooks.py --service \"Exterior Window Cleaning\"")
        print("  python query_quickbooks.py --custom-query \"SELECT * FROM quickbooks LIMIT 5\"")

if __name__ == '__main__':
    main() 