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
<<<<<<< HEAD
=======
import cv2
import os
import time
>>>>>>> 40885bf (Initial commit)

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
<<<<<<< HEAD
=======
        ultrasonic_distance_back = data.get('ultrasonic_distance_back')
        santa_mode = data.get('santa_mode', False)
        santa_standby = data.get('santa_standby', False)
        auto_park_mode = data.get('auto_park_mode', False)
        imu_data = data.get('imu_data')  # Get IMU data from client
>>>>>>> 40885bf (Initial commit)

        if not base64_frame:
            return jsonify({'error': 'No frame provided'}), 400

<<<<<<< HEAD
        # Process frame with reactive navigation
        result = processor.process_frame(base64_frame, ultrasonic_distance)
=======
        # Update processor mode
        processor.santa_mode_active = santa_mode
        processor.santa_standby = santa_standby
        processor.auto_park_mode = auto_park_mode

        # Process frame with reactive navigation + IMU data
        result = processor.process_frame(
            base64_frame, 
            ultrasonic_distance, 
            ultrasonic_distance_back,
            imu_data=imu_data
        )
>>>>>>> 40885bf (Initial commit)

        if result is None:
            return jsonify({'error': 'Failed to process frame'}), 500

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        return jsonify({'error': str(e)}), 500


<<<<<<< HEAD
=======
@app.route('/capture_photo', methods=['POST'])
def capture_photo():
    """
    Manually capture and save a photo from the current frame.
    Saves to captures/manual directory.
    """
    try:
        data = request.json
        base64_frame = data.get('frame')
        
        if not base64_frame:
            return jsonify({'error': 'No frame provided'}), 400
        
        # Convert base64 to image
        image = processor.base64_to_image(base64_frame)
        if image is None:
            return jsonify({'error': 'Failed to decode image'}), 400
        
        # Create manual captures directory
        manual_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'captures', 'manual')
        if not os.path.exists(manual_dir):
            os.makedirs(manual_dir)
        
        # Save with timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"manual_{timestamp}.jpg"
        filepath = os.path.join(manual_dir, filename)
        
        cv2.imwrite(filepath, image)
        logger.info(f"📸 Manual photo saved: {filepath}")
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'path': filepath
        })
        
    except Exception as e:
        logger.error(f"Error capturing photo: {e}")
        return jsonify({'error': str(e)}), 500


>>>>>>> 40885bf (Initial commit)
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
<<<<<<< HEAD
=======
    print("    POST /capture_photo - Manually capture photo")
>>>>>>> 40885bf (Initial commit)
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=False)
