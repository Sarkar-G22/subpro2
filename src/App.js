import React, { useState, useCallback } from 'react';
import VideoUploader from './components/VideoUploader';
import SubtitleEditor from './components/SubtitleEditor';
import FontStylePanel from './components/FontStylePanel';
import ProcessingPanel from './components/ProcessingPanel';
import ProgressIndicator from './components/ProgressIndicator';
import { SubtitleProvider, useSubtitle } from './context/SubtitleContext';
import './App.css';

function AppContent() {
  const {
    videoFile,
    subtitles,
    isProcessing,
    progress,
    fontSettings,
    selectedLanguage,
    modelName,
    processing,
    processVideo,
    setVideoFile,
    updateFontSettings,
    setSelectedLanguage,
    setModelName
  } = useSubtitle();

  const [activeTab, setActiveTab] = useState('upload');

  const handleVideoUpload = useCallback((file) => {
    setVideoFile(file);
    setActiveTab('settings');
  }, [setVideoFile]);

  const handleProcessStart = useCallback(async () => {
    if (videoFile) {
      await processVideo(videoFile);
      setActiveTab('editor');
    }
  }, [videoFile, processVideo]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Subtitle Generator</h1>
        <p>Create professional subtitles with AI-powered transcription</p>
      </header>

      <main className="app-main">
        {/* Navigation Tabs */}
        <nav className="nav-tabs">
          <button 
            className={`nav-tab ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            Upload Video
          </button>
          <button 
            className={`nav-tab ${activeTab === 'settings' ? 'active' : ''} ${!videoFile ? 'disabled' : ''}`}
            onClick={() => setActiveTab('settings')}
            disabled={!videoFile}
          >
            Settings
          </button>
          <button 
            className={`nav-tab ${activeTab === 'editor' ? 'active' : ''} ${subtitles.length === 0 ? 'disabled' : ''}`}
            onClick={() => setActiveTab('editor')}
            disabled={subtitles.length === 0}
          >
            Edit Subtitles
          </button>
        </nav>

        {/* Content Area */}
        <div className="content-area">
          {activeTab === 'upload' && (
            <div className="upload-section">
              <VideoUploader 
                onVideoUpload={handleVideoUpload}
                currentVideo={videoFile}
              />
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="settings-section">
              <div className="settings-grid">
                <div className="settings-main">
                  <ProcessingPanel
                    videoFile={videoFile}
                    selectedLanguage={selectedLanguage}
                    modelName={modelName}
                    onLanguageChange={setSelectedLanguage}
                    onModelChange={setModelName}
                    onProcessStart={handleProcessStart}
                    isProcessing={isProcessing}
                  />
                  
                  {isProcessing && (
                    <ProgressIndicator 
                      progress={progress}
                      currentStep={processing.currentStep}
                      isProcessing={isProcessing}
                    />
                  )}
                </div>
                
                <div className="settings-sidebar">
                  <FontStylePanel
                    fontSettings={fontSettings}
                    onFontChange={updateFontSettings}
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'editor' && (
            <div className="editor-section">
              <SubtitleEditor 
                subtitles={subtitles}
                fontSettings={fontSettings}
                videoFile={videoFile}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <SubtitleProvider>
      <AppContent />
    </SubtitleProvider>
  );
}

export default App;
