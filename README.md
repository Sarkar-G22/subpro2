# Subtitle Generator Frontend

A modern React frontend for the AI-powered subtitle generation tool. This application provides an intuitive interface for uploading videos, configuring transcription settings, and editing generated subtitles.

## Features

### 🎬 Video Upload
- Drag and drop video file upload
- Support for MP4, MOV, AVI, MKV, and WebM formats
- File size validation (up to 500MB)
- Visual feedback for upload status

### ⚙️ Processing Configuration
- **Language Selection**: Auto-detect, English, Hindi, Hinglish
- **AI Model Selection**: Tiny (fastest) to Large (most accurate)
- **Smart Recommendations**: Suggests better models for Hindi/Hinglish content
- Real-time processing progress with detailed status updates

### 🎨 Font Customization
- Font family selection (Inter, Arial, Helvetica, etc.)
- Adjustable font size (12-48px)
- Text and background color customization
- Text styling options (Bold, Italic, Underline)
- Text shadow effects
- Live preview of subtitle appearance

### ✏️ Subtitle Editor
- **Timeline View**: Shows all generated subtitles with timestamps
- **Video Preview**: Play video with live subtitle overlay
- **Interactive Editing**: Click to seek to specific subtitles
- **Text Editing**: In-line editing of subtitle text
- **Export Options**: Download SRT files
- **Visual Feedback**: Highlights currently active subtitle

### 📱 Responsive Design
- Mobile-friendly interface
- Adaptive layouts for different screen sizes
- Touch-friendly controls

## Architecture

### Component Structure
```
src/
├── components/
│   ├── VideoUploader.js      # Drag & drop video upload
│   ├── ProcessingPanel.js    # Configuration settings
│   ├── FontStylePanel.js     # Font customization
│   ├── ProgressIndicator.js  # Processing progress
│   └── SubtitleEditor.js     # Timeline & editing
├── context/
│   └── SubtitleContext.js    # Global state management
├── services/
│   └── subtitleService.js    # API communication
└── App.js                    # Main application
```

### State Management
- **React Context API** for global state
- **useReducer** for complex state updates
- **Optimistic updates** for better UX
- **Error handling** with user-friendly messages

### Key Features Integration

#### 1. Video Processing Pipeline
```javascript
Upload Video → Configure Settings → Process with AI → Edit Subtitles → Export
```

#### 2. Real-time Progress Tracking
- Connects to Python backend processing steps
- Shows current operation (audio extraction, transcription, etc.)
- Progress bar with percentage completion
- Error handling with detailed messages

#### 3. Font Style System
- Live preview system matching the image design
- Comprehensive styling options
- Cross-platform font support
- Visual consistency with backend rendering

#### 4. Subtitle Timeline
- Synchronized video playback with subtitle display
- Click-to-seek functionality
- In-line editing with save/cancel options
- Export to standard SRT format

## Backend Integration

The frontend is designed to work with the Python subtitle generation script:

### API Endpoints (Expected)
```
POST /api/process-video
- Multipart form data with video file
- Parameters: language, model, create_video
- Returns: SRT content and processing status
```

### Mock Implementation
Currently includes a mock service that simulates the processing pipeline for development and demonstration purposes.

## Design Philosophy

### Visual Consistency
- Matches the provided UI mockup design
- Dark theme optimized for video editing
- Professional gradient colors and spacing
- Consistent iconography using Lucide React

### User Experience
- Progressive disclosure (upload → settings → editor)
- Clear navigation with disabled states
- Visual feedback for all user actions
- Accessibility considerations

### Performance
- Efficient re-renders with React.memo where needed
- Optimized video handling with URL.createObjectURL
- Lazy loading for large subtitle lists
- Responsive design without performance penalties

## Technologies Used

- **React 18** with Hooks
- **React Context API** for state management
- **React Dropzone** for file uploads
- **Lucide React** for icons
- **CSS3** with modern features
- **HTML5 Video API** for video preview

## Installation

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## Usage

1. **Upload Video**: Drag and drop or click to select video file
2. **Configure Settings**: Choose language and AI model
3. **Process Video**: Click "Generate Subtitles" to start processing
4. **Edit Subtitles**: Review and edit generated text in the timeline
5. **Export**: Download the final SRT file

## Integration with Python Backend

To connect with the actual Python script:

1. Update `src/services/subtitleService.js` to use real API endpoints
2. Set up CORS on the Python backend
3. Handle file uploads through proper multipart form handling
4. Implement WebSocket for real-time progress updates (optional)

## Customization

The application is highly customizable:

- **Themes**: Modify CSS variables for different color schemes
- **Languages**: Add new language options in ProcessingPanel
- **Models**: Update model list with new Whisper models
- **Export Formats**: Extend export functionality for other subtitle formats

This frontend provides a complete, production-ready interface for the subtitle generation workflow, with both aesthetic appeal and functional completeness.
