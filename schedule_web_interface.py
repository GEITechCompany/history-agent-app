#!/usr/bin/env python3
import os
import pandas as pd
import sqlite3
from flask import Flask, render_template, request, jsonify, send_file
import json
from datetime import datetime
import tempfile
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Check if required packages are installed
try:
    from flask import Flask
except ImportError:
    print("Flask is not installed. Please install it with: pip3 install flask")
    print("Then run this script again.")
    exit(1)

# Create Flask app
app = Flask(__name__)

# Make sure the templates directory exists
os.makedirs('templates', exist_ok=True)

# Create the HTML templates
@app.route('/')
def index():
    return render_template('index.html')

# Function to get database connection
def get_db_connection():
    conn = sqlite3.connect('schedules.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create basic HTML template
index_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Schedule Data Browser</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            padding: 20px;
        }
        .card {
            margin-bottom: 20px;
        }
        .table-responsive {
            max-height: 500px;
            overflow-y: auto;
        }
        #vizContainer {
            height: 400px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="my-4">Schedule Data Browser</h1>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title">Search Jobs</h5>
                    </div>
                    <div class="card-body">
                        <form id="searchForm">
                            <div class="mb-3">
                                <label for="searchQuery" class="form-label">Search Query</label>
                                <input type="text" class="form-control" id="searchQuery" placeholder="Enter search terms">
                            </div>
                            <div class="mb-3">
                                <label for="searchColumn" class="form-label">Search Column</label>
                                <select class="form-control" id="searchColumn">
                                    <option value="all">All Columns</option>
                                    <!-- Columns will be added dynamically -->
                                </select>
                            </div>
                            <button type="submit" class="btn btn-primary">Search</button>
                        </form>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title">Date Range Search</h5>
                    </div>
                    <div class="card-body">
                        <form id="dateForm">
                            <div class="mb-3">
                                <label for="dateColumn" class="form-label">Date Column</label>
                                <select class="form-control" id="dateColumn">
                                    <!-- Date columns will be added dynamically -->
                                </select>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="startDate" class="form-label">Start Date</label>
                                    <input type="date" class="form-control" id="startDate">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label for="endDate" class="form-label">End Date</label>
                                    <input type="date" class="form-control" id="endDate">
                                </div>
                            </div>
                            <button type="submit" class="btn btn-primary">Search</button>
                        </form>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title">Visualization</h5>
                    </div>
                    <div class="card-body">
                        <form id="vizForm">
                            <div class="mb-3">
                                <label for="vizType" class="form-label">Visualization Type</label>
                                <select class="form-control" id="vizType">
                                    <option value="jobs_by_date">Jobs by Date</option>
                                    <option value="jobs_by_client">Jobs by Client</option>
                                </select>
                            </div>
                            <button type="submit" class="btn btn-primary">Generate</button>
                        </form>
                        <div id="vizContainer" class="mt-3">
                            <canvas id="vizChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="card-title mb-0">Results</h5>
                        <span id="resultCount" class="badge bg-info">0 Results</span>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover" id="resultsTable">
                                <thead>
                                    <tr id="tableHeader">
                                        <!-- Headers will be added dynamically -->
                                    </tr>
                                </thead>
                                <tbody id="tableBody">
                                    <!-- Results will be added dynamically -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title">Export Options</h5>
                    </div>
                    <div class="card-body">
                        <button id="exportCSV" class="btn btn-success me-2">Export to CSV</button>
                        <button id="exportExcel" class="btn btn-success">Export to Excel</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Load database metadata when page loads
        let dbMetadata = {};
        let currentResults = [];
        
        fetch('/api/metadata')
            .then(response => response.json())
            .then(data => {
                dbMetadata = data;
                
                // Populate column dropdowns
                const searchColumnSelect = document.getElementById('searchColumn');
                const dateColumnSelect = document.getElementById('dateColumn');
                
                // Add all columns to search dropdown
                Object.keys(dbMetadata.columns).forEach(column => {
                    const option = document.createElement('option');
                    option.value = column;
                    option.textContent = column;
                    searchColumnSelect.appendChild(option);
                });
                
                // Add date columns to date dropdown
                dbMetadata.date_columns.forEach(column => {
                    const option = document.createElement('option');
                    option.value = column;
                    option.textContent = column;
                    dateColumnSelect.appendChild(option);
                });
                
                // Load initial data
                fetch('/api/jobs?limit=100')
                    .then(response => response.json())
                    .then(data => {
                        displayResults(data);
                    });
            });
        
        // Handle search form submission
        document.getElementById('searchForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const query = document.getElementById('searchQuery').value;
            const column = document.getElementById('searchColumn').value;
            
            fetch(`/api/search?query=${encodeURIComponent(query)}&column=${encodeURIComponent(column)}`)
                .then(response => response.json())
                .then(data => {
                    displayResults(data);
                });
        });
        
        // Handle date form submission
        document.getElementById('dateForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const dateColumn = document.getElementById('dateColumn').value;
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            
            fetch(`/api/date_search?column=${encodeURIComponent(dateColumn)}&start=${encodeURIComponent(startDate)}&end=${encodeURIComponent(endDate)}`)
                .then(response => response.json())
                .then(data => {
                    displayResults(data);
                });
        });
        
        // Handle visualization form submission
        document.getElementById('vizForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const vizType = document.getElementById('vizType').value;
            
            fetch(`/api/visualization?type=${encodeURIComponent(vizType)}`)
                .then(response => response.json())
                .then(data => {
                    displayVisualization(vizType, data);
                });
        });
        
        // Export to CSV
        document.getElementById('exportCSV').addEventListener('click', function() {
            if (currentResults.length === 0) {
                alert('No data to export');
                return;
            }
            
            window.location.href = '/api/export?format=csv';
        });
        
        // Export to Excel
        document.getElementById('exportExcel').addEventListener('click', function() {
            if (currentResults.length === 0) {
                alert('No data to export');
                return;
            }
            
            window.location.href = '/api/export?format=excel';
        });
        
        // Function to display results
        function displayResults(data) {
            currentResults = data;
            
            const tableHeader = document.getElementById('tableHeader');
            const tableBody = document.getElementById('tableBody');
            const resultCount = document.getElementById('resultCount');
            
            // Clear previous results
            tableHeader.innerHTML = '';
            tableBody.innerHTML = '';
            
            if (data.length === 0) {
                resultCount.textContent = '0 Results';
                return;
            }
            
            resultCount.textContent = `${data.length} Results`;
            
            // Add headers
            const headers = Object.keys(data[0]);
            headers.forEach(header => {
                const th = document.createElement('th');
                th.textContent = header;
                tableHeader.appendChild(th);
            });
            
            // Add rows
            data.forEach(row => {
                const tr = document.createElement('tr');
                
                headers.forEach(header => {
                    const td = document.createElement('td');
                    td.textContent = row[header] || '';
                    tr.appendChild(td);
                });
                
                tableBody.appendChild(tr);
            });
        }
        
        // Function to display visualization
        function displayVisualization(type, data) {
            const canvas = document.getElementById('vizChart');
            
            // Clear previous chart
            if (window.chart) {
                window.chart.destroy();
            }
            
            if (type === 'jobs_by_date') {
                // Create a bar chart for jobs by date
                const labels = data.map(item => item.date);
                const values = data.map(item => item.count);
                
                window.chart = new Chart(canvas, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Jobs per Day',
                            data: values,
                            backgroundColor: 'rgba(54, 162, 235, 0.5)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            } else if (type === 'jobs_by_client') {
                // Create a pie chart for jobs by client
                const labels = data.map(item => item.client);
                const values = data.map(item => item.count);
                
                window.chart = new Chart(canvas, {
                    type: 'pie',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: values,
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.5)',
                                'rgba(54, 162, 235, 0.5)',
                                'rgba(255, 206, 86, 0.5)',
                                'rgba(75, 192, 192, 0.5)',
                                'rgba(153, 102, 255, 0.5)',
                                'rgba(255, 159, 64, 0.5)',
                                'rgba(199, 199, 199, 0.5)',
                                'rgba(83, 102, 255, 0.5)',
                                'rgba(40, 159, 64, 0.5)',
                                'rgba(210, 102, 210, 0.5)'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }
        }
    </script>
</body>
</html>
"""

# Create the HTML template file
with open('templates/index.html', 'w') as f:
    f.write(index_html)

# API endpoints
@app.route('/api/metadata')
def get_metadata():
    """Return database metadata"""
    if os.path.exists('schedule_db_metadata.json'):
        with open('schedule_db_metadata.json', 'r') as f:
            return json.load(f)
    else:
        return jsonify({
            "error": "Metadata not found. Please run schedule_database.py first."
        }), 404

@app.route('/api/jobs')
def get_jobs():
    """Return all jobs with pagination"""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    if not os.path.exists('schedules.db'):
        return jsonify({"error": "Database not found. Please run schedule_database.py first."}), 404
    
    conn = get_db_connection()
    jobs = conn.execute(f'SELECT * FROM jobs LIMIT {limit} OFFSET {offset}').fetchall()
    conn.close()
    
    return jsonify([dict(job) for job in jobs])

@app.route('/api/search')
def search_jobs():
    """Search jobs by keyword"""
    query = request.args.get('query', '', type=str)
    column = request.args.get('column', 'all', type=str)
    
    if not query:
        return jsonify([])
    
    if not os.path.exists('schedules.db'):
        return jsonify({"error": "Database not found. Please run schedule_database.py first."}), 404
    
    conn = get_db_connection()
    
    if column == 'all':
        # Need to search all columns - get column names first
        columns = conn.execute('PRAGMA table_info(jobs)').fetchall()
        column_names = [col['name'] for col in columns if col['name'] != 'id']
        
        # Build a query that searches all columns
        query_parts = []
        for col in column_names:
            query_parts.append(f"{col} LIKE '%{query}%'")
        
        sql_query = f"SELECT * FROM jobs WHERE {' OR '.join(query_parts)}"
    else:
        # Search in specific column
        sql_query = f"SELECT * FROM jobs WHERE {column} LIKE '%{query}%'"
    
    jobs = conn.execute(sql_query).fetchall()
    conn.close()
    
    return jsonify([dict(job) for job in jobs])

@app.route('/api/date_search')
def date_search():
    """Search jobs by date range"""
    column = request.args.get('column', '', type=str)
    start_date = request.args.get('start', '', type=str)
    end_date = request.args.get('end', '', type=str)
    
    if not column:
        return jsonify([])
    
    if not os.path.exists('schedules.db'):
        return jsonify({"error": "Database not found. Please run schedule_database.py first."}), 404
    
    conn = get_db_connection()
    
    sql_parts = []
    params = []
    
    if start_date:
        sql_parts.append(f"{column} >= ?")
        params.append(start_date)
    
    if end_date:
        sql_parts.append(f"{column} <= ?")
        params.append(end_date)
    
    if sql_parts:
        sql_query = f"SELECT * FROM jobs WHERE {' AND '.join(sql_parts)}"
        jobs = conn.execute(sql_query, params).fetchall()
    else:
        jobs = conn.execute(f"SELECT * FROM jobs WHERE {column} IS NOT NULL").fetchall()
    
    conn.close()
    
    return jsonify([dict(job) for job in jobs])

@app.route('/api/visualization')
def visualization():
    """Generate visualization data"""
    viz_type = request.args.get('type', 'jobs_by_date', type=str)
    
    if not os.path.exists('schedules.db'):
        return jsonify({"error": "Database not found. Please run schedule_database.py first."}), 404
    
    conn = get_db_connection()
    
    if viz_type == 'jobs_by_date':
        # Get metadata to find date column
        with open('schedule_db_metadata.json', 'r') as f:
            metadata = json.load(f)
        
        if not metadata.get('date_columns'):
            return jsonify([])
        
        date_column = metadata['date_columns'][0]
        
        # Query jobs by date
        sql_query = f"""
            SELECT {date_column} as date, COUNT(*) as count 
            FROM jobs 
            WHERE {date_column} IS NOT NULL 
            GROUP BY {date_column} 
            ORDER BY {date_column}
        """
        results = conn.execute(sql_query).fetchall()
        
    elif viz_type == 'jobs_by_client':
        # Get metadata to find client column
        with open('schedule_db_metadata.json', 'r') as f:
            metadata = json.load(f)
        
        if not metadata.get('client_columns'):
            return jsonify([])
        
        client_column = metadata['client_columns'][0]
        
        # Query jobs by client
        sql_query = f"""
            SELECT {client_column} as client, COUNT(*) as count 
            FROM jobs 
            WHERE {client_column} IS NOT NULL 
            GROUP BY {client_column} 
            ORDER BY count DESC
            LIMIT 10
        """
        results = conn.execute(sql_query).fetchall()
    
    conn.close()
    
    return jsonify([dict(row) for row in results])

@app.route('/api/export')
def export_data():
    """Export current results to CSV or Excel"""
    export_format = request.args.get('format', 'csv', type=str)
    
    if not os.path.exists('schedules.db'):
        return jsonify({"error": "Database not found. Please run schedule_database.py first."}), 404
    
    # Get all jobs
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs').fetchall()
    conn.close()
    
    # Convert to DataFrame
    df = pd.DataFrame([dict(job) for job in jobs])
    
    if export_format == 'csv':
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        df.to_csv(temp_file.name, index=False)
        return send_file(temp_file.name, as_attachment=True, download_name='schedule_data.csv')
    else:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        df.to_excel(temp_file.name, index=False)
        return send_file(temp_file.name, as_attachment=True, download_name='schedule_data.xlsx')

if __name__ == '__main__':
    print("Starting Schedule Web Interface...")
    
    # Check if database exists, if not create it
    if not os.path.exists('schedules.db'):
        print("Database not found. Please run schedule_database.py first.")
        print("You can create the database by running: python3 schedule_database.py")
    else:
        # Check if we have Flask installed
        try:
            import flask
            print("Starting web server at http://127.0.0.1:5000")
            print("Press Ctrl+C to stop the server")
            app.run(debug=True)
        except ImportError:
            print("Flask is not installed. Please install it with: pip3 install flask")
            print("Then run this script again.") 