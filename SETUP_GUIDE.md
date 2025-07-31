# 🚀 Subtitle Generator - Complete Setup Guide

## Prerequisites

1. **Python 3.8+** installed on your system
2. **Node.js 16+** and npm installed
3. **FFmpeg** installed and available in PATH (for video processing)

## Quick Start (Automated)

### Option 1: Use the Startup Script (Windows)
```bash
# Double-click start.bat or run in command prompt
start.bat
```
This will automatically:
- Install Python dependencies
- Install Node.js dependencies  
- Start the Python backend server
- Start the React frontend server

### Option 2: Manual Setup

#### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Step 2: Install Node.js Dependencies
```bash
npm install
```

#### Step 3: Start the Backend Server
```bash
python server.py
```
The backend will start at `http://localhost:5000`

#### Step 4: Start the Frontend (in a new terminal)
```bash
npm start
```
The frontend will start at `http://localhost:3000`

## 🔧 System Requirements

### Required Dependencies
- **Flask**: Web server framework
- **Flask-CORS**: Cross-origin resource sharing
- **OpenAI Whisper**: AI transcription model
- **MoviePy**: Video processing
- **React**: Frontend framework
- **Axios**: HTTP client

### Optional but Recommended
- **FFmpeg**: For better video/audio processing
- **CUDA**: For GPU acceleration (if available)

## 🎯 Usage Instructions

1. **Upload Video**: 
   - Open `http://localhost:3000` in your browser
   - Drag and drop a video file (MP4, MOV, AVI, MKV, WebM)
   - Maximum file size: 500MB

2. **Configure Settings**:
   - Select language (Auto-detect, English, Hindi, Hinglish)
   - Choose AI model (Tiny to Large)
   - Customize font settings

3. **Process Video**:
   - Click "Generate Subtitles"
   - Monitor real-time progress
   - Wait for processing to complete

4. **Edit Subtitles**:
   - Review generated subtitles
   - Edit text directly in the timeline
   - Preview with video playback

5. **Export**:
   - Download SRT file
   - Get video with burned-in subtitles

## 🔍 Troubleshooting

### Backend Issues

**Error: "Whisper not available"**
```bash
pip install openai-whisper torch torchaudio
```

**Error: "FFmpeg not found"**
- Download FFmpeg from https://ffmpeg.org/
- Add to system PATH
- Restart terminal

**Error: "Port 5000 already in use"**
- Change port in `server.py`: `app.run(port=5001)`
- Update frontend API URL in `src/services/subtitleService.js`

### Frontend Issues

**Error: "Cannot connect to server"**
- Ensure backend is running on `http://localhost:5000`
- Check CORS settings in `server.py`

**Error: "Module not found"**
```bash
npm install
```

**Error: "Port 3000 already in use"**
- React will automatically suggest port 3001
- Or set PORT=3001 environment variable

## 📁 Project Structure

```
subtitle-generator/
├── script.py              # Original Python subtitle generation
├── server.py              # Flask backend server
├── requirements.txt       # Python dependencies
├── package.json           # Node.js dependencies
├── start.bat              # Windows startup script
├── src/                   # React frontend source
│   ├── components/        # UI components
│   ├── context/           # State management
│   ├── services/          # API communication
│   └── App.js            # Main application
├── public/                # Static files
├── uploads/              # Uploaded video files
└── outputs/              # Generated subtitle files
```

## 🎨 Features

### Backend Features
- **Multi-format Support**: MP4, MOV, AVI, MKV, WebM
- **Language Detection**: Auto-detect or manual selection
- **Model Selection**: From Tiny (fast) to Large (accurate)
- **Font Customization**: Family, size, colors, styles
- **Progress Tracking**: Real-time processing updates
- **Error Handling**: Comprehensive error messages

### Frontend Features
- **Drag & Drop Upload**: Intuitive file upload
- **Real-time Progress**: Live processing updates
- **Font Preview**: Live preview of subtitle styling
- **Video Timeline**: Interactive subtitle editing
- **Export Options**: SRT download and video with subtitles

## 🔧 Configuration

### Backend Configuration (server.py)
```python
# Change server settings
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # File size limit
UPLOAD_FOLDER = 'uploads'    # Upload directory
OUTPUT_FOLDER = 'outputs'    # Output directory
```

### Frontend Configuration (src/services/subtitleService.js)
```javascript
// Change API endpoint
const API_BASE_URL = 'http://localhost:5000/api';
```

## 🚀 Production Deployment

### Backend Deployment
- Use a production WSGI server (Gunicorn, uWSGI)
- Set up reverse proxy (Nginx)
- Configure HTTPS
- Set environment variables

### Frontend Deployment
- Build optimized bundle: `npm run build`
- Serve static files
- Update API URLs for production

## 💡 Tips for Better Performance

1. **Use GPU acceleration** if available for Whisper
2. **Choose appropriate model size** based on speed vs accuracy needs
3. **Optimize video file size** before upload
4. **Use SSD storage** for faster file I/O
5. **Increase RAM** for processing large files

## 🆘 Support

If you encounter issues:

1. **Check Dependencies**: Ensure all required packages are installed
2. **Check Logs**: Look at console output for error messages  
3. **Verify Files**: Ensure video files are not corrupted
4. **Test Connection**: Verify frontend can reach backend
5. **Check Ports**: Ensure ports 3000 and 5000 are available

## 🎉 Success!

If everything is working correctly, you should see:
- ✅ Backend server running at http://localhost:5000
- ✅ Frontend application at http://localhost:3000
- ✅ File upload working
- ✅ Video processing with progress updates
- ✅ Subtitle generation and editing

Happy subtitle generation! 🎬✨
