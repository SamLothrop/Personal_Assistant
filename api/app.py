import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, render_template_string, request
from src.document_loader import collection

app = Flask(__name__)

# Define query_collection here to avoid circular import
def query_collection(query_text, n_results=3, content_type=None):
    where_clause = None
    if content_type:
        where_clause = {"content_type": content_type}
    
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances', 'uris'],
        where=where_clause
    )
    return results

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
        .result-card.image-result {
            border-left-color: #f093fb;
        }
        .result-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            align-items: center;
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
            padding-top: 10px;
            border-top: 1px solid #ddd;
            font-size: 13px;
            color: #666;
        }
        .result-meta span {
            margin-right: 15px;
        }
        .result-image {
            max-width: 100%;
            max-height: 300px;
            margin-top: 10px;
            border-radius: 5px;
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
    <h1>ChromaDB Search Interface</h1>
    
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
                    <option value="">All</option>
                    <option value="text">Text</option>
                    <option value="image">Images</option>
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
                    const isImage = result.content_type === 'image';
                    const cardClass = isImage ? 'result-card image-result' : 'result-card';
                    
                    html += `<div class="${cardClass}">`;
                    html += `<div class="result-header">`;
                    html += `<div class="result-title">`;
                    html += isImage ? '🖼️ ' : '📄 ';
                    html += `${result.file_name}`;
                    if (result.segment_number) {
                        html += ` (Segment ${result.segment_number}/${result.total_segments})`;
                    }
                    html += `</div>`;
                    html += `<div class="result-relevance">${result.relevance}% Match</div>`;
                    html += `</div>`;
                    
                    if (isImage && result.uri) {
                        html += `<img src="file://${result.uri}" class="result-image" alt="${result.file_name}" onerror="this.style.display='none'">`;
                        html += `<div class="result-content">Image file: ${result.file_name}</div>`;
                    } else if (result.content) {
                        html += `<div class="result-content">${result.content}</div>`;
                    }
                    
                    html += `<div class="result-meta">`;
                    html += `<span><strong>Type:</strong> ${result.file_type}</span>`;
                    html += `<span><strong>Content:</strong> ${result.content_type}</span>`;
                    if (result.uri) {
                        html += `<span><strong>Path:</strong> ${result.uri}</span>`;
                    }
                    html += `</div>`;
                    html += `</div>`;
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
    """API endpoint for searching using query_collection"""
    try:
        data = request.json
        query_text = data.get('query', '')
        n_results = data.get('n_results', 3)
        content_type = data.get('content_type', None)
        
        if not query_text:
            return jsonify({'error': 'No query provided'}), 400
        
        # Use the query_collection function
        results = query_collection(query_text, n_results, content_type)
        
        # Parse results - matching your metadata structure
        formatted_results = []
        
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        uris = results.get('uris', [[]])[0] if results.get('uris') else [None] * len(documents)
        
        for doc, metadata, distance, uri in zip(documents, metadatas, distances, uris):
            formatted_results.append({
                'content': doc if doc else '',
                'file_name': metadata.get('file_name', 'Unknown'),  # Changed from 'filename'
                'segment_number': metadata.get('segment_number'),
                'total_segments': metadata.get('total_segments'),
                'file_type': metadata.get('file_type', 'unknown'),
                'content_type': metadata.get('content_type', 'unknown'),
                'relevance': round((1 - distance) * 100, 2) if distance is not None else 0,
                'uri': uri,
                'full_path': metadata.get('full_path')  # For images
            })
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'count': len(formatted_results)
        })
    
    except Exception as e:
        print(f"Error in search: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get detailed statistics about the collection"""
    try:
        all_data = collection.get()
        
        # Count by content type
        content_types = {}
        file_types = {}
        
        for meta in all_data['metadatas']:
            content_type = meta.get('content_type', 'unknown')
            file_type = meta.get('file_type', 'unknown')
            
            content_types[content_type] = content_types.get(content_type, 0) + 1
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        # Count unique files
        unique_files = set(meta.get('file_name', 'unknown') for meta in all_data['metadatas'])
        
        return jsonify({
            'total_segments': collection.count(),
            'unique_files': len(unique_files),
            'content_types': content_types,
            'file_types': file_types
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Flask server starting...")
    print(f"Collection has {collection.count()} segments")
    print("Visit: http://localhost:5000")
    app.run(debug=True, port=5000)