#!/usr/bin/env python3
import os
import pandas as pd
import re
import glob
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init()

class QuickBooksProcessor:
    """
    Processor for QuickBooks CSV files.
    This class helps standardize and integrate QuickBooks financial data with the system.
    """
    
    def __init__(self):
        self.qb_files = self._get_qb_files()
        self.combined_data = None
        
    def _get_qb_files(self):
        """Get all QuickBooks CSV files in the current directory"""
        qb_files = [f for f in os.listdir('.') if re.match(r'^\d{4}\s+QB\.csv$', f)]
        print(f"{Fore.GREEN}Found {len(qb_files)} QuickBooks files: {qb_files}{Style.RESET_ALL}")
        return qb_files
    
    def process_qb_file(self, file_path):
        """Process a single QuickBooks file and extract structured data"""
        try:
            # Extract year from filename
            year_match = re.match(r'^(\d{4})\s+QB\.csv$', os.path.basename(file_path))
            year = year_match.group(1) if year_match else "Unknown"
            
            print(f"Processing QuickBooks data for year: {year}")
            
            # Read the CSV file
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Add a Year column to identify the source year
            df['Year'] = year
            
            # Clean up dollar amounts if necessary
            for column in df.columns:
                if column not in ['Customer', 'Year']:
                    try:
                        # Remove commas and dollar signs if present
                        df[column] = df[column].astype(str).str.replace(',', '').str.replace('$', '')
                        # Convert to float where possible
                        df[column] = pd.to_numeric(df[column], errors='ignore')
                    except:
                        pass
            
            return df
        
        except Exception as e:
            print(f"{Fore.RED}Error processing {file_path}: {str(e)}{Style.RESET_ALL}")
            return None
    
    def process_all_files(self):
        """Process all QuickBooks files and combine them into a unified dataset"""
        all_data = []
        
        for file_path in self.qb_files:
            try:
                df = self.process_qb_file(file_path)
                if df is not None:
                    all_data.append(df)
                    print(f"Processed {file_path}: {len(df)} records found")
            except Exception as e:
                print(f"{Fore.RED}Error with file {file_path}: {str(e)}{Style.RESET_ALL}")
        
        # Combine all dataframes
        if all_data:
            self.combined_data = pd.concat(all_data, ignore_index=True)
            print(f"{Fore.GREEN}Successfully processed {len(self.combined_data)} records from {len(self.qb_files)} files{Style.RESET_ALL}")
            
            # Save to a consolidated CSV file
            output_file = 'consolidated_quickbooks.csv'
            self.combined_data.to_csv(output_file, index=False)
            print(f"{Fore.GREEN}Saved consolidated QuickBooks data to {output_file}{Style.RESET_ALL}")
            
            # Save a SQLite version for easier querying
            self._create_sqlite_database()
            
            return True
        else:
            print(f"{Fore.YELLOW}No data found in QuickBooks files{Style.RESET_ALL}")
            return False
    
    def _create_sqlite_database(self):
        """Create a SQLite database from the consolidated QuickBooks data"""
        if self.combined_data is None:
            print("No data available to create database.")
            return False
        
        # Create SQLite database
        db_file = 'quickbooks.db'
        print(f"Creating SQLite database: {db_file}...")
        
        # Make sure the database is removed if it exists
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"Removed existing database: {db_file}")
        
        import sqlite3
        conn = sqlite3.connect(db_file)
        
        # Write the data to the database
        self.combined_data.to_sql('quickbooks', conn, index=False)
        
        # Create an index on Customer and Year for faster lookups
        conn.execute('CREATE INDEX idx_customer_year ON quickbooks (Customer, Year)')
        
        conn.close()
        print(f"{Fore.GREEN}Created SQLite database: {db_file}{Style.RESET_ALL}")
        return True

    def generate_summary_report(self):
        """Generate a summary report of the QuickBooks data"""
        if self.combined_data is None:
            print("No data available for summary report.")
            return
        
        print("\n=== QuickBooks Data Summary ===")
        
        # Years covered
        years = sorted(self.combined_data['Year'].unique())
        print(f"Years covered: {', '.join(years)}")
        
        # Total customers
        total_customers = len(self.combined_data['Customer'].unique())
        print(f"Total unique customers: {total_customers}")
        
        # Service categories
        service_columns = [col for col in self.combined_data.columns 
                          if col not in ['Customer', 'Year', 'Total']]
        print(f"Service categories: {len(service_columns)}")
        
        # Generate year-by-year revenue summary
        print("\nYearly Revenue Summary:")
        try:
            yearly_totals = self.combined_data.groupby('Year')['Total'].sum()
            for year, total in yearly_totals.items():
                # Check if total is a string and convert if needed
                if isinstance(total, str):
                    # Remove commas and convert to float
                    try:
                        clean_total = float(total.replace(',', '').replace('$', ''))
                        print(f"  {year}: ${clean_total:.2f}")
                    except ValueError:
                        print(f"  {year}: {total} (could not convert to number)")
                else:
                    print(f"  {year}: ${float(total):.2f}")
            
            # Calculate the total across all years
            total_sum = 0
            for total in yearly_totals:
                if isinstance(total, str):
                    try:
                        total_sum += float(total.replace(',', '').replace('$', ''))
                    except ValueError:
                        pass  # Skip if we can't convert
                else:
                    total_sum += float(total)
            
            print(f"\nTotal Revenue: ${total_sum:.2f}")
        except Exception as e:
            print(f"Error processing yearly revenue: {str(e)}")
        
        # Top 5 customers by revenue
        print("\nTop 5 Customers (by Revenue):")
        try:
            customer_totals = self.combined_data.groupby('Customer')['Total'].sum()
            customer_totals = customer_totals.astype(str).apply(lambda x: float(x.replace(',', '').replace('$', '')) if isinstance(x, str) else float(x))
            top_customers = customer_totals.sort_values(ascending=False).head(5)
            
            for customer, total in top_customers.items():
                print(f"  {customer}: ${float(total):.2f}")
        except Exception as e:
            print(f"Error processing top customers: {str(e)}")
        
        # Top 5 services by revenue
        print("\nTop 5 Services (by Revenue):")
        try:
            service_totals = {}
            for service in service_columns:
                # Convert column to numeric, handling string values
                col_values = self.combined_data[service].astype(str).apply(
                    lambda x: float(x.replace(',', '').replace('$', '')) 
                    if x and x != 'nan' and isinstance(x, str) 
                    else 0.0
                )
                total = col_values.sum()
                if total > 0:
                    service_totals[service] = total
            
            top_services = sorted(service_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            for service, total in top_services:
                print(f"  {service}: ${float(total):.2f}")
        except Exception as e:
            print(f"Error processing top services: {str(e)}")

def main():
    processor = QuickBooksProcessor()
    processor.process_all_files()
    processor.generate_summary_report()

if __name__ == "__main__":
    main() 