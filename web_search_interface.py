import os
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from fuzzywuzzy import fuzz
import json
import tempfile
import datetime
import sys
import re
from colorama import Fore, Style, init
import traceback

# Import our DeepSearchAgent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deep_search_agent import DeepSearchAgent

# Ensure templates directory exists
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
if not os.path.exists(template_dir):
    os.makedirs(template_dir)

app = Flask(__name__, 
           template_folder=template_dir)  # Explicitly set template folder
app.config['JSON_SORT_KEYS'] = False

# Initialize the Deep Search Agent
search_agent = DeepSearchAgent()

@app.route('/')
def index():
    """Render the main search page"""
    # Get list of all available CSV files
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    # Get a list of available columns from the first few CSV files
    sample_columns = set()
    for csv_file in csv_files[:5]:  # Limit to first 5 files to avoid too many columns
        try:
            df = pd.read_csv(csv_file)
            sample_columns.update(df.columns)
        except:
            pass
    
    try:
        # Try to render the template normally
        return render_template('index.html', csv_files=csv_files, sample_columns=sorted(sample_columns))
    except Exception as e:
        # If template rendering fails, return a simple HTML page directly
        print(f"{Fore.RED}Error rendering template: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Returning simple HTML interface{Style.RESET_ALL}")
        
        # Create a simple HTML response
        html = f"""<!DOCTYPE html>
        <html>
        <head>
            <title>Client Search Interface (Simple)</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1 class="mb-4">Client Search Interface</h1>
                <div class="card">
                    <div class="card-body">
                        <form action="/search" method="post">
                            <div class="mb-3">
                                <label for="query" class="form-label">Search Query</label>
                                <input type="text" class="form-control" id="query" name="query" 
                                       placeholder="Enter search term (e.g., 'Anna Wong')">
                            </div>
                            <div class="form-check mb-3">
                                <input class="form-check-input" type="checkbox" id="fuzzy" name="fuzzy" checked>
                                <label class="form-check-label" for="fuzzy">Enable fuzzy matching</label>
                            </div>
                            <!-- Add hidden field for HTML output -->
                            <input type="hidden" name="html_output" value="true">
                            <button type="submit" class="btn btn-primary">Search</button>
                        </form>
                    </div>
                </div>
                <div class="mt-3">
                    <p>Available CSV files: {", ".join(csv_files)}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

@app.route('/search', methods=['POST'])
def search():
    """Perform search based on form inputs"""
    query = request.form.get('query', '')
    fuzzy = 'fuzzy' in request.form
    columns = request.form.get('columns', '').split(',') if request.form.get('columns') else None
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')
    
    # If columns is empty or just contains an empty string, set to None
    if not columns or (len(columns) == 1 and not columns[0].strip()):
        columns = None
    
    # Debug settings
    debug = 'debug' in request.form
    
    # Extract common search pattern if indicated
    if 'extract_pattern' in request.form and request.form.get('extract_pattern'):
        query = extract_search_pattern(query)
    
    # Check if direct html output is requested (for browser form submission)
    return_html = 'html_output' in request.form or request.headers.get('Accept', '').find('text/html') > -1
    
    # Perform search
    try:
        if fuzzy:
            results = search_agent.fuzzy_search(query, columns=columns)
        else:
            results = search_agent.exact_search(query, columns=columns)
            
        # Apply date range filtering if specified
        if start_date or end_date:
            results = search_agent.filter_by_date_range(results, start_date, end_date)
            
        # Format results for display and return as JSON
        formatted_results = []
        
        for result in results:
            # Create a formatted result dictionary
            formatted_result = {
                'source_file': result.get('file', 'Unknown'),
                'match_score': result.get('match_score', None),
                'matching_value': result.get('matching_value', None),
                'fields': {}
            }
            
            # Add all non-metadata fields
            for field, value in result.items():
                if field not in ['file', 'match_score', 'matching_value'] and pd.notna(value):
                    formatted_result['fields'][field] = str(value)
            
            formatted_results.append(formatted_result)
        
        # Return results in the appropriate format
        if return_html:
            # Generate HTML response for direct browser viewing
            html = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>Search Results: {query}</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-3">
                    <h1>Search Results</h1>
                    <p>Found {len(formatted_results)} results for: <strong>{query}</strong></p>
                    <a href="/" class="btn btn-primary mb-3">Back to Search</a>
                    
                    <div class="results">
            """
            
            # Add results to HTML
            for i, result in enumerate(formatted_results, 1):
                html += f"""
                    <div class="card mb-3">
                        <div class="card-header d-flex justify-content-between">
                            <span>Result {i} of {len(formatted_results)}</span>
                            <span class="text-muted small">Source: {result['source_file']}</span>
                        </div>
                        <div class="card-body">
                """
                
                # Add match information if available
                if result.get('match_score'):
                    html += f"<p class='badge bg-info'>Match Score: {result['match_score']}%</p><br>"
                
                if result.get('matching_value'):
                    html += f"<p class='alert alert-warning p-1'>Matching value: {result['matching_value']}</p>"
                
                # Add all fields
                html += "<table class='table table-striped'><tbody>"
                for field, value in result['fields'].items():
                    html += f"<tr><th>{field}</th><td>{value}</td></tr>"
                html += "</tbody></table>"
                
                html += """
                        </div>
                    </div>
                """
            
            # Close HTML
            html += """
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html
        else:
            # Return JSON response
            return jsonify({
                'success': True,
                'query': query,
                'results_count': len(formatted_results),
                'results': formatted_results
            })
        
    except Exception as e:
        # Log the error and return an error response
        error_msg = f"Error during search: {str(e)}"
        if debug:
            error_msg += "\n" + traceback.format_exc()
            
        if return_html:
            # Return error as HTML
            html = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>Search Error</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-5">
                    <div class="alert alert-danger">
                        <h4>Error performing search</h4>
                        <pre>{error_msg}</pre>
                    </div>
                    <a href="/" class="btn btn-primary">Back to Search</a>
                </div>
            </body>
            </html>
            """
            return html
        else:
            # Return error as JSON
            return jsonify({
                'success': False,
                'error': error_msg
            })

@app.route('/export', methods=['POST'])
def export():
    """Export search results to a file"""
    try:
        # Get export parameters
        format = request.form.get('format', 'csv')
        results_json = request.form.get('results')
        
        if not results_json:
            return jsonify({'success': False, 'error': 'No results to export'})
        
        # Parse results from JSON
        results = json.loads(results_json)
        
        # Create a temporary file for the export
        temp_fd, temp_path = tempfile.mkstemp(suffix=f'.{format}')
        os.close(temp_fd)
        
        # Process results to flatten the structure
        flattened_results = []
        for result in results:
            flat_result = {
                'Source File': result['source_file']
            }
            
            # Add match score and matching value if available
            if result.get('match_score'):
                flat_result['Match Score'] = result['match_score']
            
            if result.get('matching_value'):
                flat_result['Matching Value'] = result['matching_value']
            
            # Add all other fields
            for field, value in result['fields'].items():
                flat_result[field] = value
            
            flattened_results.append(flat_result)
        
        # Export based on format
        if format == 'json':
            with open(temp_path, 'w') as f:
                json.dump(flattened_results, f, indent=2)
        else:
            # Default to CSV
            df = pd.DataFrame(flattened_results)
            df.to_csv(temp_path, index=False)
        
        # Generate a unique filename based on query and timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"search_results_{timestamp}.{format}"
        
        # Different versions of Flask use different parameters
        try:
            # Try newer Flask version parameters
            return send_file(
                temp_path, 
                download_name=filename,
                as_attachment=True,
                max_age=0
            )
        except TypeError:
            # Fall back to older Flask version parameters
            return send_file(
                temp_path,
                attachment_filename=filename,
                as_attachment=True,
                cache_timeout=0
            )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error during export: {str(e)}"
        })

def extract_search_pattern(query):
    """Extract common search patterns from queries"""
    # Simple patterns
    patterns = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
        'postal_code': r'\b[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d\b',  # Canadian postal code
        'name': r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'  # Simple name pattern: First Last
    }
    
    # Try to extract each pattern type
    for pattern_type, regex in patterns.items():
        matches = re.findall(regex, query)
        if matches:
            return matches[0]  # Return the first match
    
    # If no pattern is found, return the original query
    return query

@app.route('/analyze', methods=['POST'])
def analyze_file():
    """Analyze the structure of a CSV file"""
    try:
        file_name = request.form.get('file_name', '')
        if not file_name:
            return jsonify({'success': False, 'error': 'No file specified'})
        
        # Load the file
        df = pd.read_csv(file_name)
        
        # Generate analysis
        analysis = {
            'file_name': file_name,
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'sample_data': df.head(5).to_dict('records'),
            'data_types': {col: str(df[col].dtype) for col in df.columns}
        }
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error analyzing file: {str(e)}"
        })

@app.route('/get_columns', methods=['POST'])
def get_columns():
    """Get columns from a specific CSV file"""
    try:
        file_name = request.form.get('file_name', '')
        if not file_name:
            return jsonify({'success': False, 'error': 'No file specified'})
        
        # Load the file
        df = pd.read_csv(file_name)
        
        # Get the columns
        columns = df.columns.tolist()
        
        return jsonify({
            'success': True,
            'columns': columns
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Error getting columns: {str(e)}"
        })

@app.route('/templates/index.html')
def serve_template():
    """Serve the template file directly"""
    return render_template('index.html')

# Create template directory and index.html if they don't exist
def ensure_template_exists():
    """Ensure that the template directory and index.html exist"""
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    
    # Create templates directory if it doesn't exist
    if not os.path.exists(template_dir):
        print(f"{Fore.YELLOW}Creating templates directory at {template_dir}{Style.RESET_ALL}")
        os.makedirs(template_dir)
    
    # Create index.html if it doesn't exist
    template_path = os.path.join(template_dir, 'index.html')
    if not os.path.exists(template_path):
        print(f"{Fore.YELLOW}Creating index.html template at {template_path}{Style.RESET_ALL}")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Client Search Interface</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding: 20px;
            background-color: #f8f9fa;
        }
        .search-container {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .result-card {
            background-color: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 0 5px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .result-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .source-file {
            font-size: 0.8em;
            color: #6c757d;
        }
        .result-field {
            margin-bottom: 5px;
        }
        .field-name {
            font-weight: bold;
            color: #495057;
        }
        .match-highlight {
            background-color: #ffeeba;
            padding: 2px 4px;
            border-radius: 3px;
        }
        .options-container {
            background-color: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .spinner-border {
            display: none;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4 text-center">Client Information Search</h1>
        
        <div class="search-container">
            <form id="searchForm">
                <div class="mb-3">
                    <label for="query" class="form-label">Search Query</label>
                    <input type="text" class="form-control" id="query" name="query" placeholder="Enter search term (name, email, phone, etc.)">
                </div>
                
                <div class="row mb-3">
                    <div class="col-md-6">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="fuzzy" name="fuzzy" checked>
                            <label class="form-check-label" for="fuzzy">
                                Enable fuzzy matching
                            </label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="extractPattern" name="extract_pattern">
                            <label class="form-check-label" for="extractPattern">
                                Extract search pattern (email, phone, etc.)
                            </label>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="debug" name="debug">
                            <label class="form-check-label" for="debug">
                                Debug mode
                            </label>
                        </div>
                    </div>
                </div>
                
                <div class="accordion mb-3" id="searchOptions">
                    <div class="accordion-item">
                        <h2 class="accordion-header">
                            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#advancedOptions">
                                Advanced Options
                            </button>
                        </h2>
                        <div id="advancedOptions" class="accordion-collapse collapse">
                            <div class="accordion-body">
                                <div class="mb-3">
                                    <label for="columns" class="form-label">Specific Columns (comma-separated)</label>
                                    <input type="text" class="form-control" id="columns" name="columns" placeholder="Leave empty to search all columns">
                                </div>
                                
                                <div class="mb-3">
                                    <label for="fileSelector" class="form-label">Get Columns from File</label>
                                    <select class="form-select" id="fileSelector">
                                        <option value="">Select a file...</option>
                                        {% for file in csv_files %}
                                        <option value="{{ file }}">{{ file }}</option>
                                        {% endfor %}
                                    </select>
                                    <div class="mt-2">
                                        <button type="button" class="btn btn-outline-secondary btn-sm" id="getColumnsBtn">Get Columns</button>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Sample Columns</label>
                                    <div class="sample-columns mt-2" style="max-height: 150px; overflow-y: auto;">
                                        {% for column in sample_columns %}
                                        <span class="badge bg-light text-dark me-1 mb-1 column-badge" 
                                              style="cursor: pointer;" onclick="addColumn('{{ column }}')">{{ column }}</span>
                                        {% endfor %}
                                    </div>
                                </div>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <label for="startDate" class="form-label">Start Date</label>
                                        <input type="date" class="form-control" id="startDate" name="start_date">
                                    </div>
                                    <div class="col-md-6">
                                        <label for="endDate" class="form-label">End Date</label>
                                        <input type="date" class="form-control" id="endDate" name="end_date">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="d-grid">
                    <button type="submit" class="btn btn-primary">
                        Search
                        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" id="searchSpinner"></span>
                    </button>
                </div>
            </form>
        </div>
        
        <div class="results-container mt-4">
            <div class="d-flex justify-content-between mb-3" id="resultsHeader" style="display: none !important;">
                <h3 id="resultsCount">0 results found</h3>
                <div>
                    <div class="btn-group">
                        <button type="button" class="btn btn-success" id="exportCSV">Export CSV</button>
                        <button type="button" class="btn btn-info" id="exportJSON">Export JSON</button>
                    </div>
                </div>
            </div>
            
            <div id="searchResults"></div>
            <div id="errorMessage" class="alert alert-danger" style="display: none;"></div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const searchForm = document.getElementById('searchForm');
            const resultsHeader = document.getElementById('resultsHeader');
            const resultsCountElem = document.getElementById('resultsCount');
            const searchResults = document.getElementById('searchResults');
            const errorMessage = document.getElementById('errorMessage');
            const exportCSV = document.getElementById('exportCSV');
            const exportJSON = document.getElementById('exportJSON');
            const getColumnsBtn = document.getElementById('getColumnsBtn');
            const fileSelector = document.getElementById('fileSelector');
            const columnsInput = document.getElementById('columns');
            const searchSpinner = document.getElementById('searchSpinner');
            
            let currentResults = [];
            
            // Search form submission
            searchForm.addEventListener('submit', function(e) {
                e.preventDefault();
                performSearch();
            });
            
            // Perform the search
            function performSearch() {
                const formData = new FormData(searchForm);
                
                // Show spinner
                searchSpinner.style.display = 'inline-block';
                
                // Clear any previous results
                searchResults.innerHTML = '';
                errorMessage.style.display = 'none';
                resultsHeader.style.display = 'none';
                
                fetch('/search', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    // Hide spinner
                    searchSpinner.style.display = 'none';
                    
                    if (data.success) {
                        currentResults = data.results;
                        displayResults(data);
                    } else {
                        displayError(data.error);
                    }
                })
                .catch(error => {
                    // Hide spinner
                    searchSpinner.style.display = 'none';
                    displayError('Error performing search: ' + error.message);
                });
            }
            
            // Display search results
            function displayResults(data) {
                if (data.results_count === 0) {
                    searchResults.innerHTML = '<div class="alert alert-warning">No results found</div>';
                    return;
                }
                
                // Update results count
                resultsCountElem.textContent = `${data.results_count} results found for "${data.query}"`;
                resultsHeader.style.display = 'flex';
                
                // Display each result
                data.results.forEach((result, index) => {
                    const resultCard = document.createElement('div');
                    resultCard.className = 'result-card';
                    
                    // Header with source file and match info
                    let headerHTML = `<div class="d-flex justify-content-between align-items-top mb-2">
                                        <h5 class="mb-0">Result ${index + 1} of ${data.results_count}</h5>
                                        <span class="source-file">Source: ${result.source_file}</span>
                                      </div>`;
                    
                    // Match information if available
                    if (result.match_score) {
                        headerHTML += `<div class="mb-2"><span class="badge bg-info">Match Score: ${result.match_score}%</span></div>`;
                    }
                    
                    if (result.matching_value) {
                        headerHTML += `<div class="mb-3"><span class="match-highlight">${result.matching_value}</span></div>`;
                    }
                    
                    // Fields
                    let fieldsHTML = '<div class="row">';
                    
                    Object.entries(result.fields).forEach(([field, value]) => {
                        fieldsHTML += `
                            <div class="col-md-6 result-field">
                                <span class="field-name">${field}:</span> 
                                <span class="field-value">${value}</span>
                            </div>
                        `;
                    });
                    
                    fieldsHTML += '</div>';
                    
                    resultCard.innerHTML = headerHTML + fieldsHTML;
                    searchResults.appendChild(resultCard);
                });
            }
            
            // Display error message
            function displayError(message) {
                errorMessage.textContent = message;
                errorMessage.style.display = 'block';
            }
            
            // Export functions
            exportCSV.addEventListener('click', function() {
                exportResults('csv');
            });
            
            exportJSON.addEventListener('click', function() {
                exportResults('json');
            });
            
            function exportResults(format) {
                if (currentResults.length === 0) {
                    alert('No results to export');
                    return;
                }
                
                const formData = new FormData();
                formData.append('format', format);
                formData.append('results', JSON.stringify(currentResults));
                
                // Create a form to submit the download
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = '/export';
                
                // Add form data as hidden inputs
                for (const [key, value] of formData.entries()) {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = key;
                    input.value = value;
                    form.appendChild(input);
                }
                
                // Submit the form
                document.body.appendChild(form);
                form.submit();
                document.body.removeChild(form);
            }
            
            // Get columns from file
            getColumnsBtn.addEventListener('click', function() {
                const selectedFile = fileSelector.value;
                if (!selectedFile) {
                    alert('Please select a file');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file_name', selectedFile);
                
                fetch('/get_columns', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update the columns dropdown
                        updateColumnBadges(data.columns);
                    } else {
                        alert('Error getting columns: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Error: ' + error.message);
                });
            });
            
            // Update column badges
            function updateColumnBadges(columns) {
                const sampleColumns = document.querySelector('.sample-columns');
                sampleColumns.innerHTML = '';
                
                columns.forEach(column => {
                    const badge = document.createElement('span');
                    badge.className = 'badge bg-light text-dark me-1 mb-1 column-badge';
                    badge.style.cursor = 'pointer';
                    badge.textContent = column;
                    badge.onclick = function() { addColumn(column); };
                    
                    sampleColumns.appendChild(badge);
                });
            }
            
            // Add column to input
            window.addColumn = function(column) {
                const currentColumns = columnsInput.value.split(',').map(c => c.trim()).filter(c => c);
                
                if (!currentColumns.includes(column)) {
                    if (currentColumns.length > 0) {
                        columnsInput.value = currentColumns.join(', ') + ', ' + column;
                    } else {
                        columnsInput.value = column;
                    }
                }
            };
        });
    </script>
</body>
</html>''')
        print(f"{Fore.GREEN}Template file created successfully{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}Template file already exists{Style.RESET_ALL}")
    
    return template_path

if __name__ == '__main__':
    # Initialize colorama for terminal colors
    init()
    
    # Ensure template exists
    ensure_template_exists()
    
    print(f"{Fore.GREEN}Starting Deep Search Web Interface...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Access the web interface at: http://localhost:4000{Style.RESET_ALL}")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=4000)
    except OSError as e:
        print(f"{Fore.RED}Error starting server: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Try a different port. Port 4000 is in use.{Style.RESET_ALL}") 

# Add this if-name-main block for proper deployment on Render
if __name__ == "__main__":
    # Get port from environment variable (for Render deployment)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)