#!/usr/bin/env python3
"""
AI Service Server
Flask server that processes video frames and provides AI navigation commands
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from ai_processor import processor
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'ai_processor'})


@app.route('/process_frame', methods=['POST'])
def process_frame():
    """Process a video frame and return AI analysis"""
    try:
        data = request.json
        base64_frame = data.get('frame')
        
        if not base64_frame:
            return jsonify({'error': 'No frame provided'}), 400
        
        # Process frame
        result = processor.process_frame(base64_frame)
        
        if result is None:
            return jsonify({'error': 'Failed to process frame'}), 500
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🤖 AI Video Processing Service starting...")
    print("📡 Listening on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)

