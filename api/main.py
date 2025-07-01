from flask import Flask, request, jsonify, send_file
from datetime import datetime
import asyncio
import uuid
import os
from pathlib import Path
from .research import ResearchEngine
from .utils import validate_request

app = Flask(__name__)
engine = ResearchEngine()

@app.route('/api/research', methods=['POST'])
async def start_research():
    data = request.json
    errors = validate_request(data)
    if errors:
        return jsonify({"errors": errors}), 400
    
    try:
        result = await engine.process_request(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    filepath = os.path.join('storage/reports', filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)