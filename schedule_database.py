#!/usr/bin/env python3
import os
import pandas as pd
import sqlite3
from datetime import datetime
import json
import re

def create_schedule_database():
    """
    Creates a SQLite database from the consolidated schedule data
    for better querying and management.
    """
    # Check if consolidated schedule data exists
    if not os.path.exists('consolidated_schedules.csv'):
        print("Consolidated schedule data not found. Please run daily_schedule_processor.py first.")
        return False
    
    print("Reading consolidated schedule data...")
    # Read the consolidated schedule data
    data = pd.read_csv('consolidated_schedules.csv')
    
    # Create SQLite database
    db_file = 'schedules.db'
    print(f"Creating SQLite database: {db_file}...")
    
    # Make sure the database is removed if it exists
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Removed existing database: {db_file}")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create jobs table with appropriate columns
    # First, clean column names for SQL (remove spaces, special chars)
    def clean_column_name(name):
        # More thorough cleaning to prevent SQL syntax errors
        # Convert to lowercase, replace spaces and special chars with underscore
        clean_name = re.sub(r'[^a-zA-Z0-9]', '_', str(name).lower())
        # Ensure name doesn't start with a number
        if clean_name[0].isdigit():
            clean_name = 'col_' + clean_name
        # Ensure no duplicate underscores
        clean_name = re.sub(r'_+', '_', clean_name)
        # Trim trailing underscores
        clean_name = clean_name.rstrip('_')
        return clean_name
    
    # Create a mapping of original column names to clean names
    # Also handle duplicates by appending a number
    column_mapping = {}
    used_names = {}
    
    for col in data.columns:
        clean_name = clean_column_name(col)
        
        # Check if this clean name is already used
        if clean_name in used_names:
            # Append a number to make it unique
            count = used_names[clean_name] + 1
            used_names[clean_name] = count
            clean_name = f"{clean_name}_{count}"
        else:
            used_names[clean_name] = 1
        
        column_mapping[col] = clean_name
    
    # Determine column types based on data content
    column_types = {}
    date_columns = []
    
    for column in data.columns:
        clean_name = column_mapping[column]
        
        # Check if column might be a date column
        if 'date' in column.lower():
            column_types[clean_name] = 'TEXT'
            date_columns.append(column)
            continue
        
        # Sample some non-null values to determine type
        sample = data[column].dropna().head(10)
        if len(sample) == 0:
            column_types[clean_name] = 'TEXT'  # Default to TEXT if no samples
            continue
        
        # Check if all samples can be converted to numeric
        try:
            pd.to_numeric(sample)
            column_types[clean_name] = 'REAL'
        except:
            column_types[clean_name] = 'TEXT'
    
    # Rename DataFrame columns to clean names
    data_for_db = data.copy()
    data_for_db = data_for_db.rename(columns=column_mapping)
    
    # Create the jobs table
    columns_list = []
    for col in data.columns:
        clean_name = column_mapping[col]
        col_type = column_types[clean_name]
        columns_list.append(f'"{clean_name}" {col_type}')
    
    columns_sql = ', '.join(columns_list)
    create_table_sql = f'CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns_sql})'
    
    try:
        cursor.execute(create_table_sql)
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")
        print(f"SQL that failed: {create_table_sql}")
        conn.close()
        return False
    
    # Convert date columns to consistent format
    for col in date_columns:
        clean_col = column_mapping[col]
        try:
            data_for_db[clean_col] = pd.to_datetime(data_for_db[clean_col], errors='coerce').dt.strftime('%Y-%m-%d')
        except:
            pass  # Skip if conversion fails
    
    # Insert data into the database
    print(f"Inserting {len(data_for_db)} records into database...")
    
    # Prepare column names for INSERT statement
    clean_columns = [column_mapping[col] for col in data.columns]
    columns_str = ', '.join([f'"{col}"' for col in clean_columns])
    placeholders = ', '.join(['?' for _ in clean_columns])
    
    # Insert data row by row
    insert_sql = f'INSERT INTO jobs ({columns_str}) VALUES ({placeholders})'
    
    for _, row in data_for_db.iterrows():
        # Convert row values to list, handling NaN values
        values = []
        for val in row:
            if pd.isna(val):
                values.append(None)
            elif isinstance(val, (int, float)):
                values.append(val)
            else:
                values.append(str(val))
        
        try:
            cursor.execute(insert_sql, values)
        except sqlite3.Error as e:
            print(f"Error inserting row: {e}")
            print(f"Values: {values}")
            continue
    
    # Create indexes for common search columns
    print("Creating indexes for common search columns...")
    
    # Index date columns
    for col in date_columns:
        clean_name = column_mapping[col]
        try:
            cursor.execute(f'CREATE INDEX idx_{clean_name} ON jobs ("{clean_name}")')
        except sqlite3.Error as e:
            print(f"Error creating index for {clean_name}: {e}")
    
    # Index client/customer columns
    client_columns = [col for col in data.columns if any(term in col.lower() 
                     for term in ['client', 'customer', 'name', 'company'])]
    
    for col in client_columns:
        clean_name = column_mapping[col]
        try:
            cursor.execute(f'CREATE INDEX idx_{clean_name} ON jobs ("{clean_name}")')
        except sqlite3.Error as e:
            print(f"Error creating index for {clean_name}: {e}")
    
    # Commit changes and close connection
    conn.commit()
    
    # Create and save metadata about the database
    metadata = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_records": len(data),
        "columns": {col: column_types[column_mapping[col]] for col in data.columns},
        "date_columns": date_columns,
        "client_columns": client_columns,
        "column_mapping": column_mapping
    }
    
    with open('schedule_db_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Create some example queries
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cursor.fetchone()[0]
    
    print("\nDatabase created successfully!")
    print(f"Total jobs in database: {total_jobs}")
    
    # Show example queries
    print("\nExample SQL queries you can run:")
    print("1. Find all jobs for a specific client:")
    if client_columns:
        client_col = column_mapping[client_columns[0]]
        print(f'   SELECT * FROM jobs WHERE "{client_col}" LIKE "%ClientName%"')
    
    print("2. Find jobs between specific dates:")
    if date_columns:
        date_col = column_mapping[date_columns[0]]
        print(f'   SELECT * FROM jobs WHERE "{date_col}" BETWEEN "2023-01-01" AND "2023-12-31"')
    
    print("3. Count jobs by date:")
    if date_columns:
        date_col = column_mapping[date_columns[0]]
        print(f'   SELECT "{date_col}", COUNT(*) as job_count FROM jobs GROUP BY "{date_col}" ORDER BY job_count DESC')
    
    conn.close()
    return True

def query_database(sql_query):
    """
    Execute a SQL query on the schedule database and return the results.
    
    Args:
        sql_query (str): SQL query to execute
        
    Returns:
        list: List of records matching the query
    """
    if not os.path.exists('schedules.db'):
        print("Database not found. Please run create_schedule_database() first.")
        return None
    
    try:
        conn = sqlite3.connect('schedules.db')
        # Return results as dictionaries
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(sql_query)
        results = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return results
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

if __name__ == "__main__":
    create_schedule_database() 