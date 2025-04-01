import pandas as pd
import os
import datetime
import re
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init()

class CalendarAdapter:
    """
    Adapter for processing and enhancing calendar event data.
    This class helps integrate calendar data with the rest of the search functionality.
    """
    
    def __init__(self, calendar_file='cleaned_calendar_events.csv'):
        self.calendar_file = calendar_file
        self.calendar_df = None
        
        # Load the calendar data if the file exists
        if os.path.exists(calendar_file):
            try:
                self.calendar_df = pd.read_csv(calendar_file)
                print(f"{Fore.GREEN}Successfully loaded calendar data from {calendar_file}{Style.RESET_ALL}")
                print(f"Found {len(self.calendar_df)} calendar events")
            except Exception as e:
                print(f"{Fore.RED}Error loading calendar data: {str(e)}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Calendar file {calendar_file} not found{Style.RESET_ALL}")
    
    def enrich_event_data(self):
        """
        Enhance the calendar data with additional fields to make searching more effective.
        - Extract client names and contact information from descriptions
        - Standardize date formats
        - Add searchable tags
        """
        if self.calendar_df is None:
            print(f"{Fore.RED}No calendar data loaded{Style.RESET_ALL}")
            return False
        
        try:
            # Create a client name field based on the Summary field
            self.calendar_df['Client_Name'] = self.calendar_df['Summary'].apply(self._extract_client_name)
            
            # Create a location field if one doesn't exist or is empty
            if 'Location' not in self.calendar_df.columns or self.calendar_df['Location'].isna().all():
                self.calendar_df['Location'] = self.calendar_df['Description'].apply(self._extract_location)
            
            # Create a standardized date field
            self.calendar_df['Event_Date'] = self.calendar_df['Start Date'].apply(
                lambda x: x.split(' ')[0] if isinstance(x, str) and ' ' in x else x)
            
            # Create a tags field for improved searchability
            self.calendar_df['Tags'] = self.calendar_df.apply(self._generate_tags, axis=1)
            
            # Save the enriched data
            self.calendar_df.to_csv('enriched_calendar_events.csv', index=False)
            
            print(f"{Fore.GREEN}Successfully enriched calendar data{Style.RESET_ALL}")
            return True
        
        except Exception as e:
            print(f"{Fore.RED}Error enriching calendar data: {str(e)}{Style.RESET_ALL}")
            return False
    
    def _extract_client_name(self, summary):
        """Extract client name from the event summary"""
        if not isinstance(summary, str):
            return ""
        
        # Look for patterns like "NAME: John Smith" or similar
        match = re.search(r'(?:for|client|customer|with|:)\s*([A-Za-z\s]+)', summary, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # If colon exists, take what's after the colon
        if ':' in summary:
            return summary.split(':', 1)[1].strip()
        
        # Otherwise return the full summary
        return summary
    
    def _extract_location(self, description):
        """Extract location from the event description"""
        if not isinstance(description, str):
            return ""
        
        # Look for address patterns
        address_pattern = r'(?:address|location|at):\s*([^,|]+(?:avenue|street|st|ave|road|rd|drive|dr|blvd|boulevard)[^,|]*)'
        match = re.search(address_pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _generate_tags(self, row):
        """Generate searchable tags from the event data"""
        tags = []
        
        # Add calendar type as a tag
        if isinstance(row.get('Calendar'), str):
            tags.append(row['Calendar'])
        
        # Add event status as a tag
        if isinstance(row.get('Status'), str):
            tags.append(row['Status'])
        
        # Add client name as tags if available
        if isinstance(row.get('Client_Name'), str) and row['Client_Name']:
            tags.append(row['Client_Name'])
        
        # Extract company names from the description
        if isinstance(row.get('Description'), str):
            company_pattern = r'(?:company|vendor|supplier|client):\s*([A-Za-z\s]+)'
            companies = re.findall(company_pattern, row['Description'], re.IGNORECASE)
            tags.extend(companies)
        
        # Create a comma-separated string of tags
        return ", ".join(tags)

def process_calendar_data():
    """Process the calendar data and make it ready for searching"""
    adapter = CalendarAdapter()
    success = adapter.enrich_event_data()
    
    if success:
        print(f"{Fore.GREEN}Calendar data is ready for searching{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Warning: Calendar data processing failed{Style.RESET_ALL}")
    
    return success

if __name__ == "__main__":
    print(f"{Fore.CYAN}Processing calendar data...{Style.RESET_ALL}")
    process_calendar_data() 