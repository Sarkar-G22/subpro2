import React from 'react';
import { Play, Settings, Globe, Cpu } from 'lucide-react';
import './ProcessingPanel.css';

const ProcessingPanel = ({ 
  videoFile, 
  selectedLanguage, 
  modelName, 
  onLanguageChange, 
  onModelChange, 
  onProcessStart, 
  isProcessing 
}) => {
  const languages = [
    { value: 'auto', label: 'Auto-detect' },
    { value: 'english', label: 'English' },
    { value: 'hindi', label: 'Hindi' },
    { value: 'hinglish', label: 'Hinglish' }
  ];

  const models = [
    { value: 'tiny', label: 'Tiny (Fastest)', description: 'Quick processing, basic accuracy' },
    { value: 'base', label: 'Base (Recommended)', description: 'Good balance of speed and accuracy' },
    { value: 'small', label: 'Small', description: 'Better accuracy, slower processing' },
    { value: 'medium', label: 'Medium', description: 'High accuracy, requires more time' },
    { value: 'large', label: 'Large', description: 'Best accuracy, slowest processing' }
  ];

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="processing-panel">
      <div className="panel-header">
        <Settings size={20} />
        <h3>Processing Settings</h3>
      </div>

      {videoFile && (
        <div className="video-summary">
          <h4>Video Information</h4>
          <div className="video-details">
            <p><strong>File:</strong> {videoFile.name}</p>
            <p><strong>Size:</strong> {formatFileSize(videoFile.size)}</p>
            <p><strong>Type:</strong> {videoFile.type}</p>
          </div>
        </div>
      )}

      <div className="settings-grid">
        <div className="setting-group">
          <label className="setting-label">
            <Globe size={16} />
            Language
          </label>
          <select 
            value={selectedLanguage} 
            onChange={(e) => onLanguageChange(e.target.value)}
            className="setting-select"
            disabled={isProcessing}
          >
            {languages.map(lang => (
              <option key={lang.value} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </select>
          <p className="setting-help">
            Choose the primary language in your video. Auto-detect works for most cases.
          </p>
        </div>

        <div className="setting-group">
          <label className="setting-label">
            <Cpu size={16} />
            AI Model
          </label>
          <select 
            value={modelName} 
            onChange={(e) => onModelChange(e.target.value)}
            className="setting-select"
            disabled={isProcessing}
          >
            {models.map(model => (
              <option key={model.value} value={model.value}>
                {model.label}
              </option>
            ))}
          </select>
          <p className="setting-help">
            {models.find(m => m.value === modelName)?.description}
          </p>
        </div>
      </div>

      <div className="action-section">
        <button 
          className="process-button"
          onClick={onProcessStart}
          disabled={!videoFile || isProcessing}
        >
          <Play size={20} />
          {isProcessing ? 'Processing...' : 'Generate Subtitles'}
        </button>
        
        {selectedLanguage !== 'auto' && ['hindi', 'hinglish'].includes(selectedLanguage) && 
         ['tiny', 'base'].includes(modelName) && (
          <div className="model-recommendation">
            <p>💡 For better {selectedLanguage} accuracy, consider using the 'Small' or larger model.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcessingPanel;
