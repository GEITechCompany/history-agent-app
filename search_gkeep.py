import pandas as pd
import re
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init()

def main():
    print(f"{Fore.CYAN}Loading GKeep (Simple).csv...{Style.RESET_ALL}")
    
    try:
        # First, load the file as is to understand its structure
        df = pd.read_csv('GKeep (Simple).csv')
        
        print(f"{Fore.GREEN}File loaded successfully.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Shape: {df.shape}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Columns: {df.columns.tolist()}{Style.RESET_ALL}")
        
        # The file appears to have only one column that contains all data
        column_name = df.columns[0]
        
        # Search for "Anna Wong" in the single column
        print(f"{Fore.CYAN}Searching for 'Anna Wong' in the file...{Style.RESET_ALL}")
        matches = []
        
        for idx, row in df.iterrows():
            cell_value = str(row[column_name])
            if 'anna wong' in cell_value.lower():
                matches.append((idx, cell_value))
                
        if matches:
            print(f"{Fore.GREEN}Found {len(matches)} matches for 'Anna Wong' in GKeep (Simple).csv:{Style.RESET_ALL}")
            for idx, value in matches:
                print(f"{Fore.YELLOW}Row {idx}:{Style.RESET_ALL}")
                print(f"{Fore.GREEN}{value}{Style.RESET_ALL}")
                print("")
        else:
            print(f"{Fore.YELLOW}No matches found for 'Anna Wong' in GKeep (Simple).csv{Style.RESET_ALL}")
            
        # Let's try a different approach - load as plain text
        print(f"{Fore.CYAN}Trying alternative approach - loading file as text...{Style.RESET_ALL}")
        
        with open('GKeep (Simple).csv', 'r', encoding='utf-8') as file:
            text = file.read()
            
        # Search for "Anna Wong" in the text
        pattern = re.compile(r'(?i)anna\s+wong')
        text_matches = list(pattern.finditer(text))
        
        if text_matches:
            print(f"{Fore.GREEN}Found {len(text_matches)} text matches for 'Anna Wong':{Style.RESET_ALL}")
            for match in text_matches:
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]
                highlighted = context.replace(match.group(), f"{Fore.RED}{match.group()}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Context:{Style.RESET_ALL}")
                print(f"{highlighted}")
                print("")
        else:
            print(f"{Fore.YELLOW}No text matches found for 'Anna Wong'{Style.RESET_ALL}")
            
        # Let's do a broader search for just "Wong"
        broader_pattern = re.compile(r'(?i)wong')
        broader_matches = list(broader_pattern.finditer(text))
        
        if broader_matches:
            print(f"{Fore.GREEN}Found {len(broader_matches)} text matches for 'Wong':{Style.RESET_ALL}")
            for match in broader_matches:
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]
                highlighted = context.replace(match.group(), f"{Fore.RED}{match.group()}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Context:{Style.RESET_ALL}")
                print(f"{highlighted}")
                print("")
        else:
            print(f"{Fore.YELLOW}No text matches found for 'Wong'{Style.RESET_ALL}")
                
    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        
if __name__ == "__main__":
    main() 