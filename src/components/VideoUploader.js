import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Video, AlertCircle, Check } from 'lucide-react';
import './VideoUploader.css';

const VideoUploader = ({ onVideoUpload, currentVideo }) => {
  const [uploadError, setUploadError] = useState(null);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors[0]?.code === 'file-too-large') {
        setUploadError('File is too large. Maximum size is 500MB.');
      } else if (rejection.errors[0]?.code === 'file-invalid-type') {
        setUploadError('Invalid file type. Please upload MP4, MOV, or AVI files.');
      } else {
        setUploadError('Failed to upload file. Please try again.');
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setUploadError(null);
      onVideoUpload(file);
    }
  }, [onVideoUpload]);

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject
  } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    },
    maxSize: 500 * 1024 * 1024, // 500MB
    multiple: false
  });

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="video-uploader">
      <div 
        {...getRootProps()} 
        className={`
          dropzone 
          ${isDragActive ? 'drag-active' : ''} 
          ${isDragAccept ? 'drag-accept' : ''} 
          ${isDragReject ? 'drag-reject' : ''}
          ${currentVideo ? 'has-video' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="dropzone-content">
          {currentVideo ? (
            <div className="video-info">
              <div className="video-icon">
                <Check size={32} />
              </div>
              <div className="video-details">
                <h3>Video Selected</h3>
                <p className="video-name">{currentVideo.name}</p>
                <p className="video-size">{formatFileSize(currentVideo.size)}</p>
                <p className="video-type">{currentVideo.type}</p>
              </div>
              <div className="change-video">
                <p>Drop a new video here or click to change</p>
              </div>
            </div>
          ) : (
            <div className="upload-prompt">
              <div className="upload-icon">
                <Upload size={48} />
              </div>
              <h2>Upload your video</h2>
              <p className="upload-description">
                Drag and drop your video file here, or click to browse
              </p>
              <div className="supported-formats">
                <Video size={16} />
                <span>Supports MP4, MOV, AVI</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {uploadError && (
        <div className="upload-error">
          <AlertCircle size={16} />
          <span>{uploadError}</span>
        </div>
      )}
    </div>
  );
};

export default VideoUploader;
