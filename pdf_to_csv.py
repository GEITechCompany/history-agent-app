import pdfplumber
import pandas as pd
import re

def extract_data_from_pdf(pdf_path):
    data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # Split text into lines and process each line
                lines = text.split('\n')
                for line in lines:
                    # Skip empty lines and headers
                    if line.strip() and not any(header in line.lower() for header in ['invoice', 'estimate', 'date', 'total']):
                        # Try to extract relevant information
                        # This pattern might need adjustment based on your PDF structure
                        match = re.match(r'(.+?)\s+(\d+(?:\.\d{2})?)', line)
                        if match:
                            description = match.group(1).strip()
                            amount = match.group(2)
                            data.append({
                                'Description': description,
                                'Amount': amount
                            })
    
    return data

def main():
    pdf_path = 'Invoice (Freshbooks).pdf'
    output_path = 'Invoice (Freshbooks).csv'
    
    print("Starting PDF to CSV conversion...")
    data = extract_data_from_pdf(pdf_path)
    
    if data:
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        print(f"Conversion complete! Data saved to {output_path}")
    else:
        print("No data was extracted from the PDF. Please check the PDF format.")

if __name__ == "__main__":
    main() 