import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, render_template_string, request
from src.search import query_collection  # Import your existing function
from src.document_loader import collection

app = Flask(__name__)

# Enhanced HTML page with search functionality
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ChromaDB Search Interface</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 { color: #667eea; }
        .stats {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .search-section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        button {
            padding: 12px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }
        button:hover {
            background: #5568d3;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .controls {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .control-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        select {
            padding: 8px;
            border: 2px solid #ddd;
            border-radius: 5px;
        }
        .results {
            margin-top: 30px;
        }
        .result-card {
            background: #f9f9f9;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .result-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .result-title {
            font-weight: bold;
            color: #667eea;
        }
        .result-relevance {
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
        }
        .result-content {
            color: #333;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .result-meta {
            margin-top: 10px;
            font-size: 12px;
            color: #666;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        .error {
            background: #ff4444;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .no-results {
            text-align: center;
            padding: 40px;
            color: #666;
        }
    </style>
</head>
<body>
    <h1>🔍 ChromaDB Search Interface</h1>
    
    <div class="stats">
        <h2>Database Stats:</h2>
        <p><strong>Total Segments:</strong> {{ stats.total }}</p>
        <p><strong>Collection Name:</strong> {{ stats.name }}</p>
    </div>
    
    <div class="search-section">
        <h2>Search Your Documents</h2>
        
        <div class="search-box">
            <input 
                type="text" 
                id="searchInput" 
                placeholder="Enter your search query..."
                onkeypress="handleKeyPress(event)"
            />
            <button onclick="performSearch()" id="searchBtn">Search</button>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label><strong>Number of Results:</strong></label>
                <select id="numResults">
                    <option value="3" selected>3</option>
                    <option value="5">5</option>
                    <option value="10">10</option>
                    <option value="20">20</option>
                </select>
            </div>
            
            <div class="control-group">
                <label><strong>Content Type:</strong></label>
                <select id="contentType">
                    <option value="">All (No Filter)</option>
                    <option value="document">Document</option>
                    <option value="code">Code</option>
                    <option value="text">Text</option>
                </select>
            </div>
        </div>
        
        <div id="resultsSection"></div>
    </div>
    
    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                performSearch();
            }
        }
        
        async function performSearch() {
            const query = document.getElementById('searchInput').value.trim();
            const nResults = parseInt(document.getElementById('numResults').value);
            const contentType = document.getElementById('contentType').value;
            const resultsSection = document.getElementById('resultsSection');
            const searchBtn = document.getElementById('searchBtn');
            
            if (!query) {
                alert('Please enter a search query');
                return;
            }
            
            // Show loading
            searchBtn.disabled = true;
            searchBtn.textContent = 'Searching...';
            resultsSection.innerHTML = '<div class="loading">Searching...</div>';
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: query,
                        n_results: nResults,
                        content_type: contentType || null
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    resultsSection.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    return;
                }
                
                if (data.results.length === 0) {
                    resultsSection.innerHTML = '<div class="no-results">No results found. Try a different query.</div>';
                    return;
                }
                
                // Display results
                let html = `<div class="results"><h3>Found ${data.count} Results:</h3>`;
                data.results.forEach((result, index) => {
                    html += `
                        <div class="result-card">
                            <div class="result-header">
                                <div class="result-title">
                                    ${result.filename || 'Unknown File'} 
                                    ${result.segment_number ? `(Segment ${result.segment_number})` : ''}
                                </div>
                                <div class="result-relevance">
                                    ${result.relevance}% Match
                                </div>
                            </div>
                            <div class="result-content">
                                ${result.content}
                            </div>
                            ${result.uri ? `<div class="result-meta">📎 URI: ${result.uri}</div>` : ''}
                        </div>
                    `;
                });
                html += '</div>';
                
                resultsSection.innerHTML = html;
                
            } catch (error) {
                resultsSection.innerHTML = `<div class="error">Error: ${error.message}</div>`;
            } finally {
                searchBtn.disabled = false;
                searchBtn.textContent = 'Search';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    stats = {
        'total': collection.count(),
        'name': collection.name
    }
    return render_template_string(HTML, stats=stats)

@app.route('/api/search', methods=['POST'])
def search():
    """API endpoint for searching using your existing query_collection function"""
    try:
        data = request.json
        query_text = data.get('query', '')
        n_results = data.get('n_results', 3)
        content_type = data.get('content_type', None)
        
        if not query_text:
            return jsonify({'error': 'No query provided'}), 400
        
        # Use your existing query_collection function
        results = query_collection(query_text, n_results, content_type)
        
        # results is a dict with keys: 'documents', 'metadatas', 'distances', 'uris'
        # Each value is a list of lists (batch results)
        formatted_results = []
        
        documents = results.get('documents', [[]])[0]  # Get first batch
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        uris = results.get('uris', [[]])[0] if results.get('uris') else [None] * len(documents)
        
        for doc, metadata, distance, uri in zip(documents, metadatas, distances, uris):
            formatted_results.append({
                'content': doc,
                'filename': metadata.get('filename', 'Unknown'),
                'segment_number': metadata.get('segment_number', 'N/A'),
                'content_type': metadata.get('content_type', 'Unknown'),
                'relevance': round((1 - distance) * 100, 2) if distance is not None else 0,
                'uri': uri
            })
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'count': len(formatted_results)
        })
    
    except Exception as e:
        print(f"Error in search: {e}")  # For debugging
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Flask server starting...")
    print(f"Collection has {collection.count()} segments")
    print("Visit: http://localhost:5000")
    app.run(debug=True, port=5000)