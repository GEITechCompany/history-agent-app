import os
import pandas as pd
import re
import glob
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init()

class DailyScheduleProcessor:
    """
    Processor for daily schedule CSV files exported from Google Sheets.
    This class helps consolidate and standardize the daily schedule data for searching.
    """
    
    def __init__(self, schedules_folder='exported_sheets_actual'):
        self.schedules_folder = schedules_folder
        self.schedule_files = []
        self.combined_data = None
        
        # Find all CSV files in the specified folder
        if os.path.exists(schedules_folder):
            self.schedule_files = glob.glob(f"{schedules_folder}/*.csv")
            print(f"{Fore.GREEN}Found {len(self.schedule_files)} daily schedule files in {schedules_folder}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Schedule folder {schedules_folder} not found{Style.RESET_ALL}")
    
    def extract_date_from_filename(self, filename):
        """Extract the date from the daily schedule filename"""
        basename = os.path.basename(filename)
        
        # Try different date patterns
        date_patterns = [
            # MM_DD_YY
            r'(\d{2}_\d{2}_\d{2})',
            # More patterns can be added as needed
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, basename)
            if match:
                date_str = match.group(1)
                try:
                    # Convert to date object (assuming MM_DD_YY format)
                    parts = date_str.split('_')
                    if len(parts) == 3:
                        month, day, year = parts
                        # Add 20 prefix to year if it's just 2 digits
                        if len(year) == 2:
                            year = f"20{year}"
                        return f"{year}-{month}-{day}"
                except Exception:
                    pass
        
        # If no date found, try to infer from content or use modification date
        try:
            mod_time = os.path.getmtime(filename)
            return datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')
        except:
            return "Unknown"
    
    def process_schedule_file(self, file_path):
        """Process a single daily schedule file and extract structured data"""
        try:
            # Extract date from filename
            schedule_date = self.extract_date_from_filename(file_path)
            
            # Read the CSV file
            df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
            
            # Clean up the dataframe
            # Remove unnamed columns and empty rows
            df = df.dropna(how='all')
            
            # Extract jobs/tasks from the dataframe
            jobs = []
            current_job = {}
            
            for _, row in df.iterrows():
                row_values = row.values
                
                # Skip empty rows
                if all(pd.isna(x) for x in row_values):
                    if current_job and len(current_job) > 1:  # If we have a job with some data
                        jobs.append(current_job)
                        current_job = {}
                    continue
                
                # Process each row
                for cell in row_values:
                    if not isinstance(cell, str):
                        continue
                    
                    # Look for job field indicators
                    if "COMPANY:" in str(cell):
                        if current_job and len(current_job) > 1:  # If we have a job with some data
                            jobs.append(current_job)
                            current_job = {}
                        current_job['Schedule_Date'] = schedule_date
                        current_job['Source_File'] = os.path.basename(file_path)
                    
                    # Extract key-value pairs
                    if ':' in str(cell):
                        parts = cell.split(':', 1)
                        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                            key = parts[0].strip()
                            value = parts[1].strip()
                            current_job[key] = value
                    
                    # Look for addresses
                    address_pattern = r'(\d+\s+[A-Za-z\s]+(?:Avenue|Street|St|Ave|Road|Rd|Drive|Dr|Circle|Court|Crt|Blvd|Boulevard)(?:[,\s]+[A-Za-z\s]+)?(?:[,\s]+[A-Za-z]{2})?(?:[,\s]+[A-Z0-9]{5,7})?)'
                    address_matches = re.findall(address_pattern, str(cell), re.IGNORECASE)
                    if address_matches and 'Address' not in current_job:
                        current_job['Address'] = address_matches[0]
                    
                    # Look for contact information
                    phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
                    phone_matches = re.findall(phone_pattern, str(cell))
                    if phone_matches and 'Phone' not in current_job:
                        current_job['Phone'] = phone_matches[0]
                    
                    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
                    email_matches = re.findall(email_pattern, str(cell))
                    if email_matches and 'Email' not in current_job:
                        current_job['Email'] = email_matches[0]
            
            # Add the last job if it exists
            if current_job and len(current_job) > 1:
                jobs.append(current_job)
            
            return jobs
        
        except Exception as e:
            print(f"{Fore.RED}Error processing {file_path}: {str(e)}{Style.RESET_ALL}")
            return []
    
    def process_all_files(self):
        """Process all schedule files and combine them into a single dataset"""
        all_jobs = []
        
        for file_path in self.schedule_files:
            try:
                jobs = self.process_schedule_file(file_path)
                all_jobs.extend(jobs)
                print(f"Processed {file_path}: {len(jobs)} jobs found")
            except Exception as e:
                print(f"{Fore.RED}Error with file {file_path}: {str(e)}{Style.RESET_ALL}")
        
        # Convert to DataFrame
        if all_jobs:
            self.combined_data = pd.DataFrame(all_jobs)
            print(f"{Fore.GREEN}Successfully processed {len(all_jobs)} jobs from {len(self.schedule_files)} files{Style.RESET_ALL}")
            
            # Save to a consolidated CSV file
            output_file = 'consolidated_schedules.csv'
            self.combined_data.to_csv(output_file, index=False)
            print(f"{Fore.GREEN}Saved consolidated data to {output_file}{Style.RESET_ALL}")
            
            return True
        else:
            print(f"{Fore.YELLOW}No job data found in schedule files{Style.RESET_ALL}")
            return False

def process_daily_schedules():
    """Process all daily schedule files and prepare them for searching"""
    processor = DailyScheduleProcessor()
    success = processor.process_all_files()
    
    if success:
        print(f"{Fore.GREEN}Daily schedule data is ready for searching{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Warning: Daily schedule processing completed with issues{Style.RESET_ALL}")
    
    return success

if __name__ == "__main__":
    print(f"{Fore.CYAN}Processing daily schedule data...{Style.RESET_ALL}")
    process_daily_schedules() 