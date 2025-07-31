import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Download, Edit3, Save, X, Clock } from 'lucide-react';
import { useSubtitle } from '../context/SubtitleContext';
import './SubtitleEditor.css';

const SubtitleEditor = ({ subtitles, fontSettings, videoFile }) => {
  const { updateSubtitleText, exportSRT } = useSubtitle();
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState('');
  const [selectedSubtitle, setSelectedSubtitle] = useState(null);
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  useEffect(() => {
    if (videoFile && videoRef.current) {
      const videoUrl = URL.createObjectURL(videoFile);
      videoRef.current.src = videoUrl;
      
      return () => {
        URL.revokeObjectURL(videoUrl);
      };
    }
  }, [videoFile]);

  const parseTimeToSeconds = (timeString) => {
    const [time, ms] = timeString.split(',');
    const [hours, minutes, seconds] = time.split(':').map(Number);
    return hours * 3600 + minutes * 60 + seconds + ms / 1000;
  };

  const formatTimeToString = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const time = videoRef.current.currentTime;
      setCurrentTime(time);
      
      // Find the current subtitle
      const current = subtitles.find(subtitle => {
        const start = parseTimeToSeconds(subtitle.startTime);
        const end = parseTimeToSeconds(subtitle.endTime);
        return time >= start && time <= end;
      });
      
      setSelectedSubtitle(current);
    }
  };

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const seekToSubtitle = (subtitle) => {
    if (videoRef.current) {
      const startTime = parseTimeToSeconds(subtitle.startTime);
      videoRef.current.currentTime = startTime;
      setSelectedSubtitle(subtitle);
    }
  };

  const startEdit = (subtitle) => {
    setEditingId(subtitle.id);
    setEditText(subtitle.text);
  };

  const saveEdit = () => {
    if (editingId && editText.trim()) {
      updateSubtitleText(editingId, editText.trim());
    }
    setEditingId(null);
    setEditText('');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditText('');
  };

  const handleDownload = () => {
    const srtContent = exportSRT();
    const blob = new Blob([srtContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `subtitles_${Date.now()}.srt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="subtitle-editor">
      <div className="editor-header">
        <h3>Subtitle Timeline</h3>
        <div className="editor-actions">
          <button className="download-button" onClick={handleDownload}>
            <Download size={16} />
            Export SRT
          </button>
        </div>
      </div>

      <div className="editor-content">
        {videoFile && (
          <div className="video-preview">
            <video 
              ref={videoRef}
              onTimeUpdate={handleTimeUpdate}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              className="preview-video"
            />
            
            <div className="video-controls">
              <button onClick={handlePlayPause} className="play-button">
                {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              </button>
              
              <div className="time-display">
                <Clock size={14} />
                <span>{formatTimeToString(currentTime)}</span>
              </div>
            </div>

            {selectedSubtitle && (
              <div 
                className="current-subtitle-overlay"
                style={{
                  fontFamily: fontSettings.family,
                  fontSize: `${fontSettings.size}px`,
                  color: fontSettings.color,
                  backgroundColor: fontSettings.backgroundColor,
                  fontWeight: fontSettings.bold ? 'bold' : 'normal',
                  fontStyle: fontSettings.italic ? 'italic' : 'normal',
                  textDecoration: fontSettings.underline ? 'underline' : 'none',
                  textShadow: fontSettings.shadow ? '2px 2px 4px rgba(0,0,0,0.8)' : 'none'
                }}
              >
                {selectedSubtitle.text}
              </div>
            )}
          </div>
        )}

        <div className="subtitle-list">
          <div className="list-header">
            <h4>All Subtitles ({subtitles.length})</h4>
            <p>Select a subtitle to edit timing and text</p>
          </div>

          <div className="subtitle-items">
            {subtitles.map((subtitle) => (
              <div 
                key={subtitle.id} 
                className={`subtitle-item ${selectedSubtitle?.id === subtitle.id ? 'active' : ''}`}
                onClick={() => seekToSubtitle(subtitle)}
              >
                <div className="subtitle-timing">
                  <span className="time-range">
                    {subtitle.startTime} → {subtitle.endTime}
                  </span>
                  <span className="subtitle-index">#{subtitle.id}</span>
                </div>

                <div className="subtitle-content">
                  {editingId === subtitle.id ? (
                    <div className="edit-mode">
                      <textarea
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        className="edit-textarea"
                        autoFocus
                        rows={2}
                      />
                      <div className="edit-actions">
                        <button onClick={saveEdit} className="save-button">
                          <Save size={14} />
                          Save
                        </button>
                        <button onClick={cancelEdit} className="cancel-button">
                          <X size={14} />
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="view-mode">
                      <p className="subtitle-text">{subtitle.text}</p>
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          startEdit(subtitle);
                        }}
                        className="edit-button"
                      >
                        <Edit3 size={14} />
                        Edit
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubtitleEditor;
