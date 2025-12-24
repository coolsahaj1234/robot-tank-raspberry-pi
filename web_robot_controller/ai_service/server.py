#!/usr/bin/env python3
"""
AI Service Server - Reactive Navigation
Flask server that processes video frames and provides AI navigation commands.
Uses reactive obstacle avoidance - robot never stops, always moves.
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
    return jsonify({
        'status': 'ok',
        'service': 'ai_processor',
        'navigation_state': processor.navigation_state
    })


@app.route('/status', methods=['GET'])
def status():
    """Get detailed AI processor status"""
    try:
        return jsonify({
            'status': 'ok',
            **processor.get_status()
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/reset', methods=['POST'])
def reset():
    """Reset AI processor state"""
    try:
        processor.reset()
        return jsonify({'status': 'success', 'message': 'AI processor reset'})
    except Exception as e:
        logger.error(f"Error resetting processor: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/process_frame', methods=['POST'])
def process_frame():
    """
    Process a video frame and return AI analysis with sensor fusion.
    Returns navigation commands that NEVER stop the robot.
    """
    try:
        data = request.json
        base64_frame = data.get('frame')
        ultrasonic_distance = data.get('ultrasonic_distance')

        if not base64_frame:
            return jsonify({'error': 'No frame provided'}), 400

        # Process frame with reactive navigation
        result = processor.process_frame(base64_frame, ultrasonic_distance)

        if result is None:
            return jsonify({'error': 'Failed to process frame'}), 500

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("  AI Video Processing Service - Reactive Navigation")
    print("=" * 50)
    print("  Listening on http://localhost:5001")
    print("  Endpoints:")
    print("    GET  /health       - Health check")
    print("    GET  /status       - Detailed status")
    print("    POST /reset        - Reset AI state")
    print("    POST /process_frame - Process video frame")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=False)
