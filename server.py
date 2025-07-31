#!/usr/bin/env python3
"""
Flask Backend Server for Subtitle Generator
Integrates with the existing script.py for video processing
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
import time
import uuid
import logging

# Import our existing subtitle generation functions
from script import (
    process_video_with_captions,
    FontSettings,
    check_dependencies,
    LocalWhisperTools,
    VideoProcessor
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Store for tracking processing jobs
processing_jobs = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class ProgressTracker:
    """Class to track and broadcast processing progress"""
    def __init__(self, job_id):
        self.job_id = job_id
        self.progress = 0
        self.current_step = ''
        self.message = ''
        self.completed = False
        self.error = None
        
    def update(self, step, message, progress=None):
        """Update progress and store in global jobs dict"""
        self.current_step = step
        self.message = message
        if progress is not None:
            self.progress = progress
            
        # Ensure job exists in dictionary before updating
        if self.job_id not in processing_jobs:
            processing_jobs[self.job_id] = {}
            
        processing_jobs[self.job_id].update({
            'progress': self.progress,
            'current_step': self.current_step,
            'message': self.message,
            'completed': self.completed,
            'error': self.error
        })
        
        logger.info(f"Job {self.job_id}: {step} - {message} ({self.progress}%)")
        logger.debug(f"Updated job {self.job_id} state: {processing_jobs[self.job_id]}")

def process_video_background(job_id, video_path, output_dir, model_name, language, create_video, font_settings):
    """Background task to process video"""
    tracker = ProgressTracker(job_id)
    
    try:
        tracker.update("Initializing", "Starting video processing", 0)
        
        # Create progress callback
        def progress_callback(message):
            # Parse progress from message if possible
            progress = None
            step = "Processing"
            
            if "🎵" in message:
                step = "Extracting Audio"
                progress = 25
            elif "🔍" in message or "🌐" in message:
                step = "Language Detection"
                progress = 35
            elif "🎤" in message:
                if "Starting transcription" in message:
                    step = "Transcribing Audio"
                    progress = 45
                elif "completed" in message:
                    step = "Transcription Complete"
                    progress = 75
            elif "🔥" in message:
                step = "Burning Subtitles"
                progress = 85
            elif "✅" in message:
                step = "Complete"
                progress = 100
            
            tracker.update(step, message, progress)
        
        # Process the video using our existing function
        srt_path, video_with_subs_path, message = process_video_with_captions(
            video_path=video_path,
            output_dir=output_dir,
            model_name=model_name,
            font_settings=font_settings,
            create_video=create_video,
            progress_callback=progress_callback,
            language=language if language != 'auto' else None,
            auto_detect_language=language == 'auto'
        )
        
        if srt_path:
            # Read the SRT content
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            # Mark as completed
            tracker.completed = True
            tracker.progress = 100
            processing_jobs[job_id].update({
                'completed': True,
                'srt_content': srt_content,
                'srt_path': srt_path,
                'video_with_subs_path': video_with_subs_path,
                'output_dir': output_dir,
                'message': message
            })
            
            tracker.update("Completed", "Video processing completed successfully!", 100)
        else:
            raise Exception(message or "Processing failed")
            
    except Exception as e:
        logger.error(f"Processing error for job {job_id}: {str(e)}")
        tracker.error = str(e)
        processing_jobs[job_id].update({
            'error': str(e),
            'completed': True
        })
        tracker.update("Error", f"Processing failed: {str(e)}", None)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'dependencies': check_dependencies()
    })

@app.route('/api/process-video', methods=['POST'])
def process_video():
    """Main endpoint for video processing"""
    try:
        # Check if file is present
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Supported formats: MP4, MOV, AVI, MKV, WebM'}), 400
        
        # Get parameters
        language = request.form.get('language', 'auto')
        model_name = request.form.get('model', 'base')
        create_video = request.form.get('create_video', 'true').lower() == 'true'
        
        # Font settings (can be extended from form data)
        font_settings = FontSettings(
            family=request.form.get('font_family', 'Arial'),
            size=int(request.form.get('font_size', 24)),
            color=request.form.get('font_color', 'white'),
            outline_color=request.form.get('outline_color', 'black'),
            bold=request.form.get('bold', 'false').lower() == 'true',
            italic=request.form.get('italic', 'false').lower() == 'true',
            shadow=request.form.get('shadow', 'true').lower() == 'true'
        )
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        unique_filename = f"{timestamp}_{filename}"
        video_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(video_path)
        
        # Create output directory for this job
        output_dir = os.path.join(OUTPUT_FOLDER, job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize job tracking
        processing_jobs[job_id] = {
            'progress': 0,
            'current_step': 'Initializing',
            'message': 'Starting video processing',
            'completed': False,
            'error': None
        }
        
        logger.info(f"Created job {job_id} for video: {filename}")
        logger.info(f"Current jobs in memory: {list(processing_jobs.keys())}")
        
        # Start background processing
        thread = threading.Thread(
            target=process_video_background,
            args=(job_id, video_path, output_dir, model_name, language, create_video, font_settings)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'started',
            'message': 'Video processing started'
        })
        
    except Exception as e:
        logger.error(f"Error in process_video: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get processing status for a job"""
    logger.info(f"Status request for job: {job_id}")
    logger.info(f"Available jobs: {list(processing_jobs.keys())}")
    
    if job_id not in processing_jobs:
        logger.error(f"Job {job_id} not found in processing_jobs")
        return jsonify({'error': 'Job not found'}), 404
    
    job_data = processing_jobs[job_id]
    logger.info(f"Job {job_id} data: {job_data}")
    
    if job_data['completed'] and not job_data.get('error'):
        # Include SRT content in response when completed
        response_data = {
            'type': 'complete',
            'srtContent': job_data.get('srt_content', ''),
            'srtPath': job_data.get('srt_path'),
            'outputDir': job_data.get('output_dir'),
            'message': job_data.get('message', 'Processing completed'),
            'videoCreated': job_data.get('video_with_subs_path') is not None,
            'videoWithSubtitles': job_data.get('video_with_subs_path')
        }
    else:
        response_data = {
            'type': 'progress' if not job_data.get('error') else 'error',
            'progress': job_data['progress'],
            'current_step': job_data['current_step'],
            'message': job_data['message'],
            'completed': job_data['completed'],
            'error': job_data.get('error')
        }
    
    logger.info(f"Returning response for job {job_id}: {response_data}")
    return jsonify(response_data)

@app.route('/api/download-srt/<job_id>', methods=['GET'])
def download_srt(job_id):
    """Download SRT file for a completed job"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job_data = processing_jobs[job_id]
    if not job_data.get('completed') or job_data.get('error'):
        return jsonify({'error': 'Job not completed or has error'}), 400
    
    srt_path = job_data.get('srt_path')
    if not srt_path or not os.path.exists(srt_path):
        return jsonify({'error': 'SRT file not found'}), 404
    
    return send_file(srt_path, as_attachment=True, download_name='subtitles.srt')

@app.route('/api/download-video/<job_id>', methods=['GET'])
def download_video(job_id):
    """Download video with subtitles for a completed job"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job_data = processing_jobs[job_id]
    if not job_data.get('completed') or job_data.get('error'):
        return jsonify({'error': 'Job not completed or has error'}), 400
    
    video_path = job_data.get('video_with_subs_path')
    if not video_path or not os.path.exists(video_path):
        return jsonify({'error': 'Video file not found'}), 404
    
    return send_file(video_path, as_attachment=True, download_name='video_with_subtitles.mp4')

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 500MB.'}), 413

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 Starting Subtitle Generator Backend Server...")
    print("📊 Checking dependencies...")
    
    deps = check_dependencies()
    print(f"Whisper: {'Available' if deps['whisper'] else 'Missing'}")
    print(f"FFmpeg: {'Available' if deps['ffmpeg'] else 'Missing'}")
    print(f"MoviePy: {'Available' if deps['moviepy'] else 'Missing'}")
    
    if not deps['whisper']:
        print("❌ Warning: Whisper not available. Install with: pip install openai-whisper")
    
    print("\n🌐 Server will be available at: http://localhost:5000")
    print("🔗 Frontend should connect to: http://localhost:5000/api/process-video")
    print("\n📁 Upload folder: ./uploads")
    print("📁 Output folder: ./outputs")
    
    app.run(debug=False, host='0.0.0.0', port=5000)
