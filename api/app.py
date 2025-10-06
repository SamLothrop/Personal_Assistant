import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, render_template_string
from src.document_loader import collection

app = Flask(__name__)

# Simple HTML page
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ChromaDB Interface</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
        }
        h1 { color: #667eea; }
        .stats {
            background: #f0f0f0;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>🚀 ChromaDB is Running!</h1>
    <div class="stats">
        <h2>Database Stats:</h2>
        <p><strong>Total Segments:</strong> {{ stats.total }}</p>
        <p><strong>Collection Name:</strong> {{ stats.name }}</p>
    </div>
    <p>✅ Your Flask server is working!</p>
    <p>🎨 Now you can customize this page however you want.</p>
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
    """API endpoint for searching - you can use this for your custom frontend"""
    from flask import request
    
    data = request.json
    query_text = data.get('query', '')
    n_results = data.get('n_results', 5)
    
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    formatted_results = []
    for doc, metadata, distance in zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    ):
        formatted_results.append({
            'content': doc,
            'filename': metadata.get('filename'),
            'segment_number': metadata.get('segment_number'),
            'relevance': round((1 - distance) * 100, 2)
        })
    
    return jsonify({'results': formatted_results})

if __name__ == '__main__':
    print("Flask server starting...")
    print(f"Collection has {collection.count()} segments")
    print("Visit: http://localhost:5000")
    app.run(debug=True, port=5000)